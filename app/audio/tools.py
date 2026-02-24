# Woodshed AI — Audio/MIDI Tool Definitions
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tool schemas for MIDI analysis and audio transcription."""

from app.audio import analyze, transcribe


def _transcribe_and_analyze(file_path: str) -> dict:
    """Transcribe an audio file to MIDI and return the analysis."""
    result = transcribe.transcribe_audio(file_path)
    if "error" in result:
        return result
    return analyze.analyze_midi(result["midi_path"])


# Maps tool name -> callable function
AUDIO_TOOL_FUNCTIONS = {
    "analyze_uploaded_midi": analyze.analyze_midi,
    "transcribe_audio_file": _transcribe_and_analyze,
}

# Tool schemas for Ollama's tool-use format
AUDIO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_uploaded_midi",
            "description": (
                "Analyze an uploaded MIDI file to extract key, tempo, time signature, "
                "instruments, chord progression, and note content. Use this when the "
                "user uploads a MIDI file and asks about it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the uploaded MIDI file",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transcribe_audio_file",
            "description": (
                "Transcribe an audio file (wav, mp3, m4a) to MIDI and analyze it. "
                "Returns key, tempo, chords, and other musical information extracted "
                "from the audio. Use this when the user uploads an audio file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the audio file to transcribe",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
]
