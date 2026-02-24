# Woodshed AI — Music21 Theory Engine Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the music21-powered theory engine functions."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.theory.engine import (
    analyze_chord,
    analyze_progression,
    detect_key,
    get_chord_voicings,
    get_related_chords,
    get_scale_for_mood,
    suggest_next_chord,
)


def pp(d):
    """Pretty print a dict."""
    print(f"  {json.dumps(d, indent=2, default=str)[:500]}")


def test_analyze_chord():
    result = analyze_chord("Dm7")
    pp(result)
    assert "error" not in result
    assert result["root"] == "D"
    assert "D" in result["notes"][0]
    assert len(result["notes"]) >= 3


def test_analyze_chord_major():
    result = analyze_chord("C")
    pp(result)
    assert "error" not in result
    assert result["root"] == "C"


def test_analyze_chord_invalid():
    result = analyze_chord("Xzz9")
    pp(result)
    assert "error" in result


def test_analyze_progression():
    result = analyze_progression(["Am", "F", "C", "G"])
    pp(result)
    assert "error" not in result
    assert len(result["roman_numerals"]) == 4
    assert result["key"]  # should detect a key


def test_analyze_progression_with_key():
    result = analyze_progression(["Dm7", "G7", "Cmaj7"], key_str="C major")
    pp(result)
    assert "error" not in result
    assert "major" in result["key"].lower()


def test_suggest_next_chord():
    result = suggest_next_chord(["Dm7", "G7"])
    pp(result)
    assert "error" not in result
    assert len(result["suggestions"]) > 0


def test_suggest_next_chord_jazz():
    result = suggest_next_chord(["Dm7", "G7"], style="jazz")
    pp(result)
    assert "error" not in result


def test_get_scale_for_mood():
    result = get_scale_for_mood("melancholy", root="D")
    pp(result)
    assert result["mood"] == "melancholy"
    assert len(result["scales"]) > 0
    assert result["scales"][0]["notes"]  # should have actual notes


def test_get_scale_for_mood_unknown():
    result = get_scale_for_mood("underwater", root="E")
    pp(result)
    # Should fall back to major/minor
    assert len(result["scales"]) > 0


def test_detect_key():
    result = detect_key(["C", "E", "G", "A", "D", "F"])
    pp(result)
    assert "error" not in result
    assert result["key"]
    assert isinstance(result["confidence"], (int, float))


def test_get_chord_voicings():
    result = get_chord_voicings("Am")
    pp(result)
    assert len(result["voicings"]) > 0
    assert result["voicings"][0]["frets"]


def test_get_chord_voicings_unknown():
    result = get_chord_voicings("Bbm9")
    pp(result)
    assert "note" in result  # should have a fallback message


def test_get_related_chords():
    result = get_related_chords("G7")
    pp(result)
    assert "error" not in result
    assert len(result["substitutions"]) > 0  # should have tritone sub
    assert len(result["extensions"]) > 0


def test_get_related_chords_minor():
    result = get_related_chords("Dm7")
    pp(result)
    assert "error" not in result
    assert len(result["extensions"]) > 0


if __name__ == "__main__":
    tests = [
        ("analyze_chord (Dm7)", test_analyze_chord),
        ("analyze_chord (C)", test_analyze_chord_major),
        ("analyze_chord (invalid)", test_analyze_chord_invalid),
        ("analyze_progression", test_analyze_progression),
        ("analyze_progression (with key)", test_analyze_progression_with_key),
        ("suggest_next_chord", test_suggest_next_chord),
        ("suggest_next_chord (jazz)", test_suggest_next_chord_jazz),
        ("get_scale_for_mood", test_get_scale_for_mood),
        ("get_scale_for_mood (unknown)", test_get_scale_for_mood_unknown),
        ("detect_key", test_detect_key),
        ("get_chord_voicings", test_get_chord_voicings),
        ("get_chord_voicings (unknown)", test_get_chord_voicings_unknown),
        ("get_related_chords (G7)", test_get_related_chords),
        ("get_related_chords (Dm7)", test_get_related_chords_minor),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            print(f"  PASSED")
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
