# Woodshed AI — Chat Endpoint
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later

"""SSE streaming chat endpoint wrapping MusicConversation.send_stream()."""

import asyncio
import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_session, get_session_id
from app.api.schemas import ChatRequest, ChatHistoryResponse
from app.api.sessions import SessionData
from app.api import sessions
from app.llm.pipeline import StreamToken, StreamStatus, StreamToolCall, StreamThinking

router = APIRouter()

CREATIVITY_MAP = {
    "More Precise": 0.3,
    "Balanced": 0.7,
    "More Creative": 1.1,
}


@router.post("/chat")
async def chat(
    request: ChatRequest,
    session: SessionData = Depends(get_session),
):
    """Stream a chat response as Server-Sent Events."""
    temperature = CREATIVITY_MAP.get(request.creativity, 0.7)
    conv = session.conversation
    midi_summary = session.last_midi_summary

    async def generate():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        sentinel = object()

        def _produce():
            """Run the blocking sync generator in a thread, push events to queue."""
            try:
                for event in conv.send_stream(
                    request.message,
                    temperature=temperature,
                    midi_summary=midi_summary,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
                loop.call_soon_threadsafe(queue.put_nowait, sentinel)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)

        future = loop.run_in_executor(None, _produce)

        try:
            while True:
                event = await queue.get()
                if event is sentinel:
                    break
                if isinstance(event, Exception):
                    yield {"event": "error", "data": json.dumps({"message": str(event)})}
                    return

                if isinstance(event, StreamToken):
                    yield {"event": "token", "data": json.dumps({"text": event.text})}
                elif isinstance(event, StreamStatus):
                    payload = {"step": event.step}
                    if event.detail:
                        payload["detail"] = event.detail
                    yield {"event": "status", "data": json.dumps(payload)}
                elif isinstance(event, StreamThinking):
                    yield {"event": "thinking", "data": json.dumps({"text": event.text})}
                elif isinstance(event, StreamToolCall):
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({
                            "name": event.name,
                            "arguments": event.arguments,
                            "result": event.result,
                        }, default=str),
                    }
        finally:
            await future

        if conv.generated_files:
            yield {
                "event": "files",
                "data": json.dumps({"files": conv.generated_files}),
            }

        yield {"event": "done", "data": "{}"}

    # Clear midi_summary after use so it doesn't bleed into future messages
    session.last_midi_summary = None

    return EventSourceResponse(generate())


@router.post("/chat/reset")
def chat_reset(session_id: str = Depends(get_session_id)):
    """Clear conversation history for a session."""
    session = sessions.get_or_create(session_id)
    session.conversation.reset()
    session.last_midi_summary = None
    return {"status": "ok"}


@router.get("/chat/history")
def chat_history(session: SessionData = Depends(get_session)) -> ChatHistoryResponse:
    """Return conversation history for a session."""
    return ChatHistoryResponse(messages=session.conversation.get_history())
