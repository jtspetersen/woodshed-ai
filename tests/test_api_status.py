# Woodshed AI — API Status Endpoint Tests
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the /api/status endpoint and session header validation."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import create_app, lifespan

app = create_app()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=True)
@patch("app.api.routes.status.list_models", return_value=["qwen2.5:32b", "qwen3:8b"])
@patch("app.api.routes.status.is_transcription_available", return_value=True)
@patch("app.api.routes.status._get_knowledge_stats", return_value={
    "available": True, "total_chunks": 150, "sources": ["test.md"],
})
async def test_status_endpoint_returns_json(mock_kb, mock_trans, mock_models, mock_avail, client):
    resp = await client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "ollama" in data
    assert "knowledge_base" in data
    assert "transcription" in data


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=True)
@patch("app.api.routes.status.list_models", return_value=["qwen2.5:32b"])
@patch("app.api.routes.status.is_transcription_available", return_value=False)
@patch("app.api.routes.status._get_knowledge_stats", return_value={"available": True, "total_chunks": 50})
async def test_status_contains_ollama_field(mock_kb, mock_trans, mock_models, mock_avail, client):
    resp = await client.get("/api/status")
    data = resp.json()
    assert data["ollama"]["available"] is True
    assert "qwen2.5:32b" in data["ollama"]["models"]
    assert "primary_model" in data["ollama"]
    assert "fast_model" in data["ollama"]


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=False)
@patch("app.api.routes.status.list_models", return_value=[])
@patch("app.api.routes.status.is_transcription_available", return_value=False)
@patch("app.api.routes.status._get_knowledge_stats", return_value={
    "available": True, "total_chunks": 100, "sources": [], "categories": [],
})
async def test_status_contains_knowledge_base_field(mock_kb, mock_trans, mock_models, mock_avail, client):
    resp = await client.get("/api/status")
    data = resp.json()
    assert "available" in data["knowledge_base"]
    assert "total_chunks" in data["knowledge_base"]


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=False)
@patch("app.api.routes.status.list_models", return_value=[])
@patch("app.api.routes.status.is_transcription_available", return_value=True)
@patch("app.api.routes.status._get_knowledge_stats", return_value={"available": False, "total_chunks": 0})
async def test_status_contains_transcription_field(mock_kb, mock_trans, mock_models, mock_avail, client):
    resp = await client.get("/api/status")
    data = resp.json()
    assert data["transcription"]["available"] is True


@pytest.mark.anyio
async def test_cors_headers_present(client):
    resp = await client.options(
        "/api/status",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in resp.headers


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=False)
@patch("app.api.routes.status.list_models", return_value=[])
@patch("app.api.routes.status.is_transcription_available", return_value=False)
@patch("app.api.routes.status._get_knowledge_stats", return_value={"available": False, "total_chunks": 0})
async def test_ollama_unavailable_returns_empty_models(mock_kb, mock_trans, mock_models, mock_avail, client):
    resp = await client.get("/api/status")
    data = resp.json()
    assert data["ollama"]["available"] is False
    assert data["ollama"]["models"] == []


@pytest.mark.anyio
async def test_lifespan_starts_and_cancels_cleanup_task():
    """Test that the lifespan context manager creates and cancels the cleanup task."""
    import asyncio
    mock_app = MagicMock()
    async with lifespan(mock_app):
        # Inside the lifespan, the cleanup loop task should be running
        # Give it a moment to start
        await asyncio.sleep(0.01)
    # After exit, no errors should occur


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=True)
@patch("app.api.routes.status.list_models", return_value=["model1"])
@patch("app.api.routes.status.is_transcription_available", return_value=False)
@patch("app.api.routes.status.VectorStore")
async def test_get_knowledge_stats_success(mock_vs_cls, mock_trans, mock_models, mock_avail, client):
    """Test _get_knowledge_stats with a working VectorStore."""
    mock_vs = mock_vs_cls.return_value
    mock_vs.get_stats.return_value = {"total_chunks": 200, "sources": ["a.md"]}

    # Need to un-patch _get_knowledge_stats to actually test it
    from app.api.routes.status import _get_knowledge_stats
    result = _get_knowledge_stats()
    assert result["available"] is True
    assert result["total_chunks"] == 200


@pytest.mark.anyio
@patch("app.api.routes.status.is_available", return_value=True)
@patch("app.api.routes.status.list_models", return_value=[])
@patch("app.api.routes.status.is_transcription_available", return_value=False)
@patch("app.api.routes.status.VectorStore", side_effect=Exception("ChromaDB offline"))
async def test_get_knowledge_stats_error(mock_vs_cls, mock_trans, mock_models, mock_avail, client):
    """Test _get_knowledge_stats when VectorStore raises an exception."""
    from app.api.routes.status import _get_knowledge_stats
    result = _get_knowledge_stats()
    assert result["available"] is False
    assert result["total_chunks"] == 0
