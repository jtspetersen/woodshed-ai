# Woodshed AI — MIDI Analysis
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Parse MIDI files and extract structured musical information."""

import os

import pretty_midi
from music21 import chord as m21chord, harmony, key, note, roman, stream


# Maximum duration (seconds) to analyze — prevents slow processing on huge files
MAX_ANALYSIS_DURATION = 120.0


def analyze_midi(file_path: str) -> dict:
    """Analyze a MIDI file and return structured musical information.

    Args:
        file_path: Path to a .mid or .midi file.

    Returns:
        Dict with key, tempo, time_signature, duration, instruments,
        chords, notes, and a human-readable summary.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        midi = pretty_midi.PrettyMIDI(file_path)
    except Exception as e:
        return {"error": f"Couldn't read MIDI file: {e}"}

    # Basic metadata
    tempo_estimates = midi.estimate_tempi()
    tempo = round(midi.estimate_tempo())
    duration = round(midi.get_end_time(), 2)
    time_sigs = midi.time_signature_changes
    time_sig = (
        f"{time_sigs[0].numerator}/{time_sigs[0].denominator}"
        if time_sigs
        else "4/4"
    )
    instruments = [
        {
            "name": inst.name or pretty_midi.program_to_instrument_name(inst.program),
            "program": inst.program,
            "is_drum": inst.is_drum,
            "note_count": len(inst.notes),
        }
        for inst in midi.instruments
    ]

    # Detailed analysis
    notes = extract_notes(midi)
    key_info = detect_key_from_midi(midi)
    chords = detect_chords_from_midi(midi)

    analysis = {
        "file": os.path.basename(file_path),
        "tempo_bpm": tempo,
        "time_signature": time_sig,
        "duration_seconds": duration,
        "instruments": instruments,
        "total_notes": len(notes),
        "key": key_info,
        "chords": chords,
    }

    analysis["summary"] = get_midi_summary(analysis)
    return analysis


def extract_notes(midi: pretty_midi.PrettyMIDI) -> list[dict]:
    """Extract all notes from a MIDI file.

    Args:
        midi: A loaded PrettyMIDI object.

    Returns:
        List of dicts with pitch, start, end, velocity, instrument info.
    """
    notes = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        inst_name = inst.name or pretty_midi.program_to_instrument_name(inst.program)
        for n in inst.notes:
            if n.start > MAX_ANALYSIS_DURATION:
                break
            notes.append({
                "pitch": pretty_midi.note_number_to_name(n.pitch),
                "midi_number": n.pitch,
                "start": round(n.start, 3),
                "end": round(n.end, 3),
                "velocity": n.velocity,
                "instrument": inst_name,
            })
    notes.sort(key=lambda x: x["start"])
    return notes


