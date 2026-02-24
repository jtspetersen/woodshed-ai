# Woodshed AI — API File Endpoint Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the /api/files upload, download, and MIDI data URI endpoints."""

import io
import os
from unittest.mock import patch

import pretty_midi
import pytest
from httpx import ASGITransport, AsyncClient

import config
from app.api.main import create_app
from app.api import sessions

app = create_app()

SESSION_ID = "test-session-files"
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


def _make_midi_bytes() -> bytes:
    """Create a small valid MIDI file with enough notes for analysis."""
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=0, name="Piano")
    # C major chord on beat 1, then F major on beat 2 — enough for tempo estimation
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


@pytest.fixture
def midi_bytes():
    return _make_midi_bytes()


@pytest.fixture
def midi_on_disk(midi_bytes, tmp_path):
    """Write a MIDI file to the real LOCAL_MIDI_DIR for download tests."""
    os.makedirs(str(config.LOCAL_MIDI_DIR), exist_ok=True)
    path = config.LOCAL_MIDI_DIR / "test_download.mid"
    path.write_bytes(midi_bytes)
    yield path
    if path.exists():
        path.unlink()


@pytest.mark.anyio
async def test_upload_midi_returns_analysis(client, midi_bytes):
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("test.mid", midi_bytes, "audio/midi")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is None
    assert data["analysis"] is not None
    assert data["midi_summary"] is not None
    assert "BPM" in data["midi_summary"]


@pytest.mark.anyio
async def test_upload_audio_returns_analysis(client):
    """Audio upload transcribes via basic-pitch then analyzes the resulting MIDI."""
    fake_midi_bytes = _make_midi_bytes()

    # Mock transcribe_audio to write a real MIDI file and return its path
    def mock_transcribe(file_path):
        os.makedirs(str(config.LOCAL_MIDI_DIR), exist_ok=True)
        midi_path = str(config.LOCAL_MIDI_DIR / "test_transcribed.mid")
        with open(midi_path, "wb") as f:
            f.write(fake_midi_bytes)
        return {"midi_path": midi_path, "original_file": "test.wav"}

    with patch("app.api.routes.files.transcribe_audio", side_effect=mock_transcribe):
        resp = await client.post(
            "/api/files/upload",
            files={"file": ("test.wav", b"fake-audio-data", "audio/wav")},
            headers=HEADERS,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is None
    assert data["analysis"] is not None
    assert data["midi_summary"] is not None

    # Clean up
    transcribed = config.LOCAL_MIDI_DIR / "test_transcribed.mid"
    if transcribed.exists():
        transcribed.unlink()


@pytest.mark.anyio
async def test_upload_unsupported_format_returns_400(client):
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("test.pdf", b"fake-pdf", "application/pdf")},
        headers=HEADERS,
    )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]


@pytest.mark.anyio
async def test_download_existing_file(client, midi_on_disk):
    resp = await client.get(f"/api/files/download/{midi_on_disk.name}")
    assert resp.status_code == 200
    assert len(resp.content) > 0
    # MIDI files start with the "MThd" header
    assert resp.content[:4] == b"MThd"


@pytest.mark.anyio
async def test_download_nonexistent_returns_404(client):
    resp = await client.get("/api/files/download/nonexistent_file.mid")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_download_path_traversal_rejected(client):
    # ".." in the filename itself is rejected
    resp = await client.get("/api/files/download/..config.py")
    assert resp.status_code == 400

    # Direct traversal attempt
    resp2 = await client.get("/api/files/download/..%5C..%5Cconfig.py")
    assert resp2.status_code in (400, 404)  # 400 if decoded, 404 if route doesn't match


@pytest.mark.anyio
async def test_upload_stores_midi_summary_in_session(client, midi_bytes):
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("session_test.mid", midi_bytes, "audio/midi")},
        headers=HEADERS,
    )
    assert resp.status_code == 200

    # Verify the session now has a midi_summary
    session = sessions.get_or_create(SESSION_ID)
    assert session.last_midi_summary is not None
    assert "BPM" in session.last_midi_summary


@pytest.mark.anyio
async def test_midi_data_uri_returns_base64(client, midi_on_disk):
    resp = await client.get(f"/api/files/midi/{midi_on_disk.name}")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_uri" in data
    assert data["data_uri"].startswith("data:audio/midi;base64,")
    assert data["filename"] == midi_on_disk.name
