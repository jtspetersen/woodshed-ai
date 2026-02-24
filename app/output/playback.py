# Woodshed AI — Browser MIDI Playback
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate MIDI playback markers for in-browser rendering.

Uses a fenced code block with language 'midi-player' containing a base64
data URI. JavaScript in the Gradio page detects these code blocks and
replaces them with <midi-player> web components (same pattern as ABC
notation rendering).
"""

import base64


def midi_player_markdown(midi_file_path: str) -> str:
    """Generate a markdown code block that JS will render as a MIDI player.

    The MIDI file is base64-encoded into a data URI inside a fenced code
    block tagged as 'midi-player'. The LAUNCH_JS MutationObserver in
    gradio_app.py detects these and creates <midi-player> elements.

    Args:
        midi_file_path: Path to the MIDI file on disk.

    Returns:
        Markdown string with a fenced code block containing the data URI.
    """
    with open(midi_file_path, "rb") as f:
        midi_bytes = f.read()

    b64 = base64.b64encode(midi_bytes).decode("ascii")
    data_uri = f"data:audio/midi;base64,{b64}"

    return f"\n```midi-player\n{data_uri}\n```\n"
