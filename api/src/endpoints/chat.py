"""
chat — WebSocket endpoint for streaming chat with the Astro-Agent.

The frontend connects to  ws://<host>/api/v1/chat/ws?language=English
and exchanges JSON messages matching the protocol documented in
ChatContext.tsx.
"""

from __future__ import annotations

import contextlib
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.agent.agent import rag_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time streaming chat.

    Query params:
        language: "English" | "Hindi" (default "English")

    Client → Server:
        { "content": "user message text" }

    Server → Client (in order):
        { "type": "thinking",  "content": "..." }
        { "type": "tool_call", "tool_name": "...", "tool_params": {...} }
        { "type": "chunk",     "content": "..." }          (repeated)
        { "type": "done",      "sources": [...] }
        { "type": "error",     "content": "..." }          (on failure)
    """
    await websocket.accept()

    language = websocket.query_params.get("language", "English")
    session_id = str(uuid.uuid4())

    logger.info("WS connected: session=%s  language=%s", session_id, language)

    try:
        while True:
            # ── Wait for the next user message ────────────────────
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Invalid JSON payload.",
                    }
                )
                continue

            content = (data.get("content") or "").strip()
            if not content:
                continue

            # ── Stream agent events back to the client ────────────
            try:
                async for event in rag_agent.stream_events(
                    message=content,
                    session_id=session_id,
                    language=language,
                ):
                    await websocket.send_json(event)

            except Exception:
                logger.exception("Agent error (session=%s)", session_id)
                with contextlib.suppress(Exception):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "content": "Something went wrong while generating your reading. Please try again.",
                        }
                    )

    except WebSocketDisconnect:
        logger.info("WS disconnected: session=%s", session_id)
    except Exception:
        logger.exception("WS unexpected error (session=%s)", session_id)
