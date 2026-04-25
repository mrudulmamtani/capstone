"""Live monitoring WebSocket.

Subscribers connect to ``/api/monitor/ws/{session_id}`` and receive a stream
of events (per-frame action scores + any raised alerts) as JSON messages.
Events are fanned-out through Redis pub/sub so multiple API replicas can
share a session.
"""
from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/monitor", tags=["monitor"])


def session_channel(session_id: str) -> str:
    return f"vision-sop:session:{session_id}"


@router.websocket("/ws/{session_id}")
async def monitor_ws(ws: WebSocket, session_id: str) -> None:
    await ws.accept()
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(session_channel(session_id))
        await ws.send_json({"kind": "hello", "session_id": session_id})

        async def forward():
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                except Exception:
                    payload = {"raw": message["data"]}
                await ws.send_json(payload)

        async def ping():
            while True:
                await asyncio.sleep(20)
                await ws.send_json({"kind": "ping"})

        await asyncio.gather(forward(), ping())
    except WebSocketDisconnect:
        log.info("monitor.ws.disconnected", session_id=session_id)
    except Exception as exc:  # pragma: no cover
        log.warning("monitor.ws.error", session_id=session_id, error=str(exc))
    finally:
        try:
            await pubsub.unsubscribe(session_channel(session_id))
        except Exception:
            pass
        await redis.aclose()


async def publish_event(session_id: str, payload: dict) -> None:
    """Utility for the worker to push an event onto the channel."""
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.publish(session_channel(session_id), json.dumps(payload, default=str))
    finally:
        await redis.aclose()
