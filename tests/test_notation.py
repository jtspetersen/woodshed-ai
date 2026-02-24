# Woodshed AI — Notation Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from app.output.notation import chords_to_abc, scale_to_abc


class TestChordsToAbc(unittest.TestCase):
    def test_basic_progression(self):
        abc = chords_to_abc(["C", "Am", "F", "G"], key_str="C major")
        self.assertIn("X:1", abc)
        self.assertIn("K:C", abc)
        self.assertIn('"C"', abc)
        self.assertIn('"Am"', abc)

    def test_with_title(self):
        abc = chords_to_abc(["Dm7", "G7"], title="Jazz ii-V")
        self.assertIn("T:Jazz ii-V", abc)

    def test_auto_title(self):
        abc = chords_to_abc(["C", "G"])
        self.assertIn("T:C - G", abc)

    def test_time_signature(self):
        abc = chords_to_abc(["C"], time_sig="3/4")
        self.assertIn("M:3/4", abc)

    def test_empty_chords(self):
        abc = chords_to_abc([])
        self.assertEqual(abc, "")

    def test_has_bar_lines(self):
        abc = chords_to_abc(["C", "Am", "F", "G"])
        self.assertIn("|", abc)

    def test_minor_key(self):
        abc = chords_to_abc(["Am", "Dm"], key_str="A minor")
        self.assertIn("K:Am", abc)


class TestScaleToAbc(unittest.TestCase):
    def test_major_scale(self):
        abc = scale_to_abc("major", root="C")
        self.assertIn("X:1", abc)
        self.assertIn("C Major", abc)
        self.assertIn("C", abc)

    def test_minor_scale(self):
        abc = scale_to_abc("minor", root="A")
        self.assertIn("A Minor", abc)

    def test_with_title(self):
        abc = scale_to_abc("dorian", root="D", title="D Dorian Mode")
        self.assertIn("T:D Dorian Mode", abc)

    def test_unknown_scale(self):
        abc = scale_to_abc("superlocrian")
        self.assertEqual(abc, "")


if __name__ == "__main__":
    unittest.main()
