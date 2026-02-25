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
            "description": "Analyze a MIDI file: key, tempo, chords, instruments.",
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
            "description": "Transcribe audio to MIDI and analyze it.",
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
