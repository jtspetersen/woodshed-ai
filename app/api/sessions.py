# Woodshed AI — Session Management
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""In-memory session store mapping client UUIDs to MusicConversation instances."""

import time
from dataclasses import dataclass, field

from app.llm.pipeline import MusicConversation

SESSION_MAX_AGE = 3600  # 1 hour


@dataclass
class SessionData:
    conversation: MusicConversation = field(default_factory=MusicConversation)
    last_midi_summary: str | None = None
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_access = time.time()


_sessions: dict[str, SessionData] = {}


def get_or_create(session_id: str) -> SessionData:
    """Get an existing session or create a new one."""
    if session_id not in _sessions:
        _sessions[session_id] = SessionData()
    session = _sessions[session_id]
    session.touch()
    return session


def remove(session_id: str) -> None:
    """Remove a session."""
    _sessions.pop(session_id, None)


def cleanup_stale(max_age: int = SESSION_MAX_AGE) -> int:
    """Remove sessions older than max_age seconds. Returns count removed."""
    now = time.time()
    stale = [
        sid for sid, data in _sessions.items()
        if now - data.last_access > max_age
    ]
    for sid in stale:
        del _sessions[sid]
    return len(stale)


def clear_all() -> None:
    """Remove all sessions (for testing)."""
    _sessions.clear()
