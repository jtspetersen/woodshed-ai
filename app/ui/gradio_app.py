# Woodshed AI — Gradio UI
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Browser-based chat interface for Woodshed AI."""

import os
import shutil

import gradio as gr

import config
from app.audio.analyze import analyze_midi, get_midi_summary
from app.audio.transcribe import is_transcription_available, transcribe_audio
from app.llm.pipeline import MusicConversation
from app.llm.ollama_client import is_available, list_models
from app.knowledge.vectorstore import VectorStore

# -- Design System Theme (Vintage Analog Studio) --

amber = gr.themes.Color(
    name="amber",
    c50="#FFF8F0",
    c100="#FEECD2",
    c200="#FDD9A5",
    c300="#FCBF6A",
    c400="#F5A623",
    c500="#D4890A",
    c600="#A66A08",
    c700="#8A5506",
    c800="#6E4305",
    c900="#523204",
    c950="#3A2403",
)

bark = gr.themes.Color(
    name="bark",
    c50="#F7F4F1",
    c100="#EDE8E3",
    c200="#DDD5CE",
    c300="#C4B9AF",
    c400="#A89A8D",
    c500="#87776A",
    c600="#6B5B4B",
    c700="#524538",
    c800="#3D3229",
    c900="#2A211B",
    c950="#1A1310",
)

theme = gr.themes.Base(
    primary_hue=amber,
    secondary_hue=amber,
    neutral_hue=bark,
    font=[gr.themes.GoogleFont("Nunito Sans"), "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    body_background_fill="#1A1310",
    body_background_fill_dark="#1A1310",
    body_text_color="#EDE8E3",
    body_text_color_dark="#EDE8E3",
    block_background_fill="#2A211B",
    block_background_fill_dark="#2A211B",
    block_border_color="#3D3229",
    block_border_color_dark="#3D3229",
    block_label_text_color="#C4B9AF",
    block_label_text_color_dark="#C4B9AF",
    block_title_text_color="#FEECD2",
    block_title_text_color_dark="#FEECD2",
    input_background_fill="#3D3229",
    input_background_fill_dark="#3D3229",
    input_border_color="#524538",
    input_border_color_dark="#524538",
    input_placeholder_color="#87776A",
    input_placeholder_color_dark="#87776A",
    button_primary_background_fill="#F5A623",
    button_primary_background_fill_dark="#F5A623",
    button_primary_text_color="#1A1310",
    button_primary_text_color_dark="#1A1310",
    button_primary_background_fill_hover="#D4890A",
    button_primary_background_fill_hover_dark="#D4890A",
    button_secondary_background_fill="#3D3229",
    button_secondary_background_fill_dark="#3D3229",
    button_secondary_text_color="#EDE8E3",
    button_secondary_text_color_dark="#EDE8E3",
    border_color_primary="#524538",
    border_color_primary_dark="#524538",
    shadow_drop="none",
    shadow_drop_lg="none",
)

CUSTOM_CSS = """
.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
}

/* Header styling */
#header-row {
    background: linear-gradient(135deg, #2A211B 0%, #3D3229 100%);
    border: 1px solid #524538;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 8px;
}

#header-row h1 {
    color: #F5A623 !important;
    font-size: 1.6rem !important;
    margin: 0 !important;
}

#header-row p {
    color: #C4B9AF !important;
    font-size: 0.9rem !important;
    margin: 4px 0 0 0 !important;
}

/* Status bar */
#status-bar {
    background: #2A211B;
    border: 1px solid #3D3229;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 0.85rem;
    color: #87776A;
}

/* Chatbot styling */
.chatbot .message {
    border-radius: 12px !important;
    font-size: 0.95rem !important;
}

/* Hint box */
#hint-box {
    background: #2A211B;
    border: 1px solid #524538;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #A89A8D;
}

