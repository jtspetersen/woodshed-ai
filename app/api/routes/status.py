# Woodshed AI — Status Endpoint
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Health and status endpoint for system components."""

from fastapi import APIRouter

import config
from app.llm.ollama_client import is_available, list_models
from app.audio.transcribe import is_transcription_available
from app.knowledge.vectorstore import VectorStore

router = APIRouter()


def _get_knowledge_stats() -> dict:
    """Get knowledge base stats, handling errors gracefully."""
    try:
        vs = VectorStore()
        return {"available": True, **vs.get_stats()}
    except Exception:
        return {"available": False, "total_chunks": 0}


@router.get("/status")
def get_status() -> dict:
    """Return system health for all components."""
    ollama_ok = is_available()
    models = list_models() if ollama_ok else []

    return {
        "ollama": {
            "available": ollama_ok,
            "models": models,
            "primary_model": config.LLM_MODEL,
            "fast_model": config.FAST_MODEL,
        },
        "knowledge_base": _get_knowledge_stats(),
        "transcription": {
            "available": is_transcription_available(),
        },
    }
