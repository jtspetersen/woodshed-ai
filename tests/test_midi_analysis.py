# Woodshed AI — MIDI Analysis Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for app.audio.analyze — MIDI file analysis functions."""

import os
import tempfile
import unittest

import pretty_midi

from app.audio.analyze import (
    analyze_midi,
    detect_chords_from_midi,
    detect_key_from_midi,
    extract_notes,
    get_midi_summary,
)


def _create_test_midi(
    notes: list[tuple[int, float, float]] | None = None,
    tempo: float = 120.0,
    instrument_name: str = "Acoustic Grand Piano",
    program: int = 0,
) -> str:
    """Create a temporary MIDI file for testing.

    Args:
        notes: List of (pitch, start, end) tuples. Defaults to a C major chord progression.
        tempo: Tempo in BPM.
        instrument_name: Name of the instrument.
        program: MIDI program number.

    Returns:
        Path to the temporary MIDI file.
    """
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    inst = pretty_midi.Instrument(program=program, name=instrument_name)

    if notes is None:
        # Default: C-Am-F-G chord progression (1 beat each at 120 BPM = 0.5s each)
        beat = 60.0 / tempo
        # C major: C4, E4, G4
        for pitch in [60, 64, 67]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=0.0, end=beat))
        # A minor: A3, C4, E4
        for pitch in [57, 60, 64]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=beat, end=2 * beat))
        # F major: F3, A3, C4
        for pitch in [53, 57, 60]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=2 * beat, end=3 * beat))
        # G major: G3, B3, D4
        for pitch in [55, 59, 62]:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=3 * beat, end=4 * beat))
    else:
        for pitch, start, end in notes:
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end))

    midi.instruments.append(inst)

    fd, path = tempfile.mkstemp(suffix=".mid")
    os.close(fd)
    midi.write(path)
    return path


class TestAnalyzeMidi(unittest.TestCase):
    """Tests for the main analyze_midi function."""

    def test_basic_analysis(self):
        """analyze_midi returns expected structure for a valid MIDI file."""
        path = _create_test_midi()
        try:
            result = analyze_midi(path)
            self.assertNotIn("error", result)
            self.assertIn("tempo_bpm", result)
            self.assertIn("time_signature", result)
            self.assertIn("duration_seconds", result)
            self.assertIn("instruments", result)
            self.assertIn("key", result)
            self.assertIn("chords", result)
            self.assertIn("summary", result)
            self.assertIn("total_notes", result)
            self.assertGreater(result["total_notes"], 0)
        finally:
            os.unlink(path)

    def test_tempo_detection(self):
        """analyze_midi detects the correct tempo."""
        path = _create_test_midi(tempo=140.0)
        try:
            result = analyze_midi(path)
            # Tempo detection is approximate; check it's in the right range
            self.assertGreater(result["tempo_bpm"], 100)
            self.assertLess(result["tempo_bpm"], 180)
        finally:
            os.unlink(path)

    def test_instruments_listed(self):
        """analyze_midi lists instruments correctly."""
        path = _create_test_midi(instrument_name="Test Piano", program=0)
        try:
            result = analyze_midi(path)
            self.assertEqual(len(result["instruments"]), 1)
            self.assertFalse(result["instruments"][0]["is_drum"])
            self.assertGreater(result["instruments"][0]["note_count"], 0)
        finally:
            os.unlink(path)

    def test_invalid_file(self):
        """analyze_midi returns error for non-existent file."""
        result = analyze_midi("/nonexistent/file.mid")
        self.assertIn("error", result)

    def test_corrupt_file(self):
        """analyze_midi returns error for a corrupt file."""
        fd, path = tempfile.mkstemp(suffix=".mid")
        os.write(fd, b"this is not a valid midi file")
        os.close(fd)
        try:
            result = analyze_midi(path)
            self.assertIn("error", result)
        finally:
            os.unlink(path)


