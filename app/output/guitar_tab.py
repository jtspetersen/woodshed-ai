# Woodshed AI — Guitar Tab Generation
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate ASCII guitar chord diagrams and tablature."""

from app.theory.engine import GUITAR_VOICINGS

# String names from high to low (display order)
STRING_NAMES = ["e", "B", "G", "D", "A", "E"]


def _frets_to_diagram(chord_name: str, frets: str) -> str:
    """Convert a fret string like 'x32010' to an ASCII chord diagram.

    The fret string has 6 characters, one per string (EADGBE low to high).
    'x' means muted, '0' means open, digits are fret numbers.
    """
    # frets string is low-to-high (E A D G B e), reverse for display (e B G D A E)
    fret_list = list(reversed(frets))

    lines = [f"  {chord_name}"]
    for i, string_name in enumerate(STRING_NAMES):
        fret = fret_list[i]
        if fret == "x":
            lines.append(f"{string_name}|---x---|")
        elif fret == "0":
            lines.append(f"{string_name}|---0---|")
        else:
            lines.append(f"{string_name}|---{fret}---|")

    return "\n".join(lines)


def generate_chord_tab(chord_symbol: str) -> dict:
    """Generate an ASCII guitar chord diagram for a single chord.

    Returns:
        Dict with chord, tab, frets, or error if chord not in voicing database.
    """
    voicings = GUITAR_VOICINGS.get(chord_symbol, [])
    if not voicings:
        return {
            "error": f"No guitar voicing available for '{chord_symbol}'. "
                     f"Try common chords like C, Am, G7, Dm7."
        }

    voicing = voicings[0]  # Use the first (primary) voicing
    diagram = _frets_to_diagram(chord_symbol, voicing["frets"])

    return {
        "chord": chord_symbol,
        "tab": diagram,
        "frets": voicing["frets"],
        "name": voicing["name"],
    }


def generate_progression_tab(chords: list[str]) -> dict:
    """Generate ASCII guitar tab for a chord progression.

    Returns:
        Dict with tab (formatted ASCII string), chords_found, chords_missing.
    """
    if not chords:
        return {"error": "No chords provided."}

    diagrams = []
    chords_found = []
    chords_missing = []

    for chord_symbol in chords:
        result = generate_chord_tab(chord_symbol)
        if "error" in result:
            chords_missing.append(chord_symbol)
        else:
            diagrams.append(result["tab"])
            chords_found.append(chord_symbol)

    if not diagrams:
        return {
            "error": "No guitar voicings found for any of the provided chords.",
            "chords_missing": chords_missing,
        }

    tab = "\n\n".join(diagrams)

    if chords_missing:
        tab += f"\n\n(No voicing available for: {', '.join(chords_missing)})"

    return {
        "tab": tab,
        "chords_found": chords_found,
        "chords_missing": chords_missing,
    }
