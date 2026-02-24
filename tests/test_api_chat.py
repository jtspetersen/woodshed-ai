# Woodshed AI — API Chat Endpoint Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the /api/chat SSE streaming endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import create_app
from app.api import sessions
from app.llm.pipeline import StreamToken, StreamStatus, StreamToolCall

app = create_app()

SESSION_ID = "test-session-abc123"
HEADERS = {"X-Session-ID": SESSION_ID}


@pytest.fixture(autouse=True)
def clean_sessions():
    """Clean session store between tests."""
    sessions.clear_all()
    yield
    sessions.clear_all()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _mock_send_stream(events, generated_files=None):
    """Create a mock conversation whose send_stream yields given StreamEvent objects.

    For convenience, plain strings are auto-wrapped as StreamToken.
    """
    mock_conv = MagicMock()
    mock_conv.generated_files = generated_files or []
    mock_conv.messages = []

    def fake_stream(*args, **kwargs):
        mock_conv.generated_files = generated_files or []
        for event in events:
            if isinstance(event, str):
                yield StreamToken(text=event)
            else:
                yield event

    mock_conv.send_stream = MagicMock(side_effect=fake_stream)
    mock_conv.get_history.return_value = []
    mock_conv.reset = MagicMock()
    return mock_conv


def _inject_mock_session(mock_conv, midi_summary=None):
    """Inject a mock conversation into the session store."""
    session = sessions.get_or_create(SESSION_ID)
    session.conversation = mock_conv
    session.last_midi_summary = midi_summary
    return session


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


@pytest.mark.anyio
async def test_chat_returns_sse_content_type(client):
    mock_conv = _mock_send_stream(["Hello"])
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "hi", "creativity": "Balanced"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.anyio
async def test_chat_stream_emits_tokens(client):
    mock_conv = _mock_send_stream(["Hello", " world", "!"])
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "test", "creativity": "Balanced"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    token_events = [e for e in events if e.get("event") == "token"]
    assert len(token_events) == 3
    # Verify token content
    import json
    texts = [json.loads(e["data"])["text"] for e in token_events]
    assert texts == ["Hello", " world", "!"]


@pytest.mark.anyio
async def test_chat_stream_emits_done_event(client):
    mock_conv = _mock_send_stream(["response"])
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "test", "creativity": "Balanced"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    done_events = [e for e in events if e.get("event") == "done"]
    assert len(done_events) == 1


@pytest.mark.anyio
async def test_chat_with_generated_files_emits_files_event(client):
    mock_conv = _mock_send_stream(
        ["Here's your MIDI"],
        generated_files=["data/local/midi/prog_001.mid"],
    )
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "generate a progression", "creativity": "Balanced"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    file_events = [e for e in events if e.get("event") == "files"]
    assert len(file_events) == 1
    import json
    files = json.loads(file_events[0]["data"])["files"]
    assert "data/local/midi/prog_001.mid" in files


@pytest.mark.anyio
async def test_chat_creativity_maps_to_temperature(client):
    mock_conv = _mock_send_stream(["ok"])
    _inject_mock_session(mock_conv)

    await client.post(
        "/api/chat",
        json={"message": "test", "creativity": "More Precise"},
        headers=HEADERS,
    )
    call_kwargs = mock_conv.send_stream.call_args
    assert call_kwargs.kwargs["temperature"] == 0.3

    # Reset and test Creative
    mock_conv2 = _mock_send_stream(["ok"])
    _inject_mock_session(mock_conv2)

    await client.post(
        "/api/chat",
        json={"message": "test", "creativity": "More Creative"},
        headers=HEADERS,
    )
    call_kwargs2 = mock_conv2.send_stream.call_args
    assert call_kwargs2.kwargs["temperature"] == 1.1


