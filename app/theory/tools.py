# Woodshed AI — Tool Definitions
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tool schemas for Ollama tool-use and dispatch mapping to engine functions."""

from app.theory import engine

# Maps tool name → callable function
TOOL_FUNCTIONS = {
    "analyze_chord": engine.analyze_chord,
    "analyze_progression": engine.analyze_progression,
    "suggest_next_chord": engine.suggest_next_chord,
    "get_scale_for_mood": engine.get_scale_for_mood,
    "detect_key": engine.detect_key,
    "get_chord_voicings": engine.get_chord_voicings,
    "get_related_chords": engine.get_related_chords,
}

# Tool schemas for Ollama's tool-use format
MUSIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_chord",
            "description": "Analyze a chord symbol and return its root, quality, notes, and intervals. Use this when the user asks about a specific chord.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chord_symbol": {
                        "type": "string",
                        "description": "A chord symbol like 'Dm7', 'Cmaj7', 'G7', 'F#m'",
                    }
                },
                "required": ["chord_symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_progression",
            "description": "Analyze a chord progression to detect the key and provide Roman numeral analysis. Use this when the user gives you a series of chords to analyze.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of chord symbols like ['Am', 'F', 'C', 'G']",
                    },
                    "key_str": {
                        "type": "string",
                        "description": "Optional key like 'C major' or 'A minor'. Omit to auto-detect.",
                    },
                },
                "required": ["chords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_next_chord",
            "description": "Suggest chords that could follow a given chord progression, based on common resolution patterns. Use when the user asks 'what comes next' or wants chord suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of chord symbols representing the current progression",
                    },
                    "style": {
                        "type": "string",
                        "enum": ["general", "jazz", "blues", "pop"],
                        "description": "Musical style to influence suggestions. Defaults to 'general'.",
                    },
                },
                "required": ["chords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scale_for_mood",
            "description": "Suggest scales that match a given mood or emotional descriptor. Use when the user describes a feeling or atmosphere they want to create.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "An emotional descriptor like 'melancholy', 'bright', 'jazzy', 'dark', 'dreamy', 'aggressive'",
                    },
                    "root": {
                        "type": "string",
                        "description": "Optional root note like 'D', 'E', 'Bb'. Defaults to 'C'.",
                    },
                },
                "required": ["mood"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_key",
            "description": "Detect the most likely musical key from a list of notes. Use when the user provides notes and wants to know what key they're in.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notes_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of note names like ['C', 'E', 'G', 'A', 'D']",
                    }
                },
                "required": ["notes_list"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_chord_voicings",
            "description": "Get common guitar voicings (fret positions) for a chord. Use when the user asks how to play a chord on guitar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chord_symbol": {
                        "type": "string",
                        "description": "A chord symbol like 'Am', 'G7', 'Dm7'",
                    },
                    "instrument": {
                        "type": "string",
                        "description": "Instrument for voicings. Currently only 'guitar' is supported.",
                    },
                },
                "required": ["chord_symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_chords",
            "description": "Find chord substitutions, extensions, and borrowed chords related to a given chord. Use when the user wants alternatives or variations of a chord.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chord_symbol": {
                        "type": "string",
                        "description": "A chord symbol like 'Dm7', 'G7', 'Cmaj7'",
                    }
                },
                "required": ["chord_symbol"],
            },
        },
    },
]
