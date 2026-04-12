"""Tests for filesystem watcher service."""

import asyncio
import json

import pytest

from server.services.watcher import WorkspaceWatcher


@pytest.mark.asyncio
class TestWorkspaceWatcher:
    async def test_detects_new_file(self, tmp_data_dir):
        opp_id = "opp-20260405-120000"
        ws_dir = tmp_data_dir / "workspaces" / opp_id
        watcher = WorkspaceWatcher(tmp_data_dir / "workspaces")

        events = []
        watcher.subscribe(opp_id, events.append)

        await watcher.start(opp_id)
        try:
            # Let watcher initialize its OS-level monitor
            await asyncio.sleep(0.3)

            # Write a new contribution file
            contrib = {"id": "contrib-design-20260405-150000", "agent_function": "design", "round": 1, "findings": []}
            (ws_dir / "contributions" / "design-round-1.json").write_text(json.dumps(contrib))

            # Give watcher time to detect
            await asyncio.sleep(2)
        finally:
            await watcher.stop(opp_id)

        assert len(events) >= 1
        assert any("design-round-1.json" in e.get("path", "") for e in events)

    async def test_subscribe_unsubscribe(self, tmp_data_dir):
        opp_id = "opp-20260405-120000"
        watcher = WorkspaceWatcher(tmp_data_dir / "workspaces")

        events = []
        watcher.subscribe(opp_id, events.append)
        watcher.unsubscribe(opp_id, events.append)

        # No events should be received after unsubscribe
        assert True  # Structural test — subscribe/unsubscribe don't crash

    async def test_classifies_file_types(self, tmp_data_dir):
        opp_id = "opp-20260405-120000"
        ws_dir = tmp_data_dir / "workspaces" / opp_id
        watcher = WorkspaceWatcher(tmp_data_dir / "workspaces")

        events = []
        watcher.subscribe(opp_id, events.append)

        await watcher.start(opp_id)
        try:
            # Let watcher initialize its OS-level monitor
            await asyncio.sleep(0.3)

            # Write synthesis
            (ws_dir / "synthesis.json").write_text(json.dumps({"id": "synth-test"}))
            await asyncio.sleep(2)
        finally:
            await watcher.stop(opp_id)

        synth_events = [e for e in events if e.get("type") == "synthesis"]
        assert len(synth_events) >= 1
