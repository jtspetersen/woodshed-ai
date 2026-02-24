# Woodshed AI — API Dependencies
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""FastAPI dependency injection helpers."""

from fastapi import Header, HTTPException

from app.api import sessions
from app.api.sessions import SessionData


def get_session_id(x_session_id: str = Header(default=None)) -> str:
    """Extract and validate the X-Session-ID header."""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header required")
    return x_session_id


def get_session(x_session_id: str = Header(default=None)) -> SessionData:
    """Get or create the session for the given session ID."""
    session_id = get_session_id(x_session_id)
    return sessions.get_or_create(session_id)
