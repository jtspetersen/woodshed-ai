# Woodshed AI — File Upload/Download Endpoints
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""File upload (MIDI/audio), download, and MIDI data URI endpoints."""

import base64
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

import config
from app.api.deps import get_session
from app.api.schemas import FileUploadResponse
from app.api.sessions import SessionData
from app.audio.analyze import analyze_midi, get_midi_summary
from app.audio.transcribe import transcribe_audio, SUPPORTED_AUDIO_EXTENSIONS

router = APIRouter()

SUPPORTED_MIDI_EXTENSIONS = {".mid", ".midi"}
SUPPORTED_UPLOAD_EXTENSIONS = SUPPORTED_MIDI_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS

# Directories that file downloads are allowed from
_ALLOWED_DIRS = [
    config.LOCAL_MIDI_DIR,
    config.LOCAL_DATA_DIR / "exports",
]


def _validate_download_path(filename: str) -> str:
    """Resolve filename to an absolute path within allowed directories.

    Raises HTTPException on path traversal or missing file.
    """
    # Reject any path separators or traversal components
    if os.sep in filename or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    for allowed_dir in _ALLOWED_DIRS:
        candidate = allowed_dir / filename
        resolved = candidate.resolve()
        # Ensure resolved path is still under the allowed directory
        if resolved.parent == allowed_dir.resolve() and resolved.is_file():
            return str(resolved)

    raise HTTPException(status_code=404, detail="File not found")


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile,
    session: SessionData = Depends(get_session),
):
    """Upload a MIDI or audio file for analysis.

    MIDI files are copied to the local MIDI directory and analyzed directly.
    Audio files are transcribed to MIDI via basic-pitch, then analyzed.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))}",
        )

    # Save uploaded file to local MIDI directory
    os.makedirs(str(config.LOCAL_MIDI_DIR), exist_ok=True)
    dest_path = str(config.LOCAL_MIDI_DIR / file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # MIDI: analyze directly
    if ext in SUPPORTED_MIDI_EXTENSIONS:
        analysis = analyze_midi(dest_path)
        midi_summary = get_midi_summary(analysis)
        session.last_midi_summary = midi_summary
        return FileUploadResponse(
            analysis=analysis.get("summary", str(analysis)),
            midi_summary=midi_summary,
        )

    # Audio: transcribe to MIDI, then analyze
    result = transcribe_audio(dest_path)
    if "error" in result:
        return FileUploadResponse(error=result["error"])

    midi_path = result["midi_path"]
    analysis = analyze_midi(midi_path)
    midi_summary = get_midi_summary(analysis)
    session.last_midi_summary = midi_summary
    return FileUploadResponse(
        analysis=analysis.get("summary", str(analysis)),
        midi_summary=midi_summary,
    )


@router.get("/files/download/{filename}")
async def download_file(filename: str):
    """Download a generated file (MIDI, MusicXML, etc.)."""
    path = _validate_download_path(filename)
    return FileResponse(path, filename=filename)


@router.get("/files/midi/{filename}")
async def midi_data_uri(filename: str):
    """Return a base64 data URI for in-browser MIDI playback."""
    path = _validate_download_path(filename)

    if not path.endswith((".mid", ".midi")):
        raise HTTPException(status_code=400, detail="Not a MIDI file")

    with open(path, "rb") as f:
        midi_bytes = f.read()

    b64 = base64.b64encode(midi_bytes).decode("ascii")
    data_uri = f"data:audio/midi;base64,{b64}"
    return {"data_uri": data_uri, "filename": filename}