def detect_chords_from_midi(midi: pretty_midi.PrettyMIDI) -> list[dict]:
    """Detect chords using beat-aligned windows with duration-weighted notes.

    Aligns analysis windows to the musical beat grid, weights notes by
    how long they sound within each beat, and filters out passing tones
    to produce cleaner chord identification.

    Args:
        midi: A loaded PrettyMIDI object.

    Returns:
        List of dicts with time, chord, and duration.
    """
    end_time = min(midi.get_end_time(), MAX_ANALYSIS_DURATION)
    if end_time <= 0:
        return []

    # Collect all non-drum notes with their actual MIDI pitches
    all_notes = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        all_notes.extend(inst.notes)

    if not all_notes:
        return []

    # Use beat-aligned windows based on tempo
    tempo = midi.estimate_tempo()
    beat_duration = 60.0 / tempo
    # Analyze in half-beat windows for better resolution, min 0.2s
    window = max(beat_duration / 2, 0.2)

    chords = []
    prev_symbol = None
    prev_start = 0.0

    t = 0.0
    while t < end_time:
        window_end = t + window

        # Collect notes with duration-weighting in this window
        pitch_weights: dict[int, float] = {}
        lowest_pitch = 128
        for n in all_notes:
            if n.end <= t or n.start >= window_end:
                continue
            # Duration this note overlaps with the window
            overlap_start = max(n.start, t)
            overlap_end = min(n.end, window_end)
            weight = (overlap_end - overlap_start) * n.velocity
            pc = n.pitch % 12
            pitch_weights[pc] = pitch_weights.get(pc, 0) + weight
            if n.pitch < lowest_pitch:
                lowest_pitch = n.pitch

        # Filter: require at least 3 pitch classes for a chord
        if len(pitch_weights) < 3:
            t += window
            continue

        # Filter out passing tones: discard pitch classes with very low weight
        # (less than 15% of the strongest note's weight)
        max_weight = max(pitch_weights.values())
        threshold = max_weight * 0.15
        strong_pitches = {
            pc for pc, w in pitch_weights.items() if w >= threshold
        }

        if len(strong_pitches) < 3:
            t += window
            continue

        # Identify chord using the actual lowest-sounding pitch as bass
        bass_pc = lowest_pitch % 12
        chord_symbol = _identify_chord(strong_pitches, bass_pc)

        if chord_symbol != prev_symbol:
            if prev_symbol is not None:
                chords.append({
                    "time": round(prev_start, 2),
                    "chord": prev_symbol,
                    "duration": round(t - prev_start, 2),
                })
            prev_symbol = chord_symbol
            prev_start = t

        t += window

    # Append the last chord
    if prev_symbol is not None:
        chords.append({
            "time": round(prev_start, 2),
            "chord": prev_symbol,
            "duration": round(end_time - prev_start, 2),
        })

    # Post-process: remove very short chords (< 1 window) that appear
    # between two identical chords (transition artifacts)
    if len(chords) >= 3:
        filtered = [chords[0]]
        for i in range(1, len(chords) - 1):
            prev_c = filtered[-1]["chord"]
            next_c = chords[i + 1]["chord"]
            cur_dur = chords[i]["duration"]
            # If this chord is very brief and surrounded by the same chord,
            # it's a transition artifact — merge into the previous chord
            if cur_dur <= window * 1.1 and prev_c == next_c:
                continue
            filtered.append(chords[i])
        filtered.append(chords[-1])

        # Merge consecutive identical chords that resulted from filtering
        merged = [filtered[0]]
        for c in filtered[1:]:
            if c["chord"] == merged[-1]["chord"]:
                merged[-1]["duration"] = round(
                    (c["time"] + c["duration"]) - merged[-1]["time"], 2
                )
            else:
                merged.append(c)
        chords = merged

    # Remove very short transition chords (less than a full beat) that sit
    # between two longer chords — absorb them into the previous chord
    min_chord_duration = beat_duration * 0.6
    if len(chords) > 1:
        filtered2 = [chords[0]]
        for c in chords[1:]:
            if c["duration"] < min_chord_duration:
                # Extend previous chord to absorb this one
                filtered2[-1]["duration"] = round(
                    (c["time"] + c["duration"]) - filtered2[-1]["time"], 2
                )
            else:
                filtered2.append(c)
        chords = filtered2

    return chords


def _identify_chord(pitch_classes: set[int], bass_pc: int | None = None) -> str:
    """Identify a chord symbol from a set of pitch classes (0-11).

    Uses music21 to find the best matching chord symbol. When a bass pitch
    class is provided, it's used to determine the correct root/inversion
    rather than defaulting to the lowest pitch class numerically.

    Args:
        pitch_classes: Set of pitch classes (0=C, 1=C#, ... 11=B).
        bass_pc: The actual lowest-sounding pitch class (from MIDI data).
    """
    # Build notes in an octave arrangement that respects the actual bass note
    notes_for_m21 = []
    if bass_pc is not None and bass_pc in pitch_classes:
        # Place bass note in octave 3, others in octave 4
        bass_name = pretty_midi.note_number_to_name(bass_pc + 48)  # octave 3
        notes_for_m21.append(note.Note(bass_name))
        for pc in sorted(pitch_classes):
            if pc == bass_pc:
                continue
            name = pretty_midi.note_number_to_name(pc + 60)  # octave 4
            notes_for_m21.append(note.Note(name))
    else:
        # No bass info — place all in same octave, let music21 figure it out
        for pc in sorted(pitch_classes):
            name = pretty_midi.note_number_to_name(pc + 60)
            notes_for_m21.append(note.Note(name))

    try:
        c = m21chord.Chord(notes_for_m21)
        cs = harmony.chordSymbolFromChord(c)
        figure = str(cs.figure)
        # Clean up: if root matches bass, strip the slash notation
        # e.g., "Am/A" → "Am"
        if "/" in figure:
            parts = figure.split("/")
            root_of_chord = cs.root().name if cs.root() else None
            bass_of_chord = parts[-1]
            if root_of_chord and root_of_chord == bass_of_chord:
                figure = parts[0]
        return figure
    except Exception:
        # Fallback: list note names
        names = [pretty_midi.note_number_to_name(pc + 60) for pc in sorted(pitch_classes)]
        cleaned = [n[:-1] if n[-1].isdigit() else n for n in names]
        return "/".join(cleaned)


