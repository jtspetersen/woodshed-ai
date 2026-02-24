# Woodshed AI — Application Entry Point
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

import atexit
import os
import subprocess
import sys

import config
from app.ui.gradio_app import create_app, theme, CUSTOM_CSS

_service_process = None


def _start_transcription_service():
    """Start the basic-pitch transcription microservice if available."""
    global _service_process
    service_dir = config.ROOT_DIR / "services" / "basic-pitch"
    venv_python = service_dir / "venv" / "Scripts" / "python.exe"
    app_script = service_dir / "app.py"

    if not venv_python.exists():
        print("Transcription service: venv not found, skipping")
        return
    if not app_script.exists():
        print("Transcription service: app.py not found, skipping")
        return

    print("Starting transcription service on port 8765...")
    _service_process = subprocess.Popen(
        [str(venv_python), str(app_script)],
        cwd=str(service_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    atexit.register(_stop_transcription_service)


def _stop_transcription_service():
    """Stop the transcription microservice on exit."""
    global _service_process
    if _service_process and _service_process.poll() is None:
        print("Stopping transcription service...")
        _service_process.terminate()
        try:
            _service_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _service_process.kill()
        _service_process = None


def main():
    _start_transcription_service()

    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=theme,
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()
