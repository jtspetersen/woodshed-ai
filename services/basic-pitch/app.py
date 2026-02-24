# Woodshed AI — Basic Pitch Transcription Service
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Lightweight Flask microservice wrapping basic-pitch for audio-to-MIDI transcription.

Runs in a separate Python 3.12 venv because basic-pitch does not support Python 3.13+.
Start with: python app.py
"""

import io
import logging
import os
import tempfile
import traceback

from flask import Flask, Response, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}


@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON for any unhandled exception."""
    logger.exception("Unhandled error")
    return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "basic-pitch"})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Transcribe an audio file to MIDI.

    Expects a multipart form upload with field name 'file'.
    Returns the transcribed MIDI file.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Send audio as 'file' field."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported format: {ext}. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    # Import here so /health responds even if basic-pitch is slow to load
    from basic_pitch.inference import predict as bp_predict

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, f"input{ext}")
            file.save(audio_path)
            logger.info("Transcribing %s (%s)", file.filename, ext)

            _model_output, midi_data, _note_events = bp_predict(audio_path)

            # Write MIDI to an in-memory buffer so we can return it after
            # the temp directory is cleaned up
            midi_buf = io.BytesIO()
            midi_data.write(midi_buf)
            midi_bytes = midi_buf.getvalue()

    except Exception as e:
        logger.exception("Transcription failed for %s", file.filename)
        return jsonify({"error": f"Transcription failed: {e}"}), 500

    logger.info("Transcription complete: %d bytes MIDI", len(midi_bytes))
    output_name = os.path.splitext(file.filename)[0] + ".mid"
    return Response(
        midi_bytes,
        mimetype="audio/midi",
        headers={
            "Content-Disposition": f'attachment; filename="{output_name}"',
        },
    )


if __name__ == "__main__":
    print("Basic Pitch transcription service starting on http://localhost:8765")
    print("Supported formats:", ", ".join(sorted(ALLOWED_EXTENSIONS)))
    app.run(host="0.0.0.0", port=8765)
