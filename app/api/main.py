# Woodshed AI — FastAPI Application
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from app.api import sessions
from app.api.routes import chat, files, status

SESSION_CLEANUP_INTERVAL = 300  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — periodic session cleanup."""
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(SESSION_CLEANUP_INTERVAL)
            sessions.cleanup_stale()

    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Woodshed AI",
        description="AI-powered songwriting companion API",
        version="0.4.0",
        lifespan=lifespan,
    )

    # Allow any localhost origin (ports are auto-detected by dev.py)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://localhost(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(status.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(files.router, prefix="/api")

    return app