/* Accordion */
.accordion {
    border-color: #3D3229 !important;
}
"""


def _get_status_text() -> str:
    """Build the status bar text."""
    parts = []
    if is_available():
        models = list_models()
        parts.append(f"Ollama: connected ({len(models)} models)")
        parts.append(f"Model: {config.LLM_MODEL}")
    else:
        parts.append("Ollama: disconnected")

    try:
        store = VectorStore()
        stats = store.get_stats()
        parts.append(f"Knowledge base: {stats['total_chunks']} chunks")
    except Exception:
        parts.append("Knowledge base: not loaded")

    if is_transcription_available():
        parts.append("Transcription: available")
    else:
        parts.append("Transcription: offline")

    return " | ".join(parts)


# Global conversation instance (per-session state managed by Gradio)
_conversations: dict[str, MusicConversation] = {}


def _get_or_create_conversation(request: gr.Request | None = None) -> MusicConversation:
    """Get or create a conversation for the current session."""
    # Use a simple default key since Gradio manages state per-tab
    return MusicConversation()


CREATIVITY_MAP = {
    "More Precise": 0.3,
    "Balanced": 0.7,
    "More Creative": 1.1,
}


def _process_midi_upload(file_path: str) -> tuple[str, str | None]:
    """Copy an uploaded MIDI file to local storage and analyze it.

    Returns:
        Tuple of (analysis_text_for_chat, midi_summary_for_llm).
    """
    # Copy to local MIDI directory
    os.makedirs(str(config.LOCAL_MIDI_DIR), exist_ok=True)
    filename = os.path.basename(file_path)
    dest = str(config.LOCAL_MIDI_DIR / filename)
    shutil.copy2(file_path, dest)

    # Analyze
    analysis = analyze_midi(dest)
    if "error" in analysis:
        return f"**MIDI upload error:** {analysis['error']}", None

    summary = analysis.get("summary", "")
    return f"**MIDI Analysis:**\n```\n{summary}\n```\n\n", summary


AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".ogg", ".flac")
MIDI_EXTENSIONS = (".mid", ".midi")


def _process_audio_upload(file_path: str) -> tuple[str, str | None]:
    """Transcribe an uploaded audio file to MIDI, then analyze it.

    Returns:
        Tuple of (status_text_for_chat, midi_summary_for_llm).
    """
    if not is_transcription_available():
        return (
            "**Audio transcription is not available** — "
            "the transcription service isn't running. "
            "Start it and try again, or upload a MIDI file instead.",
            None,
        )

    result = transcribe_audio(file_path)
    if "error" in result:
        return f"**Transcription error:** {result['error']}", None

    midi_path = result["midi_path"]
    analysis = analyze_midi(midi_path)
    if "error" in analysis:
        return f"**MIDI analysis error:** {analysis['error']}", None

    summary = analysis.get("summary", "")
    original = result.get("original_file", "audio file")
    return (
        f"**Transcribed `{original}` to MIDI and analyzed:**\n```\n{summary}\n```\n\n",
        summary,
    )


def respond(message: dict, history: list[dict], creativity: str):
    """Chat response function for Gradio ChatInterface (multimodal)."""
    conv = MusicConversation()

    # Replay history into the conversation
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            # Extract text content from multimodal messages
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [
                    p["text"] for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = " ".join(text_parts)
            if isinstance(content, str) and content.strip():
                conv.messages.append({"role": msg["role"], "content": content})

    temperature = CREATIVITY_MAP.get(creativity, 0.7)

    # Extract text and files from multimodal input
    user_text = message.get("text", "") if isinstance(message, dict) else str(message)
    files = message.get("files", []) if isinstance(message, dict) else []

    # Process uploaded files (MIDI or audio)
    midi_summary = None
    midi_prefix = ""
    for file_path in files:
        lower = file_path.lower()
        if lower.endswith(MIDI_EXTENSIONS):
            prefix, summary = _process_midi_upload(file_path)
            midi_prefix += prefix
            if summary:
                midi_summary = summary
            break
        elif lower.endswith(AUDIO_EXTENSIONS):
            prefix, summary = _process_audio_upload(file_path)
            midi_prefix += prefix
            if summary:
                midi_summary = summary
            break

    # Build the user message
    if not user_text.strip() and midi_summary:
        user_text = "I uploaded a file. Can you analyze it and tell me about it?"

    # Stream the response
    partial = midi_prefix
    for token in conv.send_stream(
        user_text, temperature=temperature, midi_summary=midi_summary
    ):
        partial += token
        yield partial


def create_app() -> gr.Blocks:
    """Create and return the Gradio Blocks app."""

    with gr.Blocks(title="Woodshed AI") as app:

        # Header
        with gr.Row(elem_id="header-row"):
            gr.Markdown(
                "# Woodshed AI\n"
                "Your AI-powered songwriting companion — music theory, chord analysis, and creative suggestions."
            )

        # Status bar
        status = gr.Markdown(value=_get_status_text, elem_id="status-bar", every=30)

        # Chat interface
        chat = gr.ChatInterface(
            fn=respond,
            multimodal=True,
            chatbot=gr.Chatbot(
                height=500,
                show_label=False,
                elem_id="chatbot",
            ),
            textbox=gr.MultimodalTextbox(
                placeholder="Ask about chords, progressions, scales... or upload a MIDI or audio file",
                show_label=False,
                file_types=[".mid", ".midi", ".wav", ".mp3", ".m4a"],
            ),
            additional_inputs=[
                gr.Radio(
                    choices=["More Precise", "Balanced", "More Creative"],
                    value="Balanced",
                    label="Creativity",
                ),
            ],
            additional_inputs_accordion="Creativity",
            examples=[
                [{"text": "Analyze the chord Dm7 for me"}],
                [{"text": "What key is this progression in: Am, F, C, G?"}],
                [{"text": "Suggest a jazzy chord to follow Dm7 -> G7"}],
                [{"text": "I want something that sounds melancholy in E minor"}],
                [{"text": "How do I play a Cmaj7 on guitar?"}],
                [{"text": "What's a good substitution for a G7 chord?"}],
            ],
            title=None,
            description="Ask anything about chords, progressions, scales, or songwriting — "
            "Woodshed AI will analyze, explain, and suggest ideas grounded in music theory. "
            "You can upload a MIDI file for analysis, or an audio file (.wav, .mp3, .m4a) "
            "to transcribe to MIDI first. "
            "Here are some examples to get you started:",
        )

    return app
