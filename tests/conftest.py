# Woodshed AI — Shared Test Fixtures
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared pytest fixtures and markers for the test suite."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import create_app
from app.api import sessions
from app.llm.ollama_client import is_available


requires_ollama = pytest.mark.skipif(
    not is_available(),
    reason="Ollama not running or no models available",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def session_id():
    """Generate a unique session ID for test isolation."""
    return f"test-{uuid.uuid4().hex[:12]}"


@pytest.fixture
async def app_client():
    """Async httpx client wired to the FastAPI app."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_integration_sessions():
    """Clean session store before/after integration tests."""
    sessions.clear_all()
    yield
    sessions.clear_all()