@pytest.mark.anyio
async def test_chat_reset_clears_history(client):
    mock_conv = _mock_send_stream(["hello"])
    session = _inject_mock_session(mock_conv)
    session.last_midi_summary = "some midi data"

    resp = await client.post("/api/chat/reset", headers=HEADERS)
    assert resp.status_code == 200
    mock_conv.reset.assert_called_once()

    # Verify midi_summary also cleared
    updated_session = sessions.get_or_create(SESSION_ID)
    assert updated_session.last_midi_summary is None


@pytest.mark.anyio
async def test_chat_history_returns_messages(client):
    mock_conv = _mock_send_stream([])
    mock_conv.get_history.return_value = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello!"},
    ]
    _inject_mock_session(mock_conv)

    resp = await client.get("/api/chat/history", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"


@pytest.mark.anyio
async def test_chat_error_on_ollama_failure(client):
    mock_conv = MagicMock()
    mock_conv.generated_files = []

    def failing_stream(*args, **kwargs):
        raise ConnectionError("Ollama not running")

    mock_conv.send_stream = MagicMock(side_effect=failing_stream)
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "test"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    error_events = [e for e in events if e.get("event") == "error"]
    assert len(error_events) == 1
    import json
    assert "Ollama not running" in json.loads(error_events[0]["data"])["message"]


@pytest.mark.anyio
async def test_chat_stream_emits_status_events(client):
    mock_conv = _mock_send_stream([
        StreamStatus(step="Searching knowledge base..."),
        StreamStatus(step="Thinking..."),
        StreamToken(text="The answer"),
    ])
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "test", "creativity": "Balanced"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    status_events = [e for e in events if e.get("event") == "status"]
    assert len(status_events) == 2
    import json
    steps = [json.loads(e["data"])["step"] for e in status_events]
    assert "Searching knowledge base..." in steps
    assert "Thinking..." in steps


@pytest.mark.anyio
async def test_chat_stream_emits_tool_call_events(client):
    mock_conv = _mock_send_stream([
        StreamStatus(step="Calling analyze_chord..."),
        StreamToolCall(
            name="analyze_chord",
            arguments={"chord_symbol": "Dm7"},
            result={"root": "D", "quality": "minor seventh"},
        ),
        StreamToken(text="Dm7 is a minor seventh chord."),
    ])
    _inject_mock_session(mock_conv)

    resp = await client.post(
        "/api/chat",
        json={"message": "analyze Dm7", "creativity": "Balanced"},
        headers=HEADERS,
    )
    events = _parse_sse(resp.text)
    tool_events = [e for e in events if e.get("event") == "tool_call"]
    assert len(tool_events) == 1
    import json
    data = json.loads(tool_events[0]["data"])
    assert data["name"] == "analyze_chord"
    assert data["arguments"]["chord_symbol"] == "Dm7"
    assert data["result"]["root"] == "D"


@pytest.mark.anyio
async def test_chat_without_session_header_returns_400(client):
    resp = await client.post(
        "/api/chat",
        json={"message": "test"},
    )
    assert resp.status_code == 400


def test_session_remove():
    """Test sessions.remove() removes a session."""
    sessions.clear_all()
    sessions.get_or_create("to-remove")
    sessions.remove("to-remove")
    # Creating again should give a fresh session
    session = sessions.get_or_create("to-remove")
    assert session.last_midi_summary is None
    sessions.clear_all()


def test_session_cleanup_stale():
    """Test sessions.cleanup_stale() removes old sessions."""
    import time
    sessions.clear_all()

    session = sessions.get_or_create("old-session")
    # Backdate the session
    session.last_access = time.time() - 7200  # 2 hours ago

    sessions.get_or_create("fresh-session")

    removed = sessions.cleanup_stale(max_age=3600)
    assert removed == 1

    # Fresh session should still exist
    fresh = sessions.get_or_create("fresh-session")
    assert fresh is not None

    sessions.clear_all()


def test_session_remove_nonexistent():
    """Test sessions.remove() with nonexistent ID doesn't raise."""
    sessions.clear_all()
    sessions.remove("does-not-exist")  # Should not raise
    sessions.clear_all()
