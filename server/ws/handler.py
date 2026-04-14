"""WebSocket connection manager for live workspace updates."""

import asyncio
import logging
import time

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}
        self._heartbeat_task: asyncio.Task | None = None

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

    async def start_heartbeat(self, interval: float = 15.0):
        """Start background heartbeat that pings all connected clients."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop(interval))

    async def stop_heartbeat(self):
        """Cancel the heartbeat task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat_loop(self, interval: float):
        """Send ping to all clients at regular intervals."""
        try:
            while True:
                await self._ping_all()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def _ping_all(self):
        """Send ping event to every connected client, clean up dead ones."""
        ping = {"event": "ping", "ts": time.time()}
        for opp_id in list(self._connections):
            for ws in list(self._connections.get(opp_id, [])):
                try:
                    await ws.send_json(ping)
                except Exception:
                    self.disconnect(opp_id, ws)