class TestExtractNotes(unittest.TestCase):
    """Tests for extract_notes."""

    def test_extracts_correct_count(self):
        """extract_notes returns all non-drum notes."""
        path = _create_test_midi()
        try:
            midi = pretty_midi.PrettyMIDI(path)
            notes = extract_notes(midi)
            # 4 chords × 3 notes each = 12 notes
            self.assertEqual(len(notes), 12)
        finally:
            os.unlink(path)

    def test_note_structure(self):
        """Each note has expected fields."""
        path = _create_test_midi()
        try:
            midi = pretty_midi.PrettyMIDI(path)
            notes = extract_notes(midi)
            for n in notes:
                self.assertIn("pitch", n)
                self.assertIn("midi_number", n)
                self.assertIn("start", n)
                self.assertIn("end", n)
                self.assertIn("velocity", n)
                self.assertIn("instrument", n)
        finally:
            os.unlink(path)

    def test_sorted_by_start(self):
        """Notes are returned sorted by start time."""
        path = _create_test_midi()
        try:
            midi = pretty_midi.PrettyMIDI(path)
            notes = extract_notes(midi)
            starts = [n["start"] for n in notes]
            self.assertEqual(starts, sorted(starts))
        finally:
            os.unlink(path)


class TestDetectChords(unittest.TestCase):
    """Tests for detect_chords_from_midi."""

    def test_detects_chords(self):
        """detect_chords_from_midi finds chords in a known progression."""
        path = _create_test_midi()
        try:
            midi = pretty_midi.PrettyMIDI(path)
            chords = detect_chords_from_midi(midi)
            self.assertGreater(len(chords), 0)
            for c in chords:
                self.assertIn("time", c)
                self.assertIn("chord", c)
                self.assertIn("duration", c)
            # Verify the C-Am-F-G progression is detected correctly
            chord_names = [c["chord"] for c in chords]
            self.assertIn("C", chord_names)
            self.assertIn("Am", chord_names)
        finally:
            os.unlink(path)

    def test_empty_midi(self):
        """detect_chords_from_midi returns empty list for empty MIDI."""
        midi = pretty_midi.PrettyMIDI()
        midi.instruments.append(pretty_midi.Instrument(program=0))
        chords = detect_chords_from_midi(midi)
        self.assertEqual(chords, [])


class TestDetectKey(unittest.TestCase):
    """Tests for detect_key_from_midi."""

    def test_detects_key(self):
        """detect_key_from_midi returns a key for a C major progression."""
        path = _create_test_midi()
        try:
            midi = pretty_midi.PrettyMIDI(path)
            key_info = detect_key_from_midi(midi)
            self.assertIn("key", key_info)
            self.assertIn("confidence", key_info)
            self.assertNotEqual(key_info["key"], "unknown")
            # The C-Am-F-G progression should be detected as C major or A minor
            self.assertTrue(
                "C major" in key_info["key"] or "a minor" in key_info["key"].lower(),
                f"Expected C major or A minor, got {key_info['key']}",
            )
        finally:
            os.unlink(path)

    def test_empty_midi_returns_unknown(self):
        """detect_key_from_midi returns unknown for empty MIDI."""
        midi = pretty_midi.PrettyMIDI()
        midi.instruments.append(pretty_midi.Instrument(program=0))
        key_info = detect_key_from_midi(midi)
        self.assertEqual(key_info["key"], "unknown")


class TestGetMidiSummary(unittest.TestCase):
    """Tests for get_midi_summary."""

    def test_summary_format(self):
        """get_midi_summary returns readable text."""
        path = _create_test_midi()
        try:
            result = analyze_midi(path)
            summary = result["summary"]
            self.assertIn("Tempo:", summary)
            self.assertIn("BPM", summary)
            self.assertIn("Detected Key:", summary)
            self.assertIn("Total notes:", summary)
        finally:
            os.unlink(path)

    def test_error_summary(self):
        """get_midi_summary handles error dicts."""
        summary = get_midi_summary({"error": "test error"})
        self.assertIn("error", summary.lower())


if __name__ == "__main__":
    unittest.main()
