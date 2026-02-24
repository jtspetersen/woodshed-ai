# Woodshed AI — Ollama Client Wrapper
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Wrapper around the Ollama API for chat, streaming, tool-use, and embeddings."""

from collections.abc import Generator

import ollama

import config


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Send a chat message and return the full response.

    Returns the raw Ollama response dict with .message.content and
    optionally .message.tool_calls.
    """
    model = model or config.LLM_MODEL
    opts = {}
    if temperature is not None:
        opts["temperature"] = temperature

    try:
        kwargs = dict(model=model, messages=messages)
        if tools:
            kwargs["tools"] = tools
        if opts:
            kwargs["options"] = opts
        return ollama.chat(**kwargs)
    except ollama.ResponseError as e:
        raise OllamaError(f"Ollama responded with an error: {e}") from e
    except Exception as e:
        raise OllamaError(
            "Can't reach Ollama — is it running? Fire it up and I'll be ready to jam."
        ) from e


def chat_stream(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> Generator:
    """Stream a chat response, yielding chunks as they arrive.

    Each yielded item is a partial response dict from Ollama.
    """
    model = model or config.LLM_MODEL
    opts = {}
    if temperature is not None:
        opts["temperature"] = temperature

    try:
        kwargs = dict(model=model, messages=messages, stream=True)
        if tools:
            kwargs["tools"] = tools
        if opts:
            kwargs["options"] = opts
        yield from ollama.chat(**kwargs)
    except ollama.ResponseError as e:
        raise OllamaError(f"Ollama responded with an error: {e}") from e
    except Exception as e:
        raise OllamaError(
            "Can't reach Ollama — is it running? Fire it up and I'll be ready to jam."
        ) from e


def get_embedding(text: str, model: str | None = None) -> list[float]:
    """Generate an embedding vector for the given text."""
    model = model or config.EMBEDDING_MODEL
    try:
        response = ollama.embed(model=model, input=text)
        return response["embeddings"][0]
    except Exception as e:
        raise OllamaError(f"Embedding generation failed: {e}") from e


def list_models() -> list[str]:
    """Return names of locally available Ollama models."""
    try:
        response = ollama.list()
        return [m.model for m in response.models]
    except Exception:
        return []


def is_available() -> bool:
    """Check if Ollama is reachable and has the configured model."""
    try:
        models = list_models()
        return len(models) > 0
    except Exception:
        return False


class OllamaError(Exception):
    """Raised when Ollama communication fails."""
