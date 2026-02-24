# Woodshed AI — Audio Tool Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for app.audio.tools — tool schemas and dispatch mapping."""

import unittest

from app.audio.tools import AUDIO_TOOLS, AUDIO_TOOL_FUNCTIONS


class TestAudioToolSchemas(unittest.TestCase):
    """Tests for audio tool schema definitions."""

    def test_schemas_are_list(self):
        """AUDIO_TOOLS is a non-empty list."""
        self.assertIsInstance(AUDIO_TOOLS, list)
        self.assertGreater(len(AUDIO_TOOLS), 0)

    def test_schema_structure(self):
        """Each tool schema has the expected Ollama tool-use structure."""
        for tool in AUDIO_TOOLS:
            self.assertEqual(tool["type"], "function")
            func = tool["function"]
            self.assertIn("name", func)
            self.assertIn("description", func)
            self.assertIn("parameters", func)
            params = func["parameters"]
            self.assertEqual(params["type"], "object")
            self.assertIn("properties", params)

    def test_analyze_uploaded_midi_schema(self):
        """analyze_uploaded_midi tool has a file_path parameter."""
        tool = next(
            t for t in AUDIO_TOOLS if t["function"]["name"] == "analyze_uploaded_midi"
        )
        params = tool["function"]["parameters"]
        self.assertIn("file_path", params["properties"])
        self.assertIn("file_path", params["required"])


class TestAudioToolDispatch(unittest.TestCase):
    """Tests for audio tool dispatch mapping."""

    def test_dispatch_mapping_exists(self):
        """AUDIO_TOOL_FUNCTIONS maps all tool names to callables."""
        for tool in AUDIO_TOOLS:
            name = tool["function"]["name"]
            self.assertIn(name, AUDIO_TOOL_FUNCTIONS, f"Missing dispatch for {name}")
            self.assertTrue(
                callable(AUDIO_TOOL_FUNCTIONS[name]),
                f"{name} is not callable",
            )

    def test_analyze_uploaded_midi_callable(self):
        """analyze_uploaded_midi function is callable and handles bad input."""
        func = AUDIO_TOOL_FUNCTIONS["analyze_uploaded_midi"]
        result = func("/nonexistent/test.mid")
        self.assertIn("error", result)

    def test_transcribe_audio_file_schema(self):
        """transcribe_audio_file tool has a file_path parameter."""
        tool = next(
            t for t in AUDIO_TOOLS if t["function"]["name"] == "transcribe_audio_file"
        )
        params = tool["function"]["parameters"]
        self.assertIn("file_path", params["properties"])
        self.assertIn("file_path", params["required"])

    def test_transcribe_audio_file_callable(self):
        """transcribe_audio_file function is callable and handles bad input."""
        func = AUDIO_TOOL_FUNCTIONS["transcribe_audio_file"]
        result = func("/nonexistent/test.wav")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
