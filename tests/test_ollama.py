# Woodshed AI — Ollama Client Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the Ollama client wrapper. Requires Ollama running locally."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.ollama_client import (
    chat,
    chat_stream,
    get_embedding,
    is_available,
    list_models,
)


def test_availability():
    """Test that Ollama is reachable."""
    assert is_available(), "Ollama is not running or has no models"
    models = list_models()
    print(f"  Available models: {models}")
    assert len(models) > 0


def test_basic_chat():
    """Test a simple chat message gets a response."""
    messages = [{"role": "user", "content": "What key is C-E-G? Reply in one sentence."}]
    response = chat(messages)
    text = response.message.content
    print(f"  Response: {text[:200]}")
    assert len(text) > 0, "Got an empty response"


def test_chat_stream():
    """Test streaming yields chunks."""
    messages = [{"role": "user", "content": "Name 3 major chords. Be brief."}]
    chunks = []
    for chunk in chat_stream(messages):
        if chunk.message.content:
            chunks.append(chunk.message.content)
    full = "".join(chunks)
    print(f"  Streamed: {full[:200]}")
    assert len(full) > 0, "Streaming produced no output"


def test_embedding():
    """Test embedding generation."""
    vec = get_embedding("C major scale")
    print(f"  Embedding dim: {len(vec)}")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert isinstance(vec[0], float)


def test_tool_use():
    """Test that the LLM can return a tool call when given tool definitions."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_chord",
                "description": "Analyze a chord symbol and return its notes and quality",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chord_symbol": {
                            "type": "string",
                            "description": "A chord symbol like Dm7, Cmaj7, G7",
                        }
                    },
                    "required": ["chord_symbol"],
                },
            },
        }
    ]
    messages = [
        {
            "role": "system",
            "content": "You are a music theory assistant. Use the analyze_chord tool to analyze chords.",
        },
        {"role": "user", "content": "Analyze the chord Dm7 for me."},
    ]
    response = chat(messages, tools=tools)
    # LLM should either call the tool or respond with text
    has_tool_calls = response.message.tool_calls is not None
    has_text = response.message.content and len(response.message.content) > 0
    print(f"  Tool calls: {has_tool_calls}, Text: {has_text}")
    if has_tool_calls:
        for tc in response.message.tool_calls:
            print(f"  Tool: {tc.function.name}({tc.function.arguments})")
    assert has_tool_calls or has_text, "Response had neither tool calls nor text"


if __name__ == "__main__":
    tests = [
        ("Availability", test_availability),
        ("Basic chat", test_basic_chat),
        ("Streaming", test_chat_stream),
        ("Embedding", test_embedding),
        ("Tool use", test_tool_use),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
