# Woodshed AI — Audio Transcription
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Audio-to-MIDI transcription via the basic-pitch microservice.

basic-pitch does not support Python 3.13+ (as of Feb 2026), so transcription
runs in a separate Python 3.12 Flask service at TRANSCRIPTION_SERVICE_URL.
See services/basic-pitch/README.md for setup instructions.

When basic-pitch adds Python 3.13 support, this module can be simplified to
call basic-pitch directly (removing the HTTP layer).
"""

import logging
import os

import requests

import config

logger = logging.getLogger(__name__)

TRANSCRIBE_TIMEOUT = 120  # seconds — long files can take 30s+
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}


def is_transcription_available() -> bool:
    """Check if the basic-pitch transcription service is reachable."""
    try:
        resp = requests.get(
            f"{config.TRANSCRIPTION_SERVICE_URL}/health",
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def transcribe_audio(file_path: str) -> dict:
    """Transcribe an audio file to MIDI via the basic-pitch microservice.

    Args:
        file_path: Path to an audio file (wav, mp3, m4a, ogg, flac).

    Returns:
        Dict with 'midi_path' on success, or 'error' on failure.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        return {"error": f"Unsupported audio format: {ext}"}

    if not is_transcription_available():
        return {
            "error": (
                "The transcription service isn't running. "
                "Start it with: services\\basic-pitch\\start.bat"
            )
        }

    try:
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{config.TRANSCRIPTION_SERVICE_URL}/transcribe",
                files={"file": (filename, f)},
                timeout=TRANSCRIBE_TIMEOUT,
            )

        if resp.status_code != 200:
            # Try to extract JSON error, fall back to status code
            try:
                error_msg = resp.json().get("error", f"Status {resp.status_code}")
            except Exception:
                error_msg = f"Transcription service returned status {resp.status_code}"
            return {"error": error_msg}

        # Save the returned MIDI file
        os.makedirs(str(config.LOCAL_MIDI_DIR), exist_ok=True)
        base_name = os.path.splitext(filename)[0]
        midi_filename = f"{base_name}_transcribed.mid"
        midi_path = str(config.LOCAL_MIDI_DIR / midi_filename)

        with open(midi_path, "wb") as f:
            f.write(resp.content)

        logger.info("Transcribed %s -> %s", file_path, midi_path)
        return {
            "midi_path": midi_path,
            "original_file": filename,
        }

    except requests.Timeout:
        return {"error": "Transcription timed out — the audio file may be too long."}
    except requests.ConnectionError:
        return {
            "error": (
                f"Can't reach the transcription service at "
                f"{config.TRANSCRIPTION_SERVICE_URL}. Is it running?"
            )
        }
    except Exception as e:
        logger.exception("Transcription failed")
        return {"error": f"Transcription failed: {e}"}
