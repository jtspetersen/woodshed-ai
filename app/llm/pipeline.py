# Woodshed AI — RAG Pipeline
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""RAG conversation pipeline: search → augment → LLM → tool-call loop."""

import json
import os
import re
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Literal

import config
from app.knowledge.vectorstore import VectorStore
from app.llm import ollama_client
from app.llm.prompts import build_system_prompt
from app.theory.tools import MUSIC_TOOLS as THEORY_TOOLS, TOOL_FUNCTIONS as THEORY_FUNCS
from app.audio.tools import AUDIO_TOOLS, AUDIO_TOOL_FUNCTIONS
from app.output.tools import OUTPUT_TOOLS, OUTPUT_TOOL_FUNCTIONS

# Merge theory + audio + output tools
MUSIC_TOOLS = THEORY_TOOLS + AUDIO_TOOLS + OUTPUT_TOOLS
TOOL_FUNCTIONS = {**THEORY_FUNCS, **AUDIO_TOOL_FUNCTIONS, **OUTPUT_TOOL_FUNCTIONS}

MAX_TOOL_ROUNDS = 3


# --- Stream event types ---

@dataclass
class StreamToken:
    """A token of LLM output text."""
    type: Literal["token"] = "token"
    text: str = ""

@dataclass
class StreamStatus:
    """A status update about what the pipeline is doing."""
    type: Literal["status"] = "status"
    step: str = ""
    detail: str | None = None

@dataclass
class StreamToolCall:
    """A tool call being executed."""
    type: Literal["tool_call"] = "tool_call"
    name: str = ""
    arguments: dict | None = None
    result: dict | str | None = None

@dataclass
class StreamThinking:
    """LLM internal reasoning (parsed from Qwen3 <think> blocks)."""
    type: Literal["thinking"] = "thinking"
    text: str = ""

@dataclass
class StreamPart:
    """A typed content part for declarative rendering (abc, tab, midi, file)."""
    type: Literal["part"] = "part"
    part_type: str = ""
    data: dict = field(default_factory=dict)

StreamEvent = StreamToken | StreamStatus | StreamToolCall | StreamThinking | StreamPart


# --- Musician-friendly tool status messages ---

TOOL_STATUS_MESSAGES: dict[str, str] = {
    "analyze_chord": "Breaking down that chord...",
    "analyze_progression": "Analyzing the progression...",
    "suggest_next_chord": "Finding what comes next...",
    "get_scale_for_mood": "Matching scales to the vibe...",
    "detect_key": "Figuring out the key...",
    "get_chord_voicings": "Looking up voicings...",
    "get_related_chords": "Exploring related chords...",
    "generate_progression_midi": "Building your MIDI file...",
    "generate_scale_midi": "Writing out the scale...",
    "generate_guitar_tab": "Drawing up the tab...",
    "generate_notation": "Writing notation...",
    "export_for_daw": "Packaging for your DAW...",
    "analyze_midi": "Studying the MIDI file...",
    "transcribe_audio": "Transcribing the audio...",
}


# --- Thinking parser (Qwen3 <think> blocks) ---

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def _strip_thinking(text: str) -> tuple[str | None, str]:
    """Extract <think> block from LLM response. Returns (thinking, clean_text)."""
    match = _THINK_RE.search(text)
    if not match:
        return None, text
    thinking = match.group(1).strip()
    clean = (text[:match.start()] + text[match.end():]).strip()
    return thinking or None, clean


class ThinkingParser:
    """Incremental streaming parser for <think>...</think> blocks.

    Processes tokens one at a time and yields StreamThinking or StreamToken events.
    Handles the detection phase (does the response start with <think>?) and then
    routes subsequent tokens to thinking or content output.
    """

    def __init__(self):
        self.in_thinking = False
        self.detected = False
        self.detect_buffer = ""
        self.full_text = ""

    def feed(self, token: str) -> Generator[StreamEvent, None, None]:
        """Feed a token and yield any resulting events."""
        self.full_text += token

        # Detection phase: check if response starts with <think>
        if not self.detected:
            self.detect_buffer += token
            stripped = self.detect_buffer.lstrip()

            if len(stripped) < 7:
                return

            if stripped.startswith("<think>"):
                self.in_thinking = True
                self.detected = True
                after = stripped[7:]
                if "</think>" in after:
                    end = after.index("</think>")
                    if after[:end].strip():
                        yield StreamThinking(text=after[:end].strip())
                    self.in_thinking = False
                    rest = after[end + 8:].lstrip("\n")
                    if rest:
                        yield StreamToken(text=rest)
                elif after.strip():
                    yield StreamThinking(text=after)
            else:
                self.detected = True
                yield StreamToken(text=self.detect_buffer)
            return

        # Post-detection: route to thinking or content
        if self.in_thinking:
            if "</think>" in token:
                parts = token.split("</think>", 1)
                if parts[0].strip():
                    yield StreamThinking(text=parts[0])
                self.in_thinking = False
                rest = parts[1].lstrip("\n")
                if rest:
                    yield StreamToken(text=rest)
            else:
                yield StreamThinking(text=token)
        else:
            yield StreamToken(text=token)

    def flush(self) -> Generator[StreamEvent, None, None]:
        """Flush any remaining buffered content."""
        if not self.detected and self.detect_buffer:
            yield StreamToken(text=self.detect_buffer)

    def get_clean_text(self) -> str:
        """Return the full text with <think> blocks stripped."""
        _, clean = _strip_thinking(self.full_text)
        return clean


# Shared VectorStore instance (avoids recreating ChromaDB client per message)
_vectorstore: VectorStore | None = None


def _get_vectorstore() -> VectorStore:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStore()
    return _vectorstore


# --- Tool execution helper ---

def _execute_tool_calls(tool_calls, messages, generated_files=None):
    """Execute tool calls and append results to messages.

    Args:
        generated_files: Optional list to collect file paths from tool results.
    """
    messages.append({
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            }
            for tc in tool_calls
        ],
    })

    for tc in tool_calls:
        name = tc.function.name
        args = tc.function.arguments
        if name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[name](**args)
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"error": f"Unknown tool: {name}"}

        # Track generated files (MIDI, MusicXML, etc.)
        if generated_files is not None and isinstance(result, dict):
            for key in ("file_path", "midi_path"):
                path = result.get(key)
                if path and isinstance(path, str):
                    generated_files.append(path)

        messages.append({
            "role": "tool",
            "content": json.dumps(result, default=str),
        })


def _emit_tool_parts(name: str, result) -> Generator[StreamPart, None, None]:
    """Emit typed content parts from a tool result for declarative rendering."""
    if not isinstance(result, dict) or "error" in result:
        return
    if name == "generate_notation" and "abc" in result:
        yield StreamPart(part_type="abc", data={"abc": result["abc"]})
    elif name == "generate_guitar_tab" and "tab" in result:
        yield StreamPart(part_type="tab", data={"tab": result["tab"]})
    elif name in ("generate_progression_midi", "generate_scale_midi") and "file_path" in result:
        yield StreamPart(part_type="midi", data={"filename": os.path.basename(result["file_path"])})
    elif name == "export_for_daw":
        if result.get("midi_path"):
            yield StreamPart(part_type="file", data={"filename": os.path.basename(result["midi_path"])})
        if result.get("musicxml_path"):
            yield StreamPart(part_type="file", data={"filename": os.path.basename(result["musicxml_path"])})


def _condense_tool_result(name: str, result) -> str:
    """Create a condensed version of a tool result for conversation history.

    The UI already renders full ABC/tab/MIDI content via StreamPart events.
    For conversation continuity the LLM only needs a short summary of what
    was produced — keeping full notation/tab strings wastes context tokens.
    """
    if not isinstance(result, dict):
        return str(result)
    if "error" in result:
        return json.dumps(result)
    # Strip bulky content, keep structural info
    condensed = {}
    for key, val in result.items():
        if key == "abc":
            condensed["abc_generated"] = True
            # Keep the chord list from the title line if present
            if "chords" in result:
                condensed["chords"] = result["chords"]
        elif key == "tab":
            condensed["tab_generated"] = True
            if "chords" in result:
                condensed["chords"] = result["chords"]
        elif key == "file_path":
            condensed["file_generated"] = os.path.basename(val)
        elif key == "midi_path":
            condensed["midi_file"] = os.path.basename(val)
        elif key == "musicxml_path":
            condensed["musicxml_file"] = os.path.basename(val)
        else:
            condensed[key] = val
    return json.dumps(condensed, default=str)


def _find_user_message(messages: list[dict]) -> str:
    """Walk back through messages to find the last user message."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg["content"]
    return ""


