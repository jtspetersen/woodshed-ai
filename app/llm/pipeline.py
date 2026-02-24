# Woodshed AI — RAG Pipeline
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""RAG conversation pipeline: search → route → augment → LLM → tool-call loop."""

import json
import re
from collections.abc import Generator
from dataclasses import dataclass
from typing import Literal

import ollama

import config
from app.knowledge.vectorstore import VectorStore
from app.llm.prompts import build_system_prompt
from app.theory.tools import MUSIC_TOOLS as THEORY_TOOLS, TOOL_FUNCTIONS as THEORY_FUNCS
from app.audio.tools import AUDIO_TOOLS, AUDIO_TOOL_FUNCTIONS
from app.output.tools import OUTPUT_TOOLS, OUTPUT_TOOL_FUNCTIONS

# Merge theory + audio + output tools
MUSIC_TOOLS = THEORY_TOOLS + AUDIO_TOOLS + OUTPUT_TOOLS
TOOL_FUNCTIONS = {**THEORY_FUNCS, **AUDIO_TOOL_FUNCTIONS, **OUTPUT_TOOL_FUNCTIONS}

MAX_TOOL_ROUNDS = 5


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

StreamEvent = StreamToken | StreamStatus | StreamToolCall | StreamThinking


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

# Shared VectorStore instance (avoids recreating ChromaDB client per message)
_vectorstore: VectorStore | None = None


def _get_vectorstore() -> VectorStore:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStore()
    return _vectorstore


# --- Model Router ---

ROUTER_PROMPT = """\
Classify the following user message as either SIMPLE or COMPLEX.

SIMPLE: Direct questions about specific chords, notes, keys, scales, voicings, \
or progressions that can be answered with a tool call and brief explanation. \
Examples: "What notes are in Dm7?", "What key is Am F C G?", "How do I play G7 on guitar?"

COMPLEX: Open-ended creative requests, songwriting advice, mood-based suggestions, \
multi-part questions, or anything requiring detailed explanation without a clear tool match. \
Examples: "Help me write a bridge for my song", "I want something dreamy and nostalgic", \
"Explain how jazz reharmonization works"

Reply with exactly one word: SIMPLE or COMPLEX"""


def route_model(user_message: str) -> str:
    """Use the fast model to classify query complexity and pick the right model."""
    try:
        response = ollama.chat(
            model=config.FAST_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            options={"temperature": 0, "num_predict": 10},
        )
        answer = response.message.content.strip().upper()
        # Extract just the classification word
        if "SIMPLE" in answer:
            return config.FAST_MODEL
        return config.LLM_MODEL
    except Exception:
        # If routing fails, fall back to the big model
        return config.LLM_MODEL


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
        model = route_model(user_message)

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
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=MUSIC_TOOLS,
            options={"temperature": temperature},
        )

        # 4. Tool-call loop
        self.generated_files = []
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            _execute_tool_calls(response.message.tool_calls, messages, self.generated_files)
            response = ollama.chat(
                model=model,
                messages=messages,
                tools=MUSIC_TOOLS,
                options={"temperature": temperature},
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

        Yields StreamStatus, StreamToolCall, StreamThinking, and StreamToken events.
        Tool calls are resolved non-streaming, then the final response
        is streamed. If no tool calls occur, streams directly (no double-call).
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE

        yield StreamStatus(step="Warming up...")
        model = route_model(user_message)
        model_short = model.split(":")[0]
        is_quick = model == config.FAST_MODEL
        yield StreamStatus(
            step="Warming up...",
            detail=f"Going with {model_short} — {'quick answer' if is_quick else 'deep dive'}",
        )

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

        # 3. First call — non-streaming to check for tool calls
        yield StreamStatus(step="Noodling on it...")
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=MUSIC_TOOLS,
            options={"temperature": temperature},
        )

        # 4. If no tool calls, yield the already-generated response (no double-call)
        self.generated_files = []
        if not response.message.tool_calls:
            final_text = response.message.content or ""
            thinking, clean_text = _strip_thinking(final_text)
            if thinking:
                yield StreamThinking(text=thinking)
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": clean_text})
            yield StreamToken(text=clean_text)
            return

        # 5. Tool-call loop (non-streaming) — yield tool call events
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            for tc in response.message.tool_calls:
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
                # Append to messages for next LLM call
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": name, "arguments": args}}],
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, default=str),
                })

            response = ollama.chat(
                model=model,
                messages=messages,
                tools=MUSIC_TOOLS,
                options={"temperature": temperature},
            )

        # 6. Stream the final post-tool response
        yield StreamStatus(step="Putting it all together...")
        if not response.message.tool_calls:
            yield from self._stream_response(model, messages, temperature)
        else:
            final_text = response.message.content or ""
            thinking, clean_text = _strip_thinking(final_text)
            if thinking:
                yield StreamThinking(text=thinking)
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": clean_text})
            yield StreamToken(text=clean_text)

    def _stream_response(
        self, model: str, messages: list[dict], temperature: float
    ) -> Generator[StreamEvent, None, None]:
        """Stream a response, separating <think> blocks from content tokens."""
        in_thinking = False
        detect_buffer = ""
        detected = False
        full_text = ""

        for chunk in ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature},
            stream=True,
        ):
            token = chunk.message.content or ""
            full_text += token

            # Detection phase: check if response starts with <think>
            if not detected:
                detect_buffer += token
                stripped = detect_buffer.lstrip()

                if len(stripped) < 7:
                    continue

                if stripped.startswith("<think>"):
                    in_thinking = True
                    detected = True
                    after = stripped[7:]
                    if "</think>" in after:
                        end = after.index("</think>")
                        if after[:end].strip():
                            yield StreamThinking(text=after[:end].strip())
                        in_thinking = False
                        rest = after[end + 8:].lstrip("\n")
                        if rest:
                            yield StreamToken(text=rest)
                    elif after.strip():
                        yield StreamThinking(text=after)
                else:
                    detected = True
                    yield StreamToken(text=detect_buffer)
                continue

            # Post-detection: route to thinking or content
            if in_thinking:
                if "</think>" in token:
                    parts = token.split("</think>", 1)
                    if parts[0].strip():
                        yield StreamThinking(text=parts[0])
                    in_thinking = False
                    rest = parts[1].lstrip("\n")
                    if rest:
                        yield StreamToken(text=rest)
                else:
                    yield StreamThinking(text=token)
            else:
                yield StreamToken(text=token)

        # Flush anything still in the detect buffer
        if not detected and detect_buffer:
            yield StreamToken(text=detect_buffer)

        # Store clean text in conversation history
        _, clean_text = _strip_thinking(full_text)
        user_msg = messages[-1]["content"] if messages else ""
        # Walk back to find the user message (last user role)
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg["content"]
                break
        self.messages.append({"role": "user", "content": user_msg})
        self.messages.append({"role": "assistant", "content": clean_text})

    def reset(self):
        """Clear conversation history."""
        self.messages = []

    def get_history(self) -> list[dict]:
        """Return conversation history."""
        return list(self.messages)
