# Woodshed AI — Music Theory Engine
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Music theory functions powered by music21, exposed as LLM-callable tools."""

from music21 import chord, harmony, interval as m21interval, key, note, roman, scale, stream


def _parse_key_string(key_str: str) -> key.Key:
    """Parse a key string like 'C major', 'A minor', 'C', 'a' into a music21 Key.

    music21's key.Key() doesn't accept 'C major' as a single string —
    it needs tonic and mode as separate args, or shorthand like 'C' (major)
    or 'c' (minor).
    """
    parts = key_str.strip().split()
    if len(parts) == 2:
        tonic, mode = parts
        # music21 convention: uppercase tonic for major, lowercase for minor
        if mode.lower() == "minor":
            tonic = tonic[0].lower() + tonic[1:]
        else:
            tonic = tonic[0].upper() + tonic[1:]
        return key.Key(tonic)
    # Single token — pass directly
    return key.Key(key_str)


# ---------------------------------------------------------------------------
# Mood → scale mapping
# ---------------------------------------------------------------------------
MOOD_SCALES = {
    "melancholy": [
        ("Natural Minor (Aeolian)", "minor", "The classic sad/reflective sound"),
        ("Dorian", "dorian", "Minor with a brighter 6th — melancholy but not defeated"),
    ],
    "sad": [
        ("Natural Minor (Aeolian)", "minor", "The quintessential sad scale"),
        ("Phrygian", "phrygian", "Dark and haunting — deeper sadness"),
    ],
    "bright": [
        ("Major (Ionian)", "major", "The happiest, most resolved sound"),
        ("Lydian", "lydian", "Major with a dreamy, floating #4"),
    ],
    "happy": [
        ("Major (Ionian)", "major", "Pure brightness and resolution"),
        ("Mixolydian", "mixolydian", "Major with a bluesy b7 — happy but grounded"),
    ],
    "dark": [
        ("Phrygian", "phrygian", "Dark and exotic — flamenco, metal"),
        ("Locrian", "locrian", "The darkest mode — unstable, tense"),
    ],
    "mysterious": [
        ("Whole Tone", "whole-tone", "Dreamlike, no resolution — Debussy territory"),
        ("Lydian", "lydian", "Floating, otherworldly quality from the #4"),
    ],
    "jazzy": [
        ("Mixolydian", "mixolydian", "The dominant scale — bluesy, groovy, jazzy"),
        ("Dorian", "dorian", "The go-to minor mode in jazz"),
    ],
    "bluesy": [
        ("Mixolydian", "mixolydian", "Dominant feel — the backbone of blues"),
        ("Minor Pentatonic", "minor-pentatonic", "The blues box — raw and expressive"),
    ],
    "dreamy": [
        ("Lydian", "lydian", "Floaty, ethereal #4 gives a suspended feel"),
        ("Whole Tone", "whole-tone", "No gravity, pure drift"),
    ],
    "aggressive": [
        ("Phrygian", "phrygian", "Dark and driving — common in metal"),
        ("Locrian", "locrian", "Maximum dissonance and tension"),
    ],
    "peaceful": [
        ("Major (Ionian)", "major", "Stable, resolved, calm"),
        ("Major Pentatonic", "major-pentatonic", "Simple, open, folk-like clarity"),
    ],
    "tense": [
        ("Locrian", "locrian", "Diminished tonic — never resolves"),
        ("Phrygian", "phrygian", "Dark tension with a b2"),
    ],
}

# Common chord resolution patterns by style
STYLE_PATTERNS = {
    "general": {
        "I": ["IV", "V", "vi", "ii"],
        "ii": ["V", "viio"],
        "iii": ["vi", "IV"],
        "IV": ["V", "I", "ii"],
        "V": ["I", "vi"],
        "vi": ["ii", "IV", "V"],
        "viio": ["I", "iii"],
    },
    "jazz": {
        "ii": ["V7", "bII7"],
        "V": ["Imaj7", "vi7", "bVImaj7"],
        "I": ["IVmaj7", "ii7", "#ivo7"],
        "IV": ["iii7", "bVII7"],
        "vi": ["ii7"],
        "iii": ["vi7", "VI7"],
    },
    "blues": {
        "I": ["IV7", "V7"],
        "IV": ["I7", "V7"],
        "V": ["IV7", "I7"],
    },
    "pop": {
        "I": ["V", "vi", "IV"],
        "IV": ["V", "I"],
        "V": ["vi", "I"],
        "vi": ["IV", "V"],
    },
}


def analyze_chord(chord_symbol: str) -> dict:
    """Analyze a chord symbol and return its components.

    Args:
        chord_symbol: A chord symbol like "Dm7", "Cmaj7", "G7"

    Returns:
        Dict with root, quality, notes, and intervals.
    """
    try:
        cs = harmony.ChordSymbol(chord_symbol)
    except Exception:
        return {"error": f"Couldn't parse chord symbol '{chord_symbol}'. Try standard notation like Dm7, Cmaj7, G7."}

    pitches = [p.name for p in cs.pitches]
    intervals = []
    root_pitch = cs.root()
    for p in cs.pitches[1:]:
        iv = m21interval.Interval(root_pitch, p)
        intervals.append(iv.niceName)

    return {
        "chord": chord_symbol,
        "root": cs.root().name,
        "quality": cs.chordKind or cs.quality,
        "notes": pitches,
        "intervals": intervals,
        "bass": cs.bass().name if cs.bass() != cs.root() else None,
    }


def analyze_progression(chords: list[str], key_str: str | None = None) -> dict:
    """Analyze a chord progression, optionally in a specified key.

    Args:
        chords: List of chord symbols like ["Am", "F", "C", "G"]
        key_str: Optional key like "C major" or "A minor". Auto-detected if omitted.

    Returns:
        Dict with detected key, roman numerals, and analysis.
    """
    if not chords:
        return {"error": "No chords provided."}

    parsed = []
    for c in chords:
        try:
            parsed.append(harmony.ChordSymbol(c))
        except Exception:
            return {"error": f"Couldn't parse chord '{c}'."}

    # Detect or parse key
    if key_str:
        try:
            k = _parse_key_string(key_str)
        except Exception:
            return {"error": f"Couldn't parse key '{key_str}'. Try 'C major' or 'A minor'."}
    else:
        s = stream.Stream()
        for cs in parsed:
            s.append(cs)
        k = s.analyze("key")

    # Get roman numerals
    numerals = []
    for cs in parsed:
        try:
            rn = roman.romanNumeralFromChord(cs, k)
            numerals.append(str(rn.figure))
        except Exception:
            numerals.append("?")

    return {
        "chords": chords,
        "key": str(k),
        "roman_numerals": numerals,
        "analysis": f"This progression is in {k}. The roman numerals are: {' → '.join(numerals)}.",
    }


def suggest_next_chord(chords: list[str], style: str = "general") -> dict:
    """Suggest chords that could follow the given progression.

    Args:
        chords: List of chord symbols like ["Dm7", "G7"]
        style: One of "general", "jazz", "blues", "pop"

    Returns:
        Dict with a list of suggestions, each with chord name and reason.
    """
    if not chords:
        return {"error": "No chords provided."}

    analysis = analyze_progression(chords)
    if "error" in analysis:
        return analysis

    k = _parse_key_string(analysis["key"])
    last_numeral = analysis["roman_numerals"][-1]

    patterns = STYLE_PATTERNS.get(style, STYLE_PATTERNS["general"])
    suggestions = []

    # Strip quality suffixes for pattern matching
    last_base = last_numeral.rstrip("0123456789").replace("o", "").replace("+", "")

    for pattern_key, targets in patterns.items():
        if last_base.lower() == pattern_key.lower() or last_numeral.lower().startswith(pattern_key.lower()):
            for target in targets:
                try:
                    rn = roman.RomanNumeral(target, k)
                    # Try to get a chord symbol
                    try:
                        cs = harmony.chordSymbolFromChord(chord.Chord(rn.pitches))
                        chord_name = str(cs.figure)
                    except Exception:
                        chord_name = " ".join(str(p) for p in rn.pitches)
                    suggestions.append({
                        "chord": chord_name,
                        "roman_numeral": target,
                        "reason": f"{last_numeral} → {target} in {k}",
                    })
                except Exception:
                    suggestions.append({
                        "chord": target,
                        "roman_numeral": target,
                        "reason": f"Common resolution from {last_numeral}",
                    })

    # Fallback: diatonic options
    if not suggestions:
        for degree in ["I", "IV", "V", "vi"]:
            try:
                rn = roman.RomanNumeral(degree, k)
                cs = harmony.chordSymbolFromChord(chord.Chord(rn.pitches))
                suggestions.append({
                    "chord": str(cs.figure),
                    "roman_numeral": degree,
                    "reason": f"Diatonic {degree} chord in {k}",
                })
            except Exception:
                pass

    return {
        "current_progression": chords,
        "key": str(k),
        "style": style,
        "suggestions": suggestions[:5],
    }


def get_scale_for_mood(mood: str, root: str | None = None) -> dict:
    """Suggest scales that match a given mood or emotional descriptor.

    Args:
        mood: An emotional descriptor like "melancholy", "bright", "jazzy"
        root: Optional root note like "D", "E", "Bb". Defaults to C.

    Returns:
        Dict with a list of scale suggestions.
    """
    mood_lower = mood.lower().strip()
    root_note = root or "C"

    # Find matching moods (allow partial matches)
    matches = None
    for m, scales_info in MOOD_SCALES.items():
        if m in mood_lower or mood_lower in m:
            matches = scales_info
            break

    if not matches:
        matches = [
            ("Major (Ionian)", "major", "A good starting point for any mood"),
            ("Natural Minor (Aeolian)", "minor", "Try this for a darker color"),
        ]

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
    # Pentatonic scales: built from major/minor by selecting degrees
    PENTATONIC_DEGREES = {
        "major-pentatonic": (scale.MajorScale, [1, 2, 3, 5, 6]),
        "minor-pentatonic": (scale.MinorScale, [1, 3, 4, 5, 7]),
    }

    results = []
    for scale_name, scale_type, reason in matches:
        try:
            if scale_type in PENTATONIC_DEGREES:
                base_cls, degrees = PENTATONIC_DEGREES[scale_type]
                s = base_cls(note.Note(root_note))
                pitches = [s.pitchFromDegree(d) for d in degrees]
                pitches.append(note.Note(root_note + "5").pitch)  # add octave
            elif scale_type in SCALE_MAP:
                s = SCALE_MAP[scale_type](note.Note(root_note))
                pitches = s.getPitches(root_note + "4", root_note + "5")
            else:
                s = scale.MajorScale(note.Note(root_note))
                pitches = s.getPitches(root_note + "4", root_note + "5")
            results.append({
                "name": f"{root_note} {scale_name}",
                "notes": [p.name for p in pitches],
                "why": reason,
            })
        except Exception:
            results.append({
                "name": f"{root_note} {scale_name}",
                "notes": [],
                "why": reason,
            })

    return {"mood": mood, "root": root_note, "scales": results}


def detect_key(notes_list: list[str]) -> dict:
    """Detect the most likely key from a list of note names.

    Args:
        notes_list: List of note names like ["C", "E", "G", "A"]

    Returns:
        Dict with key, confidence, and alternative keys.
    """
    if not notes_list:
        return {"error": "No notes provided."}

    s = stream.Stream()
    for n in notes_list:
        try:
            s.append(note.Note(n))
        except Exception:
            return {"error": f"Couldn't parse note '{n}'."}

    k = s.analyze("key")

    # Get top alternatives by re-running analysis and picking runner-ups
    alt_keys = []
    try:
        # music21's key analysis returns alternateInterpretations
        for alt in k.alternateInterpretations[:3]:
            alt_keys.append({
                "key": f"{alt.tonic.name} {alt.mode}",
                "confidence": round(alt.correlationCoefficient, 3),
            })
    except Exception:
        pass

    return {
        "key": str(k),
        "confidence": round(k.correlationCoefficient, 3),
        "alternatives": alt_keys,
    }


# Common guitar voicings (curated)
GUITAR_VOICINGS = {
    "C": [{"name": "Open C", "frets": "x32010", "description": "Standard open C major"}],
    "D": [{"name": "Open D", "frets": "xx0232", "description": "Standard open D major"}],
    "E": [{"name": "Open E", "frets": "022100", "description": "Standard open E major"}],
    "F": [{"name": "Barre F", "frets": "133211", "description": "F barre chord, 1st fret"}],
    "G": [{"name": "Open G", "frets": "320003", "description": "Standard open G major"}],
    "A": [{"name": "Open A", "frets": "x02220", "description": "Standard open A major"}],
    "Am": [{"name": "Open Am", "frets": "x02210", "description": "Standard open A minor"}],
    "Em": [{"name": "Open Em", "frets": "022000", "description": "Standard open E minor"}],
    "Dm": [{"name": "Open Dm", "frets": "xx0231", "description": "Standard open D minor"}],
    "Dm7": [{"name": "Open Dm7", "frets": "xx0211", "description": "Open D minor 7th"}],
    "G7": [{"name": "Open G7", "frets": "320001", "description": "Open G dominant 7th"}],
    "C7": [{"name": "Open C7", "frets": "x32310", "description": "Open C dominant 7th"}],
    "Am7": [{"name": "Open Am7", "frets": "x02010", "description": "Open A minor 7th"}],
    "Cmaj7": [{"name": "Open Cmaj7", "frets": "x32000", "description": "Open C major 7th"}],
    "Fmaj7": [{"name": "Open Fmaj7", "frets": "xx3210", "description": "Open F major 7th"}],
    "E7": [{"name": "Open E7", "frets": "020100", "description": "Open E dominant 7th"}],
    "A7": [{"name": "Open A7", "frets": "x02020", "description": "Open A dominant 7th"}],
    "D7": [{"name": "Open D7", "frets": "xx0212", "description": "Open D dominant 7th"}],
    "Bm": [{"name": "Barre Bm", "frets": "x24432", "description": "B minor barre, 2nd fret"}],
}


def get_chord_voicings(chord_symbol: str, instrument: str = "guitar") -> dict:
    """Get common voicings for a chord on a given instrument.

    Args:
        chord_symbol: A chord symbol like "Dm7", "G", "Cmaj7"
        instrument: Currently only "guitar" is supported.

    Returns:
        Dict with voicing information.
    """
    if instrument.lower() != "guitar":
        return {
            "chord": chord_symbol,
            "instrument": instrument,
            "voicings": [],
            "note": f"Voicings for {instrument} aren't supported yet — guitar only for now.",
        }

    voicings = GUITAR_VOICINGS.get(chord_symbol, [])
    if not voicings:
        info = analyze_chord(chord_symbol)
        return {
            "chord": chord_symbol,
            "instrument": "guitar",
            "voicings": [],
            "note": f"No pre-built voicing for {chord_symbol}. Notes: {info.get('notes', 'unknown')}. Try a chord chart app for fingering.",
        }

    return {"chord": chord_symbol, "instrument": "guitar", "voicings": voicings}


def get_related_chords(chord_symbol: str) -> dict:
    """Find substitutions, extensions, and borrowed chords for a given chord.

    Args:
        chord_symbol: A chord symbol like "Dm7", "G7", "Cmaj7"

    Returns:
        Dict with substitutions, extensions, and borrowed chords.
    """
    try:
        cs = harmony.ChordSymbol(chord_symbol)
    except Exception:
        return {"error": f"Couldn't parse chord symbol '{chord_symbol}'."}

    root = cs.root()
    quality = (cs.chordKind or "").lower()
    root_name = str(root.name)
    is_minor = "minor" in quality or ("m" in chord_symbol and "maj" not in chord_symbol.lower())
    is_dominant = "dominant" in quality or (chord_symbol.endswith("7") and not is_minor and "maj" not in chord_symbol.lower())

    substitutions = []
    extensions = []
    borrowed = []

    # Tritone substitution (for dominant 7ths)
    if is_dominant:
        tritone_root = root.transpose(m21interval.Interval("A4"))
        sub = f"{tritone_root.name}7"
        substitutions.append({
            "chord": sub,
            "type": "Tritone substitution",
            "reason": f"{chord_symbol} and {sub} share the same tritone interval, so they can replace each other.",
        })

    # Relative major/minor swap
    if is_minor:
        rel_root = root.transpose("m3")
        substitutions.append({
            "chord": f"{rel_root.name}",
            "type": "Relative major",
            "reason": f"{chord_symbol} and {rel_root.name} share most of the same notes.",
        })
    elif not is_dominant:
        rel_root = root.transpose("-m3")
        substitutions.append({
            "chord": f"{rel_root.name}m",
            "type": "Relative minor",
            "reason": f"{chord_symbol} and {rel_root.name}m share most of the same notes.",
        })

    # Extensions
    if is_minor:
        extensions.append({"chord": f"{root_name}m9", "type": "Add 9th", "reason": "Adds color and openness."})
        extensions.append({"chord": f"{root_name}m11", "type": "Add 11th", "reason": "Suspended, modern sound."})
    elif is_dominant:
        extensions.append({"chord": f"{root_name}9", "type": "Add 9th", "reason": "Funky, soulful extension."})
        extensions.append({"chord": f"{root_name}13", "type": "Add 13th", "reason": "Rich, full jazz voicing."})
    else:
        extensions.append({"chord": f"{root_name}maj9", "type": "Add 9th", "reason": "Lush, dreamy extension."})
        extensions.append({"chord": f"{root_name}add9", "type": "Add 9 (no 7th)", "reason": "Open, modern pop sound."})

    # Borrowed chords (parallel major/minor interchange)
    if is_minor:
        borrowed.append({
            "chord": root_name,
            "type": "Parallel major",
            "reason": f"Borrow from {root_name} major for a brighter color.",
        })
    else:
        borrowed.append({
            "chord": f"{root_name}m",
            "type": "Parallel minor",
            "reason": f"Borrow from {root_name} minor for a darker color.",
        })

    return {
        "chord": chord_symbol,
        "substitutions": substitutions,
        "extensions": extensions,
        "borrowed_chords": borrowed,
    }
