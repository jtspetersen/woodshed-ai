# Woodshed AI — RAG Pipeline
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""RAG conversation pipeline: search → route → augment → LLM → tool-call loop."""

import json
import re
from collections.abc import Generator

import ollama

import config
from app.knowledge.vectorstore import VectorStore
from app.llm.prompts import build_system_prompt
from app.theory.tools import MUSIC_TOOLS as THEORY_TOOLS, TOOL_FUNCTIONS as THEORY_FUNCS
from app.audio.tools import AUDIO_TOOLS, AUDIO_TOOL_FUNCTIONS

# Merge theory + audio tools
MUSIC_TOOLS = THEORY_TOOLS + AUDIO_TOOLS
TOOL_FUNCTIONS = {**THEORY_FUNCS, **AUDIO_TOOL_FUNCTIONS}

MAX_TOOL_ROUNDS = 5

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

def _execute_tool_calls(tool_calls, messages):
    """Execute tool calls and append results to messages."""
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

        messages.append({
            "role": "tool",
            "content": json.dumps(result, default=str),
        })


class MusicConversation:
    """Manages a multi-turn conversation with RAG and tool-use."""

    def __init__(self):
        self.messages: list[dict] = []
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
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            _execute_tool_calls(response.message.tool_calls, messages)
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
    ) -> Generator[str, None, None]:
        """Send a message and stream the response token by token.

        Tool calls are resolved non-streaming, then the final response
        is streamed. If no tool calls occur, streams directly (no double-call).
        """
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

        # 3. First call — non-streaming to check for tool calls
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=MUSIC_TOOLS,
            options={"temperature": temperature},
        )

        # 4. If no tool calls, yield the already-generated response (no double-call)
        if not response.message.tool_calls:
            final_text = response.message.content or ""
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": final_text})
            yield final_text
            return

        # 5. Tool-call loop (non-streaming)
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            _execute_tool_calls(response.message.tool_calls, messages)
            response = ollama.chat(
                model=model,
                messages=messages,
                tools=MUSIC_TOOLS,
                options={"temperature": temperature},
            )

        # 6. Stream the final post-tool response
        if not response.message.tool_calls:
            full_text = ""
            for chunk in ollama.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature},
                stream=True,
            ):
                token = chunk.message.content or ""
                full_text += token
                yield token

            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": full_text})
        else:
            final_text = response.message.content or ""
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": final_text})
            yield final_text

    def reset(self):
        """Clear conversation history."""
        self.messages = []

    def get_history(self) -> list[dict]:
        """Return conversation history."""
        return list(self.messages)