def detect_key_from_midi(midi: pretty_midi.PrettyMIDI) -> dict:
    """Detect the most likely key from MIDI note content.

    Args:
        midi: A loaded PrettyMIDI object.

    Returns:
        Dict with key, confidence, and alternatives.
    """
    # Collect all pitched notes
    all_pitch_names = set()
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            if n.start > MAX_ANALYSIS_DURATION:
                break
            name = pretty_midi.note_number_to_name(n.pitch)
            # Strip octave number
            all_pitch_names.add(name[:-1] if name[-1].isdigit() else name)

    if not all_pitch_names:
        return {"key": "unknown", "confidence": 0, "alternatives": []}

    # Build a music21 stream and analyze
    s = stream.Stream()
    for n in all_pitch_names:
        try:
            s.append(note.Note(n))
        except Exception:
            continue

    if len(s) == 0:
        return {"key": "unknown", "confidence": 0, "alternatives": []}

    k = s.analyze("key")

    alternatives = []
    try:
        for alt in k.alternateInterpretations[:3]:
            alternatives.append({
                "key": f"{alt.tonic.name} {alt.mode}",
                "confidence": round(alt.correlationCoefficient * 100),
            })
    except Exception:
        pass

    return {
        "key": str(k),
        "confidence": round(k.correlationCoefficient * 100),
        "alternatives": alternatives,
    }


def get_midi_summary(analysis: dict) -> str:
    """Format a MIDI analysis dict into a human-readable summary.

    Args:
        analysis: The dict returned by analyze_midi() (without 'summary' key).

    Returns:
        A multi-line text summary suitable for injecting into LLM context.
    """
    if "error" in analysis:
        return f"MIDI analysis error: {analysis['error']}"

    lines = []
    lines.append(f"MIDI File: {analysis.get('file', 'unknown')}")
    lines.append(f"Tempo: {analysis['tempo_bpm']} BPM")
    lines.append(f"Time Signature: {analysis['time_signature']}")
    lines.append(f"Duration: {analysis['duration_seconds']}s")

    # Key
    key_info = analysis.get("key", {})
    if key_info.get("key") and key_info["key"] != "unknown":
        lines.append(
            f"Detected Key: {key_info['key']} ({key_info.get('confidence', '?')}% confidence)"
        )

    # Instruments
    instruments = analysis.get("instruments", [])
    if instruments:
        inst_names = [i["name"] for i in instruments if not i["is_drum"]]
        drum_count = sum(1 for i in instruments if i["is_drum"])
        if inst_names:
            lines.append(f"Instruments: {', '.join(inst_names)}")
        if drum_count:
            lines.append(f"Drum tracks: {drum_count}")

    # Chord progression
    chords = analysis.get("chords", [])
    if chords:
        # Deduplicate consecutive identical chords for readability
        chord_sequence = [c["chord"] for c in chords]
        lines.append(f"Chord progression: {' | '.join(chord_sequence)}")

    lines.append(f"Total notes: {analysis.get('total_notes', 0)}")

    return "\n".join(lines)
