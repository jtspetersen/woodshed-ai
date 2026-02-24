# Woodshed AI — MIDI Generation Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

import pretty_midi

from app.output.midi_gen import generate_progression_midi, generate_scale_midi


class TestGenerateProgressionMidi(unittest.TestCase):
    def test_basic_progression(self):
        result = generate_progression_midi(["C", "Am", "F", "G"])
        self.assertNotIn("error", result)
        self.assertIn("file_path", result)
        self.assertTrue(os.path.isfile(result["file_path"]))
        self.assertEqual(result["chord_count"], 4)
        # Verify it's a valid MIDI file
        pm = pretty_midi.PrettyMIDI(result["file_path"])
        self.assertGreater(len(pm.instruments), 0)

    def test_with_key_and_tempo(self):
        result = generate_progression_midi(
            ["Dm7", "G7", "Cmaj7"], key_str="C major", tempo_bpm=140
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["tempo_bpm"], 140)

    def test_with_instrument(self):
        result = generate_progression_midi(["Am", "E7"], instrument_name="guitar")
        self.assertNotIn("error", result)
        self.assertTrue(os.path.isfile(result["file_path"]))

    def test_invalid_chord(self):
        result = generate_progression_midi(["Xzz9"])
        self.assertIn("error", result)

    def test_empty_chords(self):
        result = generate_progression_midi([])
        self.assertIn("error", result)

    def test_beats_per_chord(self):
        result = generate_progression_midi(["C", "G"], beats_per_chord=2, tempo_bpm=120)
        self.assertNotIn("error", result)
        # 2 chords * 2 beats = 4 beats at 120 BPM = 2 seconds
        self.assertAlmostEqual(result["duration_seconds"], 2.0)


class TestGenerateScaleMidi(unittest.TestCase):
    def test_major_scale(self):
        result = generate_scale_midi("major", root="C")
        self.assertNotIn("error", result)
        self.assertTrue(os.path.isfile(result["file_path"]))
        self.assertIn("C", result["notes"])

    def test_dorian_scale(self):
        result = generate_scale_midi("dorian", root="D")
        self.assertNotIn("error", result)
        self.assertEqual(result["scale_name"], "D dorian")

    def test_both_directions(self):
        result = generate_scale_midi("minor", root="A", direction="both")
        self.assertNotIn("error", result)
        self.assertEqual(result["direction"], "both")

    def test_unknown_scale(self):
        result = generate_scale_midi("superlocrian")
        self.assertIn("error", result)

    def test_invalid_root(self):
        result = generate_scale_midi("major", root="Z")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
