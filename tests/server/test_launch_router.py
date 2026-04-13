"""Tests for launch router — parallel Phase 2 and single-agent Phase 0."""

import json
from unittest.mock import patch, MagicMock

import pytest
from pydantic import BaseModel


class TestLaunchRouter:
    @pytest.mark.asyncio
    async def test_start_with_roster_uses_staggered(self, client, app):
        """POST /api/launch/{opp_id}/start uses launch_staggered when roster exists."""
        launcher = app.state.launcher
        with patch.object(launcher, "launch_staggered", return_value={"product": True, "data": True, "design": True, "engineering": True}) as mock_parallel:
            resp = await client.post("/api/launch/opp-20260405-120000/start")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "launched"
            assert data["mode"] == "parallel"
            assert "functions" in data
            mock_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_without_roster_uses_single(self, client, app, tmp_data_dir):
        """POST /api/launch/{opp_id}/start uses single launch when no roster."""
        # Create a workspace without roster
        ws_dir = tmp_data_dir / "workspaces" / "opp-noroster"
        ws_dir.mkdir(parents=True)
        (ws_dir / "contributions").mkdir()
        (ws_dir / "reviews").mkdir()
        (ws_dir / "artifacts").mkdir()
        opp = {
            "id": "opp-noroster",
            "type": "signal",
            "title": "No roster test",
            "description": "Testing without roster",
            "status": "confirmed",
            "roster": None,
            "created_at": "2026-04-12T00:00:00Z",
            "updated_at": "2026-04-12T00:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

        launcher = app.state.launcher
        with patch.object(launcher, "launch", return_value=True) as mock_single:
            resp = await client.post("/api/launch/opp-noroster/start")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "launched"
            assert data.get("mode") != "parallel"
            mock_single.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_parallel_returns_function_outputs(self, client, app):
        """GET /api/launch/{opp_id}/status includes function outputs for parallel runs."""
        launcher = app.state.launcher
        # Simulate parallel process state
        from collections import deque
        launcher._output["opp-20260405-120000:product"] = deque(["product line 1"])
        launcher._output["opp-20260405-120000:data"] = deque(["data line 1"])

        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        launcher._processes["opp-20260405-120000:product"] = mock_proc
        launcher._processes["opp-20260405-120000:data"] = mock_proc

        resp = await client.get("/api/launch/opp-20260405-120000/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "function_outputs" in data
        assert "product" in data["function_outputs"]
        assert "data" in data["function_outputs"]

    @pytest.mark.asyncio
    async def test_start_aligning_returns_400(self, client, app, tmp_data_dir):
        """POST /api/launch/{opp_id}/start returns 400 for aligning status."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-draft"
        ws_dir.mkdir(parents=True)
        (ws_dir / "contributions").mkdir()
        (ws_dir / "reviews").mkdir()
        (ws_dir / "artifacts").mkdir()
        opp = {
            "id": "opp-draft",
            "type": "signal",
            "title": "Draft test",
            "description": "Still drafting",
            "status": "aligning",
            "roster": None,
            "created_at": "2026-04-12T00:00:00Z",
            "updated_at": "2026-04-12T00:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))
        resp = await client.post("/api/launch/opp-draft/start")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_status_returns_latest_output_after_resume(self, client, app):
        """GET /api/launch/{id}/status returns only post-resume output, not old turns."""
        launcher = app.state.launcher
        from collections import deque
        # Simulate output with a resume separator
        launcher._output["opp-20260405-120000"] = deque([
            '{"type":"text","text":"turn 1 response"}',
            "--- RESUMED ---",
            '{"type":"text","text":"turn 2 response"}',
        ])
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0  # finished
        mock_proc.returncode = 0
        launcher._processes["opp-20260405-120000"] = mock_proc

        resp = await client.get("/api/launch/opp-20260405-120000/status")
        assert resp.status_code == 200
        data = resp.json()
        # Should only contain post-resume output
        assert len(data["output"]) == 1
        assert "turn 2" in data["output"][0]
        assert not any("turn 1" in line for line in data["output"])

    # --- /assemble endpoint ---

    @pytest.mark.asyncio
    async def test_assemble_launches_for_assembled_opportunity(self, client, app, tmp_data_dir):
        """POST /api/launch/{opp_id}/assemble launches for an assembled opportunity."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-open-assemble"
        ws_dir.mkdir(parents=True)
        for d in ("contributions", "reviews", "artifacts"):
            (ws_dir / d).mkdir()
        opp = {
            "id": "opp-open-assemble", "type": "hypothesis",
            "title": "Ready to assemble",
            "description": "Framed and ready",
            "context_refs": ["L1-global"],
            "assumptions": [{"id": "asm-001", "content": "test", "status": "untested", "importance": "critical"}],
            "success_signals": ["X"], "kill_signals": ["Y"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T16:00:00Z",
            "updated_at": "2026-04-12T16:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

        launcher = app.state.launcher
        with patch.object(launcher, "launch", return_value=True) as mock_launch:
            resp = await client.post("/api/launch/opp-open-assemble/assemble")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "launched"
            assert data["opp_id"] == "opp-open-assemble"
            mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_assemble_rejects_aligning_status(self, client, tmp_data_dir):
        """POST /api/launch/{opp_id}/assemble returns 400 for aligning status."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-draft-assemble"
        ws_dir.mkdir(parents=True)
        for d in ("contributions", "reviews", "artifacts"):
            (ws_dir / d).mkdir()
        opp = {
            "id": "opp-draft-assemble", "type": "hypothesis",
            "title": "Still drafting", "description": "Not ready",
            "status": "aligning", "roster": None,
            "created_at": "2026-04-12T16:00:00Z",
            "updated_at": "2026-04-12T16:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))
        resp = await client.post("/api/launch/opp-draft-assemble/assemble")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_assemble_rejects_opportunity_with_roster(self, client, tmp_data_dir):
        """POST /api/launch/{opp_id}/assemble returns 400 if roster already exists."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-rostered"
        ws_dir.mkdir(parents=True)
        for d in ("contributions", "reviews", "artifacts"):
            (ws_dir / d).mkdir()
        opp = {
            "id": "opp-rostered", "type": "hypothesis",
            "title": "Already has roster", "description": "Done",
            "status": "assembled",
            "roster": [{"function": "product", "rationale": "test", "investigation_tracks": [], "tool_access": []}],
            "created_at": "2026-04-12T16:00:00Z",
            "updated_at": "2026-04-12T16:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))
        resp = await client.post("/api/launch/opp-rostered/assemble")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_assemble_404_for_missing(self, client):
        """POST /api/launch/{opp_id}/assemble returns 404 for missing workspace."""
        resp = await client.post("/api/launch/opp-nonexistent/assemble")
        assert resp.status_code == 404

    # --- /dot-vote endpoint ---

    @pytest.mark.asyncio
    async def test_dot_vote_launches_parallel(self, client, app, tmp_data_dir):
        """POST /api/launch/{opp_id}/dot-vote launches parallel dot-vote agents."""
        # Create a synthesized workspace with roster
        ws_dir = tmp_data_dir / "workspaces" / "opp-dv-launch"
        ws_dir.mkdir(parents=True)
        for d in ("contributions", "reviews", "artifacts", "votes"):
            (ws_dir / d).mkdir()
        opp = {
            "id": "opp-dv-launch", "type": "hypothesis",
            "title": "Dot vote test", "description": "Testing",
            "context_refs": [], "assumptions": [],
            "success_signals": [], "kill_signals": [],
            "status": "converging",
            "roster": [
                {"function": "product", "rationale": "test", "investigation_tracks": [{"track": "t", "question": "What is it?", "expected_artifacts": []}], "tool_access": []},
                {"function": "data", "rationale": "test", "investigation_tracks": [{"track": "t", "question": "What is it?", "expected_artifacts": []}], "tool_access": []},
            ],
            "decision": None,
            "created_at": "2026-04-12T17:00:00Z",
            "updated_at": "2026-04-12T17:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))
        synthesis = {"id": "synth-test", "opportunity_id": "opp-dv-launch", "status": "presented",
                     "solutions": [{"id": "sol-001"}, {"id": "sol-002"}, {"id": "sol-003"}]}
        (ws_dir / "synthesis.json").write_text(json.dumps(synthesis))

        launcher = app.state.launcher
        with patch.object(launcher, "launch_staggered", return_value={"product": True, "data": True}) as mock_staggered:
            resp = await client.post("/api/launch/opp-dv-launch/dot-vote")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "launched"
            assert data["mode"] == "dot_vote"
            mock_staggered.assert_called_once()

    @pytest.mark.asyncio
    async def test_dot_vote_404_for_missing(self, client):
        """POST /api/launch/{opp_id}/dot-vote returns 404 for missing workspace."""
        resp = await client.post("/api/launch/opp-nonexistent/dot-vote")
        assert resp.status_code == 404

    # --- /decision-brief endpoint ---

    @pytest.mark.asyncio
    async def test_decision_brief_launches(self, client, app, tmp_data_dir):
        """POST /api/launch/{opp_id}/decision-brief launches single product agent."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-brief-launch"
        ws_dir.mkdir(parents=True)
        for d in ("contributions", "reviews", "artifacts", "votes"):
            (ws_dir / d).mkdir()
        opp = {
            "id": "opp-brief-launch", "type": "hypothesis",
            "title": "Brief test", "description": "Testing",
            "context_refs": [], "assumptions": [],
            "success_signals": [], "kill_signals": [],
            "status": "scoring",
            "roster": [
                {"function": "product", "rationale": "test", "investigation_tracks": [{"track": "t", "question": "What?", "expected_artifacts": []}], "tool_access": []},
            ],
            "decision": None,
            "created_at": "2026-04-12T17:00:00Z",
            "updated_at": "2026-04-12T17:00:00Z",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))
        synthesis = {"id": "synth-test", "opportunity_id": "opp-brief-launch", "status": "presented",
                     "solutions": [{"id": "sol-001"}, {"id": "sol-002"}, {"id": "sol-003"}]}
        (ws_dir / "synthesis.json").write_text(json.dumps(synthesis))

        launcher = app.state.launcher
        with patch.object(launcher, "launch", return_value=True) as mock_launch:
            resp = await client.post("/api/launch/opp-brief-launch/decision-brief")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "launched"
            mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_decision_brief_404_for_missing(self, client):
        """POST /api/launch/{opp_id}/decision-brief returns 404 for missing workspace."""
        resp = await client.post("/api/launch/opp-nonexistent/decision-brief")
        assert resp.status_code == 404

    # --- /processes endpoints ---

    @pytest.mark.asyncio
    async def test_list_processes_empty(self, client, app):
        """GET /api/launch/processes returns empty list when nothing tracked."""
        resp = await client.get("/api/launch/processes")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"processes": []}

    @pytest.mark.asyncio
    async def test_list_processes_returns_tracked(self, client, app):
        """GET /api/launch/processes returns tracked processes."""
        launcher = app.state.launcher
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.returncode = None
        launcher._processes["opp-001"] = mock_proc

        resp = await client.get("/api/launch/processes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["processes"]) == 1
        assert data["processes"][0]["key"] == "opp-001"
        assert data["processes"][0]["running"] is True

        # Clean up
        del launcher._processes["opp-001"]

    @pytest.mark.asyncio
    async def test_stop_by_key_simple(self, client, app):
        """POST /api/launch/processes/stop stops a process by key."""
        launcher = app.state.launcher
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        launcher._processes["opp-001"] = mock_proc

        resp = await client.post("/api/launch/processes/stop", json={"key": "opp-001"})
        assert resp.status_code == 200
        assert resp.json() == {"stopped": True}
        mock_proc.terminate.assert_called_once()

        # Clean up
        del launcher._processes["opp-001"]

    @pytest.mark.asyncio
    async def test_stop_by_key_compound(self, client, app):
        """POST /api/launch/processes/stop works with compound keys (colon)."""
        launcher = app.state.launcher
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        launcher._processes["opp-001:product"] = mock_proc

        resp = await client.post("/api/launch/processes/stop", json={"key": "opp-001:product"})
        assert resp.status_code == 200
        assert resp.json() == {"stopped": True}

        # Clean up
        del launcher._processes["opp-001:product"]

    @pytest.mark.asyncio
    async def test_stop_by_key_not_found(self, client, app):
        """POST /api/launch/processes/stop returns stopped=false for unknown key."""
        resp = await client.post("/api/launch/processes/stop", json={"key": "opp-nonexistent"})
        assert resp.status_code == 200
        assert resp.json() == {"stopped": False}
