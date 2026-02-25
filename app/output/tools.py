# Woodshed AI — Output Tool Definitions
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tool schemas and dispatch for MIDI generation, notation, tab, and export."""

from app.output import midi_gen, guitar_tab, notation, export

# Tool schemas for Ollama's tool-use format
OUTPUT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_progression_midi",
            "description": "Generate a playable MIDI file from a chord progression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Chord symbols like ['Dm7', 'G7', 'Cmaj7']",
                    },
                    "key_str": {
                        "type": "string",
                        "description": "Key signature like 'C major'. Optional.",
                    },
                    "tempo_bpm": {
                        "type": "integer",
                        "description": "Tempo in BPM. Default 120.",
                    },
                    "beats_per_chord": {
                        "type": "integer",
                        "description": "How many beats each chord lasts. Default 4.",
                    },
                    "instrument_name": {
                        "type": "string",
                        "enum": ["piano", "guitar", "bass"],
                        "description": "Instrument sound. Default 'piano'.",
                    },
                },
                "required": ["chords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_scale_midi",
            "description": "Generate a MIDI file playing a scale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scale_name": {
                        "type": "string",
                        "description": "Scale type: 'major', 'minor', 'dorian', 'mixolydian', etc.",
                    },
                    "root": {
                        "type": "string",
                        "description": "Root note like 'C', 'D', 'Bb'. Default 'C'.",
                    },
                    "tempo_bpm": {
                        "type": "integer",
                        "description": "Tempo in BPM. Default 100.",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["ascending", "descending", "both"],
                        "description": "Direction to play the scale. Default 'ascending'.",
                    },
                },
                "required": ["scale_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_guitar_tab",
            "description": "Generate ASCII guitar chord diagrams for a progression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Chord symbols like ['Am', 'F', 'C', 'G']",
                    },
                },
                "required": ["chords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_notation",
            "description": "Generate sheet music (ABC notation) for a chord progression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Chord symbols like ['Dm7', 'G7', 'Cmaj7']",
                    },
                    "key_str": {
                        "type": "string",
                        "description": "Key signature like 'C major'. Optional.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for the notation.",
                    },
                },
                "required": ["chords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_for_daw",
            "description": "Export a progression as MIDI + MusicXML for a DAW.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Chord symbols to export",
                    },
                    "key_str": {
                        "type": "string",
                        "description": "Optional key signature like 'C major'.",
                    },
                    "daw_name": {
                        "type": "string",
                        "enum": ["garageband", "logic", "ableton", "reaper", "fl_studio"],
                        "description": "Target DAW for import instructions. Optional.",
                    },
                    "tempo_bpm": {
                        "type": "integer",
                        "description": "Tempo in BPM. Default 120.",
                    },
                },
                "required": ["chords"],
            },
        },
    },
]


def _generate_notation_wrapper(chords: list[str], key_str: str | None = None, title: str | None = None) -> dict:
    """Wrapper that returns ABC notation in a dict for the LLM tool pipeline."""
    abc = notation.chords_to_abc(chords, key_str=key_str, title=title)
    if not abc:
        return {"error": "Could not generate notation. Check chord symbols."}
    return {"abc": abc, "chords": chords}


# Maps tool name -> callable function
OUTPUT_TOOL_FUNCTIONS = {
    "generate_progression_midi": midi_gen.generate_progression_midi,
    "generate_scale_midi": midi_gen.generate_scale_midi,
    "generate_guitar_tab": guitar_tab.generate_progression_tab,
    "generate_notation": _generate_notation_wrapper,
    "export_for_daw": export.export_for_daw,
}
