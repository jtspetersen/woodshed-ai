# Woodshed AI — Gradio UI
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Browser-based chat interface for Woodshed AI."""

import gradio as gr

import config
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

    return " | ".join(parts)


# Global conversation instance (per-session state managed by Gradio)
_conversations: dict[str, MusicConversation] = {}


def _get_or_create_conversation(request: gr.Request | None = None) -> MusicConversation:
    """Get or create a conversation for the current session."""
    # Use a simple default key since Gradio manages state per-tab
    return MusicConversation()


def respond(message: str, history: list[dict], temperature: float, category: str):
    """Chat response function for Gradio ChatInterface."""
    conv = MusicConversation()

    # Replay history into the conversation
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            conv.messages.append(msg)

    cat_filter = category if category != "All" else None

    # Stream the response
    partial = ""
    for token in conv.send_stream(message, temperature=temperature, category_filter=cat_filter):
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
            chatbot=gr.Chatbot(
                height=500,
                show_label=False,
                elem_id="chatbot",
            ),
            textbox=gr.Textbox(
                placeholder="Ask me about chords, progressions, scales, or songwriting...",
                show_label=False,
                max_lines=3,
            ),
            additional_inputs=[
                gr.Slider(
                    minimum=0.0,
                    maximum=1.5,
                    value=config.TEMPERATURE,
                    step=0.1,
                    label="Temperature",
                ),
                gr.Dropdown(
                    choices=["All", "harmony", "melody", "rhythm", "form", "genre", "instrumentation", "production"],
                    value="All",
                    label="Knowledge Category",
                ),
            ],
            additional_inputs_accordion=gr.Accordion(
                label="Settings", open=False
            ),
            examples=[
                ["Analyze the chord Dm7 for me"],
                ["What key is this progression in: Am, F, C, G?"],
                ["Suggest a jazzy chord to follow Dm7 -> G7"],
                ["I want something that sounds melancholy in E minor"],
                ["How do I play a Cmaj7 on guitar?"],
                ["What's a good substitution for a G7 chord?"],
            ],
            title=None,
            description=None,
        )

        # Hint box
        gr.Markdown(
            "**Try asking about:** chord analysis, progressions, scales for a mood, "
            "guitar voicings, chord substitutions, or what chord comes next.",
            elem_id="hint-box",
        )

    return app
