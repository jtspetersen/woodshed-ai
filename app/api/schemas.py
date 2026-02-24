# Woodshed AI — API Schemas
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    creativity: str = "Balanced"


class ChatHistoryResponse(BaseModel):
    messages: list[dict]


class FileUploadResponse(BaseModel):
    analysis: str | None = None
    midi_summary: str | None = None
    error: str | None = None


class StatusResponse(BaseModel):
    ollama: dict
    knowledge_base: dict
    transcription: dict
