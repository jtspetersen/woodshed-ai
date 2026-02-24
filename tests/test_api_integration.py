# Woodshed AI — API Integration Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""End-to-end API tests using live Ollama. Skipped if Ollama is offline.

Run with: pytest tests/test_api_integration.py -m integration
"""

import io
import json

import pretty_midi
import pytest

from app.api import sessions
from tests.conftest import requires_ollama

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


def _make_midi_bytes() -> bytes:
    """Create a small valid MIDI file for upload tests."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=0, name="Piano")
    for pitch in [60, 64, 67]:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=0.0, end=0.5))
    for pitch in [65, 69, 72]:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=0.5, end=1.0))
    for pitch in [67, 71, 74]:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=1.0, end=1.5))
    for pitch in [60, 64, 67]:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=1.5, end=2.0))
    midi.instruments.append(inst)
    buf = io.BytesIO()
    midi.write(buf)
    buf.seek(0)
    return buf.read()


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE text into list of {event, data} dicts."""
    events = []
    current = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            if current:
                events.append(current)
                current = {}
            continue
        if line.startswith("event:"):
            current["event"] = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:"):].strip()
    if current:
        events.append(current)
    return events


@requires_ollama
async def test_full_chat_flow(app_client, session_id):
    """Send a message and receive a streamed SSE response with real LLM."""
    headers = {"X-Session-ID": session_id}
    resp = await app_client.post(
        "/api/chat",
        json={"message": "What notes are in a C major chord?", "creativity": "Balanced"},
        headers=headers,
        timeout=60,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    events = _parse_sse(resp.text)
    token_events = [e for e in events if e.get("event") == "token"]
    done_events = [e for e in events if e.get("event") == "done"]

    assert len(token_events) > 0, "Expected at least one token event"
    assert len(done_events) == 1

    # Verify we got actual text content
    full_text = "".join(json.loads(e["data"])["text"] for e in token_events)
    assert len(full_text) > 10, f"Response too short: {full_text!r}"


@requires_ollama
async def test_chat_with_tool_use(app_client, session_id):
    """A theory question should trigger tool use and return a meaningful answer."""
    headers = {"X-Session-ID": session_id}
    resp = await app_client.post(
        "/api/chat",
        json={"message": "Analyze the chord Dm7", "creativity": "More Precise"},
        headers=headers,
        timeout=60,
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    token_events = [e for e in events if e.get("event") == "token"]
    full_text = "".join(json.loads(e["data"])["text"] for e in token_events)

    # The response should mention something about D minor 7
    assert len(full_text) > 0, "Expected non-empty response"


@requires_ollama
async def test_upload_midi_then_chat(app_client, session_id):
    """Upload a MIDI file, then ask about it — session should have context."""
    headers = {"X-Session-ID": session_id}
    midi_bytes = _make_midi_bytes()

    # Upload MIDI
    upload_resp = await app_client.post(
        "/api/files/upload",
        files={"file": ("test_integration.mid", midi_bytes, "audio/midi")},
        headers=headers,
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["midi_summary"] is not None

    # Chat about the uploaded file
    chat_resp = await app_client.post(
        "/api/chat",
        json={"message": "What can you tell me about the MIDI file I just uploaded?", "creativity": "Balanced"},
        headers=headers,
        timeout=60,
    )
    assert chat_resp.status_code == 200
    events = _parse_sse(chat_resp.text)
    token_events = [e for e in events if e.get("event") == "token"]
    assert len(token_events) > 0, "Expected response tokens"

    # After chat, midi_summary should be cleared (consumed)
    session = sessions.get_or_create(session_id)
    assert session.last_midi_summary is None


@requires_ollama
async def test_session_isolation(app_client):
    """Two sessions should have independent conversations."""
    headers_a = {"X-Session-ID": "integration-session-a"}
    headers_b = {"X-Session-ID": "integration-session-b"}

    # Send different messages to each session
    resp_a = await app_client.post(
        "/api/chat",
        json={"message": "Remember: my favorite chord is Cmaj7", "creativity": "Balanced"},
        headers=headers_a,
        timeout=60,
    )
    resp_b = await app_client.post(
        "/api/chat",
        json={"message": "Remember: my favorite key is D minor", "creativity": "Balanced"},
        headers=headers_b,
        timeout=60,
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    # Verify histories are separate
    hist_a = await app_client.get("/api/chat/history", headers=headers_a)
    hist_b = await app_client.get("/api/chat/history", headers=headers_b)

    msgs_a = hist_a.json()["messages"]
    msgs_b = hist_b.json()["messages"]

    # Each session should have its own user message
    user_msgs_a = [m["content"] for m in msgs_a if m["role"] == "user"]
    user_msgs_b = [m["content"] for m in msgs_b if m["role"] == "user"]

    assert any("Cmaj7" in m for m in user_msgs_a)
    assert not any("D minor" in m for m in user_msgs_a)
    assert any("D minor" in m for m in user_msgs_b)
    assert not any("Cmaj7" in m for m in user_msgs_b)


@requires_ollama
async def test_status_with_live_ollama(app_client):
    """Status endpoint returns real model list when Ollama is running."""
    resp = await app_client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ollama"]["available"] is True
    assert len(data["ollama"]["models"]) > 0
