# Woodshed AI — ABC Notation Generation
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate ABC notation from chord progressions and scales for browser rendering."""

from music21 import harmony, note, scale

from app.theory.engine import _parse_key_string

# Scale type -> music21 class (reuse from midi_gen)
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


def _pitch_to_abc(pitch) -> str:
    """Convert a music21 Pitch object to ABC notation.

    ABC conventions:
    - C4 = C (middle C)
    - C5 = c (lowercase = one octave up)
    - C6 = c' (apostrophe = two octaves up)
    - C3 = C, (comma = one octave down)
    - Sharps: ^C, Flats: _B
    """
    name = pitch.step  # letter name without accidental
    octave = pitch.octave

    # Accidentals
    acc = ""
    if pitch.accidental:
        if pitch.accidental.alter == 1:
            acc = "^"
        elif pitch.accidental.alter == -1:
            acc = "_"
        elif pitch.accidental.alter == 2:
            acc = "^^"
        elif pitch.accidental.alter == -2:
            acc = "__"

    # Octave: C4 is the reference (uppercase, no modifier)
    if octave is None:
        octave = 4

    if octave >= 5:
        # Lowercase letter + apostrophes for each octave above 5
        letter = name.lower()
        letter += "'" * (octave - 5)
    elif octave == 4:
        letter = name
    else:
        # Uppercase letter + commas for each octave below 4
        letter = name
        letter += "," * (4 - octave)

    return acc + letter


def _key_to_abc(key_str: str | None) -> str:
    """Convert a key string to ABC key field value."""
    if not key_str:
        return "C"
    try:
        k = _parse_key_string(key_str)
        abc_key = k.tonic.name.replace("-", "b")
        if k.mode == "minor":
            abc_key += "m"
        elif k.mode and k.mode != "major":
            abc_key += " " + k.mode
        return abc_key
    except Exception:
        return "C"


def chords_to_abc(
    chords: list[str],
    key_str: str | None = None,
    time_sig: str = "4/4",
    title: str | None = None,
) -> str:
    """Convert a chord progression to ABC notation string.

    Args:
        chords: Chord symbols like ["Dm7", "G7", "Cmaj7"]
        key_str: Key signature like "C major"
        time_sig: Time signature
        title: Optional title for the notation

    Returns:
        ABC notation string that abcjs can render.
    """
    if not chords:
        return ""

    abc_key = _key_to_abc(key_str)
    display_title = title or " - ".join(chords)

    lines = [
        "X:1",
        f"T:{display_title}",
        f"M:{time_sig}",
        "L:1/4",
        f"K:{abc_key}",
    ]

    # Build the notation body — each chord as a whole-note chord
    measures = []
    for chord_symbol in chords:
        try:
            cs = harmony.ChordSymbol(chord_symbol)
            pitches = cs.pitches
            # Convert pitches to ABC notation
            abc_notes = [_pitch_to_abc(p) for p in pitches]
            # Chord annotation above staff + chord notes
            chord_str = f'"{chord_symbol}"[{" ".join(abc_notes)}]4'
            measures.append(chord_str)
        except Exception:
            # Fallback: just show the chord name with a rest
            measures.append(f'"{chord_symbol}"z4')

    # Group into measures (one chord per measure with bar lines)
    body = " | ".join(measures) + " |]"
    lines.append(body)

    return "\n".join(lines)


def scale_to_abc(
    scale_name: str,
    root: str = "C",
    title: str | None = None,
) -> str:
    """Convert a scale to ABC notation string.

    Args:
        scale_name: Scale type like "major", "minor", "dorian"
        root: Root note like "C", "D", "Bb"
        title: Optional title for the notation

    Returns:
        ABC notation string that abcjs can render.
    """
    scale_cls = SCALE_MAP.get(scale_name.lower())
    if not scale_cls:
        return ""

    try:
        sc = scale_cls(note.Note(root))
        pitches = sc.getPitches(f"{root}4", f"{root}5")
    except Exception:
        return ""

    display_title = title or f"{root} {scale_name.title()} Scale"
    abc_key = root.replace("-", "b")

    lines = [
        "X:1",
        f"T:{display_title}",
        "M:4/4",
        "L:1/4",
        f"K:{abc_key}",
    ]

    abc_notes = [_pitch_to_abc(p) for p in pitches]
    body = " ".join(abc_notes) + " |]"
    lines.append(body)

    return "\n".join(lines)
