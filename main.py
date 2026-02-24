# Woodshed AI — Application Entry Point
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

from app.ui.gradio_app import create_app, theme, CUSTOM_CSS


def main():
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=theme,
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()
