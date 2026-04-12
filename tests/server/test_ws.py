"""Tests for WebSocket handler."""

import json

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient


class TestWebSocketHandler:
    def test_websocket_connect(self, app):
        """Test that WebSocket connection is accepted."""
        client = TestClient(app)
        with client.websocket_connect("/ws/workspace/opp-20260405-120000") as ws:
            # Should receive a connected message
            data = ws.receive_json()
            assert data["event"] == "connected"
            assert data["opp_id"] == "opp-20260405-120000"
