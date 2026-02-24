# Woodshed AI — RAG Pipeline
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""RAG conversation pipeline: search → augment → LLM → tool-call loop."""

import json
from collections.abc import Generator

import ollama

import config
from app.knowledge.vectorstore import VectorStore
from app.llm.prompts import build_system_prompt
from app.theory.tools import MUSIC_TOOLS, TOOL_FUNCTIONS

MAX_TOOL_ROUNDS = 5


class MusicConversation:
    """Manages a multi-turn conversation with RAG and tool-use."""

    def __init__(self):
        self.messages: list[dict] = []
        self._vectorstore = VectorStore()

    def send(
        self,
        user_message: str,
        temperature: float | None = None,
        category_filter: str | None = None,
    ) -> str:
        """Send a message and return the assistant's response.

        Steps:
        1. Search knowledge base for relevant context
        2. Build augmented system prompt
        3. Call LLM with tool definitions
        4. Execute any tool calls in a loop (max MAX_TOOL_ROUNDS)
        5. Return final text response
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE

        # 1. RAG retrieval
        context_chunks = self._vectorstore.search(
            user_message, n_results=5, category_filter=category_filter
        )

        # 2. Build message list
        system_msg = build_system_prompt(context_chunks)
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.messages)
        messages.append({"role": "user", "content": user_message})

        # 3. Call LLM with tools
        response = ollama.chat(
            model=config.LLM_MODEL,
            messages=messages,
            tools=MUSIC_TOOLS,
            options={"temperature": temperature},
        )

        # 4. Tool-call loop
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break

            # Append the assistant's tool-call message
            messages.append({
                "role": "assistant",
                "content": response.message.content or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in response.message.tool_calls
                ],
            })

            # Execute each tool and add results
            for tc in response.message.tool_calls:
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

            # Send tool results back to LLM
            response = ollama.chat(
                model=config.LLM_MODEL,
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
    ) -> Generator[str, None, None]:
        """Send a message and stream the response token by token.

        Tool calls are resolved non-streaming first, then the final
        response is streamed back.
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE

        # 1. RAG retrieval
        context_chunks = self._vectorstore.search(
            user_message, n_results=5, category_filter=category_filter
        )

        # 2. Build message list
        system_msg = build_system_prompt(context_chunks)
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.messages)
        messages.append({"role": "user", "content": user_message})

        # 3. First call (non-streaming to check for tool calls)
        response = ollama.chat(
            model=config.LLM_MODEL,
            messages=messages,
            tools=MUSIC_TOOLS,
            options={"temperature": temperature},
        )

        # 4. Tool-call loop (non-streaming)
        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": response.message.content or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in response.message.tool_calls
                ],
            })

            for tc in response.message.tool_calls:
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

            # Check if the next round also has tool calls
            response = ollama.chat(
                model=config.LLM_MODEL,
                messages=messages,
                tools=MUSIC_TOOLS,
                options={"temperature": temperature},
            )

        # 5. If the last response had no tool calls, re-do it as streaming
        if not response.message.tool_calls:
            # Stream the final response
            full_text = ""
            for chunk in ollama.chat(
                model=config.LLM_MODEL,
                messages=messages,
                options={"temperature": temperature},
                stream=True,
            ):
                token = chunk.message.content or ""
                full_text += token
                yield token

            # Store in history
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": full_text})
        else:
            # Fallback: yield the non-streamed response
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
