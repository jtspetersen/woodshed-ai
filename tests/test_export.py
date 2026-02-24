# Woodshed AI — Export Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from app.output.export import (
    export_for_daw,
    export_musicxml,
    export_tab_text,
    get_daw_import_guide,
)


class TestExportMusicXml(unittest.TestCase):
    def test_basic_export(self):
        result = export_musicxml(["C", "Am", "F", "G"])
        self.assertNotIn("error", result)
        self.assertTrue(result["file_path"].endswith(".musicxml"))
        self.assertTrue(os.path.isfile(result["file_path"]))

    def test_with_key(self):
        result = export_musicxml(["Dm7", "G7", "Cmaj7"], key_str="C major")
        self.assertNotIn("error", result)

    def test_empty_chords(self):
        result = export_musicxml([])
        self.assertIn("error", result)


class TestExportTabText(unittest.TestCase):
    def test_basic_export(self):
        result = export_tab_text(["C", "Am", "G"])
        self.assertNotIn("error", result)
        self.assertTrue(result["file_path"].endswith(".txt"))
        self.assertTrue(os.path.isfile(result["file_path"]))
        self.assertEqual(len(result["chords_found"]), 3)

    def test_mixed_chords(self):
        result = export_tab_text(["C", "Bbm9"])
        self.assertNotIn("error", result)
        self.assertEqual(len(result["chords_missing"]), 1)

    def test_empty_chords(self):
        result = export_tab_text([])
        self.assertIn("error", result)


class TestGetDawImportGuide(unittest.TestCase):
    def test_known_daw(self):
        for daw in ["garageband", "logic", "ableton", "reaper", "fl_studio"]:
            result = get_daw_import_guide(daw)
            self.assertNotIn("error", result)
            self.assertIn("midi_instructions", result)
            self.assertIn("daw", result)

    def test_unknown_daw(self):
        result = get_daw_import_guide("cubase")
        self.assertIn("error", result)


class TestExportForDaw(unittest.TestCase):
    def test_basic_export(self):
        result = export_for_daw(["C", "Am", "F", "G"])
        self.assertIn("midi_path", result)
        self.assertIn("musicxml_path", result)
        self.assertTrue(os.path.isfile(result["midi_path"]))
        self.assertTrue(os.path.isfile(result["musicxml_path"]))

    def test_with_daw_guide(self):
        result = export_for_daw(["C", "G"], daw_name="ableton")
        self.assertIn("daw_guide", result)
        self.assertIn("Ableton", result["daw_guide"]["daw"])

    def test_empty_chords(self):
        result = export_for_daw([])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
