"""Tests for watcher → WebSocket wiring."""

import pytest

from server.services.watcher import WorkspaceWatcher


class TestWatcherInAppState:
    def test_app_has_watcher(self, app):
        assert hasattr(app.state, "watcher")
        assert isinstance(app.state.watcher, WorkspaceWatcher)


class TestWatcherCallbackBridge:
    """Verify that watcher events can be bridged to async broadcast."""

    def test_subscribe_receives_events(self):
        """Watcher subscribe + _build_event produces dict with expected keys."""
        from pathlib import Path

        watcher = WorkspaceWatcher(Path("/tmp/fake"))
        received = []
        watcher.subscribe("opp-001", lambda evt: received.append(evt))

        # Simulate what _watch does internally
        event = watcher._build_event(
            Path("/tmp/fake/opp-001"),
            Path("/tmp/fake/opp-001/contributions/data-round-1.json"),
        )
        for cb in watcher._subscribers.get("opp-001", []):
            cb(event)

        assert len(received) == 1
        assert received[0]["event"] == "file_changed"
        assert received[0]["type"] == "contribution"
        assert "data-round-1.json" in received[0]["path"]

    def test_unsubscribe_removes_callback(self):
        from pathlib import Path

        watcher = WorkspaceWatcher(Path("/tmp/fake"))
        received = []
        cb = lambda evt: received.append(evt)
        watcher.subscribe("opp-001", cb)
        watcher.unsubscribe("opp-001", cb)

        assert len(watcher._subscribers.get("opp-001", [])) == 0