class MusicConversation:
    """Manages a multi-turn conversation with RAG and tool-use."""

    def __init__(self):
        self.messages: list[dict] = []
        self.generated_files: list[str] = []
        self._vectorstore = _get_vectorstore()

    def send(
        self,
        user_message: str,
        temperature: float | None = None,
        category_filter: str | None = None,
        midi_summary: str | None = None,
    ) -> str:
        """Send a message and return the assistant's response."""
        temperature = temperature if temperature is not None else config.TEMPERATURE
        model = config.LLM_MODEL

        # 1. RAG retrieval
        context_chunks = self._vectorstore.search(
            user_message, n_results=config.RAG_RESULTS, category_filter=category_filter
        )

        # 2. Build message list
        system_msg = build_system_prompt(context_chunks, midi_summary=midi_summary)
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.messages)
        messages.append({"role": "user", "content": user_message})

        # 3. Call LLM with tools
        response = ollama_client.chat(
            messages=messages,
            tools=MUSIC_TOOLS,
            model=model,
            temperature=temperature,
        )

        # 4. Tool-call loop
        self.generated_files = []
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            _execute_tool_calls(response.message.tool_calls, messages, self.generated_files)
            response = ollama_client.chat(
                messages=messages,
                tools=MUSIC_TOOLS,
                model=model,
                temperature=temperature,
            )

        # 5. Store in conversation history and return
        final_text = response.message.content or ""
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": final_text})
        return final_text

    def send_stream(
        self,
        user_message: str,
        temperature: float | None = None,
        category_filter: str | None = None,
        midi_summary: str | None = None,
    ) -> Generator[StreamEvent, None, None]:
        """Send a message and stream the response as structured events.

        Streams tokens immediately via streaming + tools. If the model
        decides to call tools, they are executed and a post-tool streaming
        call follows. No non-streaming first call needed.
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE
        model = config.LLM_MODEL

        # 1. RAG retrieval
        yield StreamStatus(step="Checking my notes...")
        context_chunks = self._vectorstore.search(
            user_message, n_results=config.RAG_RESULTS, category_filter=category_filter
        )
        n_chunks = len(context_chunks)
        if n_chunks:
            categories = {c.get("category", "general") for c in context_chunks if isinstance(c, dict)}
            cat_str = ", ".join(sorted(categories)) if categories else "music theory"
            yield StreamStatus(
                step="Checking my notes...",
                detail=f"Found {n_chunks} relevant section{'s' if n_chunks != 1 else ''} on {cat_str}",
            )

        # 2. Build message list
        system_msg = build_system_prompt(context_chunks, midi_summary=midi_summary)
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.messages)
        messages.append({"role": "user", "content": user_message})

        # 3. Stream first call with tools — tokens arrive immediately
        yield StreamStatus(step="Noodling on it...")
        self.generated_files = []
        tool_calls = None
        parser = ThinkingParser()
        # Track messages to persist in conversation history
        history_additions: list[dict] = []

        for chunk in ollama_client.chat_stream(
            messages=messages,
            tools=MUSIC_TOOLS,
            model=model,
            temperature=temperature,
        ):
            token = chunk.message.content or ""
            if token:
                yield from parser.feed(token)
            # Ollama sends tool_calls in the final chunk
            if hasattr(chunk.message, "tool_calls") and chunk.message.tool_calls:
                tool_calls = chunk.message.tool_calls

        yield from parser.flush()

        # 4. If no tool calls, we're done — text was already streamed
        if not tool_calls:
            clean_text = parser.get_clean_text()
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": clean_text})
            return

        # Store initial assistant text (if any was streamed before tool calls)
        initial_text = parser.get_clean_text()
        if initial_text:
            history_additions.append({"role": "assistant", "content": initial_text})

        # 5. Tool-call loop — execute tools, yield events
        for round_num in range(MAX_TOOL_ROUNDS):
            if not tool_calls:
                break

            for tc in tool_calls:
                name = tc.function.name
                args = tc.function.arguments
                step_msg = TOOL_STATUS_MESSAGES.get(name, f"Running {name}...")
                yield StreamStatus(step=step_msg)
                # Execute tool
                if name in TOOL_FUNCTIONS:
                    try:
                        result = TOOL_FUNCTIONS[name](**args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Unknown tool: {name}"}
                # Track generated files
                if isinstance(result, dict):
                    for key in ("file_path", "midi_path"):
                        path = result.get(key)
                        if path and isinstance(path, str):
                            self.generated_files.append(path)
                yield StreamToolCall(name=name, arguments=args, result=result)
                # Emit typed content parts from tool results
                yield from _emit_tool_parts(name, result)
                # Append full result to messages for the current LLM call
                tool_call_msg = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": name, "arguments": args}}],
                }
                tool_result_msg = {
                    "role": "tool",
                    "content": json.dumps(result, default=str),
                }
                messages.append(tool_call_msg)
                messages.append(tool_result_msg)
                # Store condensed version in persistent history (saves tokens)
                history_additions.append(tool_call_msg)
                history_additions.append({
                    "role": "tool",
                    "content": _condense_tool_result(name, result),
                })

            # Stream post-tool response (may trigger more tool calls)
            tool_calls = None
            parser = ThinkingParser()
            yield StreamStatus(step="Putting it all together...")

            for chunk in ollama_client.chat_stream(
                messages=messages,
                tools=MUSIC_TOOLS if round_num < MAX_TOOL_ROUNDS - 1 else None,
                model=model,
                temperature=temperature,
            ):
                token = chunk.message.content or ""
                if token:
                    yield from parser.feed(token)
                if hasattr(chunk.message, "tool_calls") and chunk.message.tool_calls:
                    tool_calls = chunk.message.tool_calls

            yield from parser.flush()

        # 6. Store full exchange in conversation history (user + tools + final text)
        clean_text = parser.get_clean_text()
        self.messages.append({"role": "user", "content": user_message})
        self.messages.extend(history_additions)
        self.messages.append({"role": "assistant", "content": clean_text})

    def reset(self):
        """Clear conversation history."""
        self.messages = []

    def get_history(self) -> list[dict]:
        """Return conversation history."""
        return list(self.messages)
