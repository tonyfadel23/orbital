"""WebSocket connection manager for live workspace updates."""

import json
import logging

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, opp_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(opp_id, []).append(ws)
        await ws.send_json({"event": "connected", "opp_id": opp_id})

    def disconnect(self, opp_id: str, ws: WebSocket):
        if opp_id in self._connections:
            try:
                self._connections[opp_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, opp_id: str, event: dict):
        for ws in list(self._connections.get(opp_id, [])):
            try:
                await ws.send_json(event)
            except Exception as exc:
                logger.warning("Broadcast failed for %s: %s", opp_id, exc)
                self.disconnect(opp_id, ws)
