# Woodshed AI — MIDI Generation
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate MIDI files from chord progressions and scales using music21."""

import os
from datetime import datetime

from music21 import harmony, instrument, key, meter, note, scale, stream, tempo

import config
from app.theory.engine import _parse_key_string

# Instrument name → music21 class
INSTRUMENT_MAP = {
    "piano": instrument.Piano,
    "guitar": instrument.AcousticGuitar,
    "bass": instrument.ElectricBass,
}

# Scale type → music21 class
SCALE_MAP = {
    "major": scale.MajorScale,
    "minor": scale.MinorScale,
    "dorian": scale.DorianScale,
    "phrygian": scale.PhrygianScale,
    "lydian": scale.LydianScale,
    "mixolydian": scale.MixolydianScale,
    "locrian": scale.LocrianScale,
    "whole-tone": scale.WholeToneScale,
}


def _get_output_path(prefix: str, extension: str = ".mid") -> str:
    """Generate a unique output file path in data/local/midi/."""
    os.makedirs(config.LOCAL_MIDI_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}{extension}"
    return str(config.LOCAL_MIDI_DIR / filename)


def _build_stream_from_chords(
    chords: list[str],
    key_str: str | None = None,
    tempo_bpm: int = 120,
    time_sig: str = "4/4",
    beats_per_chord: int = 4,
    instrument_name: str = "piano",
) -> stream.Score:
    """Build a music21 Score from chord symbols.

    Shared by MIDI generation, notation rendering, and MusicXML export.
    """
    inst_cls = INSTRUMENT_MAP.get(instrument_name.lower(), instrument.Piano)

    s = stream.Score()
    p = stream.Part()
    p.insert(0, inst_cls())

    # Key signature
    if key_str:
        k = _parse_key_string(key_str)
        p.insert(0, k)

    # Time signature
    p.insert(0, meter.TimeSignature(time_sig))

    # Tempo
    p.insert(0, tempo.MetronomeMark(number=tempo_bpm))

    # Add chords
    for chord_symbol in chords:
        cs = harmony.ChordSymbol(chord_symbol)
        cs.quarterLength = beats_per_chord
        p.append(cs)

    s.append(p)
    return s


def generate_progression_midi(
    chords: list[str],
    key_str: str | None = None,
    tempo_bpm: int = 120,
    time_sig: str = "4/4",
    beats_per_chord: int = 4,
    instrument_name: str = "piano",
) -> dict:
    """Generate a MIDI file from a chord progression.

    Args:
        chords: List of chord symbols like ["Dm7", "G7", "Cmaj7"]
        key_str: Optional key signature, e.g. "C major"
        tempo_bpm: Tempo in BPM (default 120)
        time_sig: Time signature string (default "4/4")
        beats_per_chord: Duration of each chord in beats (default 4)
        instrument_name: "piano", "guitar", or "bass"

    Returns:
        Dict with file_path, duration_seconds, chord_count, or error.
    """
    if not chords:
        return {"error": "No chords provided."}

    # Validate chord symbols before building
    for c in chords:
        try:
            harmony.ChordSymbol(c)
        except Exception:
            return {"error": f"Couldn't parse chord symbol '{c}'. Try standard notation like Dm7, Cmaj7, G7."}

    try:
        s = _build_stream_from_chords(
            chords, key_str, tempo_bpm, time_sig, beats_per_chord, instrument_name
        )
        midi_path = _get_output_path("progression")
        s.write("midi", fp=midi_path)

        # Calculate duration
        beats_total = len(chords) * beats_per_chord
        duration_secs = round(beats_total * 60.0 / tempo_bpm, 1)

        return {
            "file_path": midi_path,
            "duration_seconds": duration_secs,
            "chord_count": len(chords),
            "tempo_bpm": tempo_bpm,
            "chords": chords,
        }
    except Exception as e:
        return {"error": f"MIDI generation failed: {e}"}


def generate_scale_midi(
    scale_name: str,
    root: str = "C",
    tempo_bpm: int = 100,
    direction: str = "ascending",
) -> dict:
    """Generate a MIDI file playing a scale ascending and/or descending.

    Args:
        scale_name: Scale type like "major", "minor", "dorian", "mixolydian"
        root: Root note like "C", "D", "Bb"
        tempo_bpm: Tempo in BPM
        direction: "ascending", "descending", or "both"

    Returns:
        Dict with file_path, notes, or error.
    """
    scale_cls = SCALE_MAP.get(scale_name.lower())
    if not scale_cls:
        supported = ", ".join(sorted(SCALE_MAP.keys()))
        return {"error": f"Unknown scale '{scale_name}'. Supported: {supported}"}

    try:
        sc = scale_cls(note.Note(root))
    except Exception:
        return {"error": f"Couldn't parse root note '{root}'."}

    try:
        pitches = sc.getPitches(f"{root}4", f"{root}5")
        note_names = [p.name for p in pitches]

        s = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, tempo.MetronomeMark(number=tempo_bpm))

        notes_to_add = list(pitches)
        if direction == "descending":
            notes_to_add = list(reversed(pitches))
        elif direction == "both":
            notes_to_add = list(pitches) + list(reversed(pitches[:-1]))

        for pitch in notes_to_add:
            n = note.Note(pitch)
            n.quarterLength = 1  # quarter note
            p.append(n)

        s.append(p)
        midi_path = _get_output_path("scale")
        s.write("midi", fp=midi_path)

        return {
            "file_path": midi_path,
            "scale_name": f"{root} {scale_name}",
            "notes": note_names,
            "direction": direction,
        }
    except Exception as e:
        return {"error": f"Scale MIDI generation failed: {e}"}
