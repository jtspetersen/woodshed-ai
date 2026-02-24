# Woodshed AI — Export & DAW Integration
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Export chord progressions as MusicXML and provide DAW import guides."""

import os
from datetime import datetime

import config
from app.output.midi_gen import _build_stream_from_chords
from app.output.guitar_tab import generate_progression_tab

# DAW import instructions
DAW_GUIDES = {
    "garageband": {
        "daw": "GarageBand",
        "midi_instructions": (
            "Open GarageBand > File > Open > select the .mid file. "
            "GarageBand will create tracks for each MIDI channel."
        ),
        "musicxml_instructions": (
            "GarageBand does not directly import MusicXML. "
            "Use the MIDI file instead, or open the MusicXML in "
            "MuseScore and export as MIDI."
        ),
    },
    "logic": {
        "daw": "Logic Pro",
        "midi_instructions": (
            "File > Open or drag the .mid file into the Tracks area. "
            "Logic creates Software Instrument tracks automatically."
        ),
        "musicxml_instructions": (
            "File > Open > select the .musicxml file. "
            "Logic imports it as a notation score."
        ),
    },
    "ableton": {
        "daw": "Ableton Live",
        "midi_instructions": (
            "Drag the .mid file from your file browser into a MIDI track. "
            "Ableton creates clips for each MIDI channel."
        ),
        "musicxml_instructions": (
            "Ableton does not import MusicXML. Use the MIDI file."
        ),
    },
    "reaper": {
        "daw": "REAPER",
        "midi_instructions": (
            "Insert > Media File > select the .mid file, or drag and drop. "
            "REAPER creates tracks for each MIDI channel."
        ),
        "musicxml_instructions": (
            "REAPER does not natively import MusicXML. Use the MIDI file, "
            "or install the MusicXML import extension."
        ),
    },
    "fl_studio": {
        "daw": "FL Studio",
        "midi_instructions": (
            "File > Import > MIDI File, or drag the .mid file "
            "into the Channel Rack or Playlist."
        ),
        "musicxml_instructions": (
            "FL Studio does not import MusicXML. Use the MIDI file."
        ),
    },
}


def _get_export_path(prefix: str, extension: str) -> str:
    """Generate a unique export file path."""
    export_dir = config.LOCAL_DATA_DIR / "exports"
    os.makedirs(export_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(export_dir / f"{prefix}_{timestamp}{extension}")


def export_musicxml(
    chords: list[str],
    key_str: str | None = None,
    title: str = "Woodshed AI Export",
    tempo_bpm: int = 120,
) -> dict:
    """Export a chord progression as MusicXML.

    MusicXML can be imported into MuseScore, Finale, Sibelius,
    Dorico, Logic Pro, and other notation software.

    Returns:
        Dict with file_path or error.
    """
    if not chords:
        return {"error": "No chords provided."}

    try:
        s = _build_stream_from_chords(
            chords, key_str=key_str, tempo_bpm=tempo_bpm
        )
        xml_path = _get_export_path("export", ".musicxml")
        s.write("musicxml", fp=xml_path)
        return {
            "file_path": xml_path,
            "format": "MusicXML",
            "chords": chords,
        }
    except Exception as e:
        return {"error": f"MusicXML export failed: {e}"}


def export_tab_text(chords: list[str]) -> dict:
    """Export guitar tab as a plain text file.

    Returns:
        Dict with file_path or error.
    """
    if not chords:
        return {"error": "No chords provided."}

    result = generate_progression_tab(chords)
    if "error" in result:
        return result

    try:
        txt_path = _get_export_path("tab", ".txt")
        with open(txt_path, "w") as f:
            f.write(f"Guitar Tab: {' - '.join(chords)}\n")
            f.write("=" * 40 + "\n\n")
            f.write(result["tab"])
            if result.get("chords_missing"):
                f.write(f"\n\nMissing voicings: {', '.join(result['chords_missing'])}")
        return {
            "file_path": txt_path,
            "format": "Text",
            "chords_found": result["chords_found"],
            "chords_missing": result.get("chords_missing", []),
        }
    except Exception as e:
        return {"error": f"Tab export failed: {e}"}


def get_daw_import_guide(daw_name: str) -> dict:
    """Return instructions for importing MIDI/MusicXML into a specific DAW.

    Args:
        daw_name: "garageband", "logic", "ableton", "reaper", or "fl_studio"

    Returns:
        Dict with daw name, midi_instructions, musicxml_instructions.
    """
    guide = DAW_GUIDES.get(daw_name.lower().replace(" ", "_"))
    if not guide:
        supported = ", ".join(g["daw"] for g in DAW_GUIDES.values())
        return {
            "error": f"No guide for '{daw_name}'. Supported DAWs: {supported}",
        }
    return guide


def export_for_daw(
    chords: list[str],
    key_str: str | None = None,
    daw_name: str | None = None,
    tempo_bpm: int = 120,
) -> dict:
    """Export a chord progression as MIDI + MusicXML with DAW import instructions.

    Returns:
        Dict with midi_path, musicxml_path, and optionally daw_guide.
    """
    if not chords:
        return {"error": "No chords provided."}

    # Generate MIDI
    from app.output.midi_gen import generate_progression_midi
    midi_result = generate_progression_midi(
        chords, key_str=key_str, tempo_bpm=tempo_bpm
    )

    # Generate MusicXML
    xml_result = export_musicxml(
        chords, key_str=key_str, tempo_bpm=tempo_bpm
    )

    result = {"chords": chords}

    if "error" not in midi_result:
        result["midi_path"] = midi_result["file_path"]
    else:
        result["midi_error"] = midi_result["error"]

    if "error" not in xml_result:
        result["musicxml_path"] = xml_result["file_path"]
    else:
        result["musicxml_error"] = xml_result["error"]

    # Add DAW guide if requested
    if daw_name:
        guide = get_daw_import_guide(daw_name)
        if "error" not in guide:
            result["daw_guide"] = guide
        else:
            result["daw_guide_error"] = guide["error"]

    return result
