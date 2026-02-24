# Woodshed AI — Transcription Service Integration Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for the basic-pitch transcription service.

These tests require the service to be running at localhost:8765.
They are automatically skipped if the service is not available.
"""

import os
import unittest

import requests

import config


def _service_is_running() -> bool:
    try:
        r = requests.get(f"{config.TRANSCRIPTION_SERVICE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@unittest.skipUnless(
    _service_is_running(), "Transcription service not running"
)
class TestTranscriptionService(unittest.TestCase):
    """Integration tests that hit the live transcription service."""

    def test_health_check(self):
        """Health endpoint returns ok."""
        r = requests.get(f"{config.TRANSCRIPTION_SERVICE_URL}/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "basic-pitch")

    def test_no_file_returns_400(self):
        """POST without a file returns 400."""
        r = requests.post(f"{config.TRANSCRIPTION_SERVICE_URL}/transcribe")
        self.assertEqual(r.status_code, 400)

    def test_unsupported_format_returns_400(self):
        """POST with an unsupported format returns 400."""
        r = requests.post(
            f"{config.TRANSCRIPTION_SERVICE_URL}/transcribe",
            files={"file": ("test.txt", b"not audio", "text/plain")},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())


if __name__ == "__main__":
    unittest.main()
