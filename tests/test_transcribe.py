# Woodshed AI — Transcription Client Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for app.audio.transcribe — audio transcription client.

All tests use mocking so the basic-pitch microservice does not need to be running.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.audio.transcribe import (
    SUPPORTED_AUDIO_EXTENSIONS,
    is_transcription_available,
    transcribe_audio,
)


class TestIsTranscriptionAvailable(unittest.TestCase):
    """Tests for the is_transcription_available health check."""

    @patch("app.audio.transcribe.requests.get")
    def test_available_when_service_responds(self, mock_get):
        """Returns True when the health endpoint responds 200."""
        mock_get.return_value = MagicMock(status_code=200)
        self.assertTrue(is_transcription_available())

    @patch("app.audio.transcribe.requests.get")
    def test_unavailable_on_connection_error(self, mock_get):
        """Returns False when the service can't be reached."""
        mock_get.side_effect = ConnectionError()
        self.assertFalse(is_transcription_available())

    @patch("app.audio.transcribe.requests.get")
    def test_unavailable_on_bad_status(self, mock_get):
        """Returns False when the health endpoint returns non-200."""
        mock_get.return_value = MagicMock(status_code=500)
        self.assertFalse(is_transcription_available())

    @patch("app.audio.transcribe.requests.get")
    def test_unavailable_on_timeout(self, mock_get):
        """Returns False when the health check times out."""
        import requests as req
        mock_get.side_effect = req.Timeout()
        self.assertFalse(is_transcription_available())


class TestTranscribeAudio(unittest.TestCase):
    """Tests for the transcribe_audio client function."""

    def test_nonexistent_file(self):
        """Returns error for a file that doesn't exist."""
        result = transcribe_audio("/nonexistent/file.wav")
        self.assertIn("error", result)
        self.assertIn("not found", result["error"].lower())

    def test_unsupported_format(self):
        """Returns error for unsupported file formats."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            result = transcribe_audio(path)
            self.assertIn("error", result)
            self.assertIn("Unsupported", result["error"])
        finally:
            os.unlink(path)

    @patch("app.audio.transcribe.is_transcription_available", return_value=False)
    def test_service_unavailable(self, _mock_avail):
        """Returns error when the transcription service isn't running."""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            result = transcribe_audio(path)
            self.assertIn("error", result)
            self.assertIn("isn't running", result["error"])
        finally:
            os.unlink(path)

    @patch("app.audio.transcribe.is_transcription_available", return_value=True)
    @patch("app.audio.transcribe.requests.post")
    def test_successful_transcription(self, mock_post, _mock_avail):
        """Returns midi_path on successful transcription."""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.write(fd, b"fake audio data")
        os.close(fd)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"MThd\x00\x00\x00\x06"  # fake MIDI header bytes
        mock_post.return_value = mock_resp

        try:
            result = transcribe_audio(path)
            self.assertNotIn("error", result)
            self.assertIn("midi_path", result)
            self.assertIn("original_file", result)
            self.assertTrue(result["midi_path"].endswith("_transcribed.mid"))
            # Clean up the generated MIDI file
            if os.path.exists(result["midi_path"]):
                os.unlink(result["midi_path"])
        finally:
            os.unlink(path)

    @patch("app.audio.transcribe.is_transcription_available", return_value=True)
    @patch("app.audio.transcribe.requests.post")
    def test_service_error_response(self, mock_post, _mock_avail):
        """Returns error when the service returns a non-200 status."""
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"error": "Transcription failed: bad audio"}
        mock_post.return_value = mock_resp

        try:
            result = transcribe_audio(path)
            self.assertIn("error", result)
            self.assertIn("bad audio", result["error"])
        finally:
            os.unlink(path)

    @patch("app.audio.transcribe.is_transcription_available", return_value=True)
    @patch("app.audio.transcribe.requests.post")
    def test_timeout_error(self, mock_post, _mock_avail):
        """Returns error when the request times out."""
        import requests as req
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        mock_post.side_effect = req.Timeout()

        try:
            result = transcribe_audio(path)
            self.assertIn("error", result)
            self.assertIn("timed out", result["error"].lower())
        finally:
            os.unlink(path)

    def test_supported_extensions(self):
        """All expected audio formats are in the supported set."""
        for ext in [".wav", ".mp3", ".m4a", ".ogg", ".flac"]:
            self.assertIn(ext, SUPPORTED_AUDIO_EXTENSIONS)


if __name__ == "__main__":
    unittest.main()
