"""Tests for WebSocket handler."""

import asyncio
import json
import time

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from server.ws.handler import ConnectionManager


class TestWebSocketHandler:
    def test_websocket_connect(self, app):
        """Test that WebSocket connection is accepted."""
        client = TestClient(app)
        with client.websocket_connect("/ws/workspace/opp-20260405-120000") as ws:
            # Should receive a connected message
            data = ws.receive_json()
            assert data["event"] == "connected"
            assert data["opp_id"] == "opp-20260405-120000"


class TestHeartbeat:
    def test_ping_all_sends_to_connections(self):
        """_ping_all sends ping event to all connected clients."""
        manager = ConnectionManager()
        received = []

        class FakeWS:
            async def send_json(self, data):
                received.append(data)

        manager._connections["opp-1"] = [FakeWS(), FakeWS()]
        manager._connections["opp-2"] = [FakeWS()]

        asyncio.run(manager._ping_all())

        assert len(received) == 3
        assert all(r["event"] == "ping" for r in received)
        assert all("ts" in r for r in received)

    def test_heartbeat_cleans_dead_connections(self):
        """Dead connections should be removed during heartbeat ping."""
        manager = ConnectionManager()

        class FakeWS:
            def __init__(self, alive=True):
                self._alive = alive

            async def send_json(self, data):
                if not self._alive:
                    raise RuntimeError("Connection closed")

        live = FakeWS(alive=True)
        dead = FakeWS(alive=False)
        manager._connections["test-opp"] = [live, dead]

        loop = asyncio.new_event_loop()
        loop.run_until_complete(manager._ping_all())
        loop.close()

        assert live in manager._connections["test-opp"]
        assert dead not in manager._connections["test-opp"]

    def test_start_stop_heartbeat(self):
        """Heartbeat task can be started and stopped."""
        manager = ConnectionManager()

        async def _test():
            await manager.start_heartbeat(interval=0.05)
            assert manager._heartbeat_task is not None
            assert not manager._heartbeat_task.done()
            await manager.stop_heartbeat()
            assert manager._heartbeat_task.done()

        asyncio.run(_test())
