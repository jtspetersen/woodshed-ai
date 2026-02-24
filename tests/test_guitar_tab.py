# Woodshed AI — Guitar Tab Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from app.output.guitar_tab import generate_chord_tab, generate_progression_tab


class TestGenerateChordTab(unittest.TestCase):
    def test_known_chord(self):
        result = generate_chord_tab("Am")
        self.assertNotIn("error", result)
        self.assertIn("e|", result["tab"])
        self.assertIn("E|", result["tab"])
        self.assertEqual(result["frets"], "x02210")

    def test_diagram_has_all_strings(self):
        result = generate_chord_tab("C")
        for string in ["e|", "B|", "G|", "D|", "A|", "E|"]:
            self.assertIn(string, result["tab"])

    def test_unknown_chord(self):
        result = generate_chord_tab("Bbm9")
        self.assertIn("error", result)

    def test_chord_name_in_diagram(self):
        result = generate_chord_tab("G")
        self.assertIn("G", result["tab"])


class TestGenerateProgressionTab(unittest.TestCase):
    def test_full_progression(self):
        result = generate_progression_tab(["C", "Am", "F", "G"])
        self.assertNotIn("error", result)
        self.assertEqual(len(result["chords_found"]), 4)
        self.assertEqual(len(result["chords_missing"]), 0)

    def test_mixed_progression(self):
        result = generate_progression_tab(["C", "Bbm9", "G"])
        self.assertNotIn("error", result)
        self.assertEqual(len(result["chords_found"]), 2)
        self.assertEqual(len(result["chords_missing"]), 1)
        self.assertIn("Bbm9", result["chords_missing"])

    def test_all_unknown(self):
        result = generate_progression_tab(["Xzz", "Yyy"])
        self.assertIn("error", result)

    def test_empty_chords(self):
        result = generate_progression_tab([])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
