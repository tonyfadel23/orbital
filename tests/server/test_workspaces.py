"""Tests for workspace service and router — read operations."""

import json
import logging
from pathlib import Path

import pytest

from server.services.workspace import WorkspaceService


# --- Service layer tests ---

class TestWorkspaceService:
    def test_list_workspaces(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        workspaces = svc.list_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0]["id"] == "opp-20260405-120000"
        assert workspaces[0]["status"] == "orbiting"
        assert "title" in workspaces[0]

    def test_list_workspaces_empty(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "workspaces").mkdir()
        svc = WorkspaceService(data_dir)
        assert svc.list_workspaces() == []

    def test_get_opportunity(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        opp = svc.get_opportunity("opp-20260405-120000")
        assert opp["id"] == "opp-20260405-120000"
        assert opp["type"] == "hypothesis"

    def test_get_opportunity_not_found(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_opportunity("opp-nonexistent") is None

    def test_list_contributions(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        contribs = svc.list_contributions("opp-20260405-120000")
        assert len(contribs) == 1
        assert contribs[0]["filename"] == "data-round-1.json"

    def test_list_contributions_empty_workspace(self, tmp_data_dir):
        # Create empty workspace
        ws = tmp_data_dir / "workspaces" / "opp-20260410-100000"
        ws.mkdir()
        (ws / "contributions").mkdir()
        (ws / "opportunity.json").write_text(json.dumps({
            "id": "opp-20260410-100000", "type": "question",
            "title": "Empty workspace test opportunity",
            "description": "No contributions yet in this test workspace",
            "context_refs": [], "assumptions": [],
            "success_signals": ["Something"], "kill_signals": ["Nothing"],
            "status": "assembled", "decision": None,
            "created_at": "2026-04-10T10:00:00Z", "updated_at": "2026-04-10T10:00:00Z"
        }))
        svc = WorkspaceService(tmp_data_dir)
        assert svc.list_contributions("opp-20260410-100000") == []

    def test_get_contribution(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        contrib = svc.get_file("opp-20260405-120000", "contributions", "data-round-1.json")
        assert contrib["agent_function"] == "data"

    def test_list_artifacts(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        artifacts = svc.list_artifacts("opp-20260405-120000")
        assert len(artifacts) == 1
        assert artifacts[0]["filename"] == "data.md"

    def test_get_artifact_markdown(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        content = svc.get_artifact("opp-20260405-120000", "data.md")
        assert "Baselines" in content

    def test_get_workspace_state(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        state = svc.get_workspace_state("opp-20260405-120000")
        assert state["opportunity"]["id"] == "opp-20260405-120000"
        assert len(state["contributions"]) == 1
        assert len(state["artifacts"]) == 1
        assert state["synthesis"] is None

    def test_list_evidence(self, tmp_data_dir):
        # Create evidence directory and file
        ev_dir = tmp_data_dir / "workspaces" / "opp-20260405-120000" / "evidence"
        ev_dir.mkdir(exist_ok=True)
        (ev_dir / "ev-20260406-100000.json").write_text(json.dumps({
            "id": "ev-20260406-100000",
            "source_type": "data-query",
            "query": "NPS scores for tmart",
            "status": "completed",
            "findings": [{"finding": "NPS dropped 12 points", "confidence": 0.8, "source": "BigQuery"}],
            "summary": "NPS declining for tmart users",
            "confidence": 0.8,
            "created_at": "2026-04-06T10:00:00Z",
        }))
        svc = WorkspaceService(tmp_data_dir)
        evidence = svc.list_evidence("opp-20260405-120000")
        assert len(evidence) == 1
        assert evidence[0]["source_type"] == "data-query"

    def test_list_evidence_empty(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        evidence = svc.list_evidence("opp-20260405-120000")
        assert evidence == []

    def test_workspace_state_includes_evidence(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        state = svc.get_workspace_state("opp-20260405-120000")
        assert "evidence" in state

    def test_delete_workspace(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        result = svc.delete_workspace("opp-20260405-120000")
        assert result is True
        assert svc.get_opportunity("opp-20260405-120000") is None
        assert not (tmp_data_dir / "workspaces" / "opp-20260405-120000").exists()

    def test_delete_workspace_not_found(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        result = svc.delete_workspace("opp-nonexistent")
        assert result is False


# --- Router tests ---

@pytest.mark.asyncio
class TestWorkspacesRouter:
    async def test_list_workspaces(self, client):
        resp = await client.get("/api/workspaces")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "opp-20260405-120000"

    async def test_get_workspace(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["opportunity"]["id"] == "opp-20260405-120000"

    async def test_get_workspace_not_found(self, client):
        resp = await client.get("/api/workspaces/opp-nonexistent")
        assert resp.status_code == 404

    async def test_get_opportunity(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/opportunity")
        assert resp.status_code == 200
        assert resp.json()["type"] == "hypothesis"

    async def test_list_contributions(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/contributions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_contribution(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/contributions/data-round-1.json")
        assert resp.status_code == 200
        assert resp.json()["agent_function"] == "data"

    async def test_list_artifacts(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/artifacts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_artifact(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/artifacts/data.md")
        assert resp.status_code == 200
        assert "Baselines" in resp.text

    async def test_get_synthesis_not_found(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/synthesis")
        assert resp.status_code == 404

    async def test_delete_workspace(self, client):
        resp = await client.delete("/api/workspaces/opp-20260405-120000")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == "opp-20260405-120000"
        # Verify it's gone
        resp2 = await client.get("/api/workspaces/opp-20260405-120000")
        assert resp2.status_code == 404

    async def test_delete_workspace_not_found(self, client):
        resp = await client.delete("/api/workspaces/opp-nonexistent")
        assert resp.status_code == 404


# --- Corrupted data resilience tests ---

class TestWorkspaceServiceCorruptedData:
    def test_get_opportunity_corrupted_json(self, tmp_data_dir):
        """get_opportunity() returns None (not crash) when opportunity.json is invalid JSON."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-corrupted-001"
        ws_dir.mkdir(parents=True)
        (ws_dir / "opportunity.json").write_text("{bad json,,}")

        svc = WorkspaceService(tmp_data_dir)
        result = svc.get_opportunity("opp-corrupted-001")
        assert result is None

    def test_list_workspaces_skips_corrupted(self, tmp_data_dir):
        """list_workspaces() skips workspaces with corrupted opportunity.json."""
        # tmp_data_dir already has one valid workspace (opp-20260405-120000)
        # Add a corrupted second workspace
        ws_dir = tmp_data_dir / "workspaces" / "opp-corrupted-002"
        ws_dir.mkdir(parents=True)
        (ws_dir / "opportunity.json").write_text("NOT VALID JSON AT ALL")

        svc = WorkspaceService(tmp_data_dir)
        workspaces = svc.list_workspaces()
        # Should still return the valid workspace, skipping the corrupted one
        assert len(workspaces) == 1
        assert workspaces[0]["id"] == "opp-20260405-120000"

    def test_list_context_layers_skips_corrupted(self, tmp_data_dir):
        """list_context_layers() skips files with corrupted JSON."""
        # Write a corrupted context layer file
        layer_dir = tmp_data_dir / "context" / "L1"
        (layer_dir / "corrupted.json").write_text("{nope")

        svc = WorkspaceService(tmp_data_dir)
        layers = svc.list_context_layers("L1")
        # Should return the valid 'global' layer only, skipping corrupted
        valid_ids = [layer["id"] for layer in layers]
        assert "L1-global" in valid_ids
        assert not any("corrupted" in lid for lid in valid_ids)

    def test_get_opportunity_corrupted_logs_warning(self, tmp_data_dir, caplog):
        """get_opportunity() logs a warning when JSON is corrupted."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-corrupted-log"
        ws_dir.mkdir(parents=True)
        (ws_dir / "opportunity.json").write_text("{bad}")

        svc = WorkspaceService(tmp_data_dir)
        with caplog.at_level(logging.WARNING, logger="server.services.workspace"):
            svc.get_opportunity("opp-corrupted-log")
        assert any("opp-corrupted-log" in msg for msg in caplog.messages)


class TestAssumptionNormalization:
    """get_opportunity() should normalize assumptions into {id, content, status, importance} objects."""

    def _make_opp(self, tmp_data_dir, opp_id, assumptions):
        ws_dir = tmp_data_dir / "workspaces" / opp_id
        ws_dir.mkdir(parents=True)
        opp = {"id": opp_id, "title": "Test", "status": "aligning",
               "type": "hypothesis", "assumptions": assumptions}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        return WorkspaceService(tmp_data_dir)

    def test_string_assumptions_normalized(self, tmp_data_dir):
        """Plain string assumptions get wrapped into structured objects."""
        svc = self._make_opp(tmp_data_dir, "opp-str-asm", [
            "Users want savings visibility",
            "Gamification drives engagement",
        ])
        opp = svc.get_opportunity("opp-str-asm")
        assert len(opp["assumptions"]) == 2
        a = opp["assumptions"][0]
        assert a["content"] == "Users want savings visibility"
        assert a["status"] == "untested"
        assert a["importance"] == "medium"
        assert a["id"] == "asm-001"

    def test_structured_assumptions_unchanged(self, tmp_data_dir):
        """Proper {id, content, status, importance} objects pass through unchanged."""
        svc = self._make_opp(tmp_data_dir, "opp-obj-asm", [
            {"id": "asm-X", "content": "Already structured", "status": "validated", "importance": "critical"},
        ])
        opp = svc.get_opportunity("opp-obj-asm")
        a = opp["assumptions"][0]
        assert a["content"] == "Already structured"
        assert a["status"] == "validated"
        assert a["importance"] == "critical"
        assert a["id"] == "asm-X"

    def test_corrupted_spread_assumptions_recovered(self, tmp_data_dir):
        """Spread-operator-corrupted objects ({0:'T', 1:'h', ...}) get recovered."""
        corrupted = {str(i): c for i, c in enumerate("Test assumption")}
        svc = self._make_opp(tmp_data_dir, "opp-spread-asm", [corrupted])
        opp = svc.get_opportunity("opp-spread-asm")
        a = opp["assumptions"][0]
        assert a["content"] == "Test assumption"
        assert a["status"] == "untested"
        assert a["id"] == "asm-001"

    def test_no_assumptions_key(self, tmp_data_dir):
        """Missing assumptions key is fine — no normalization needed."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-no-asm"
        ws_dir.mkdir(parents=True)
        opp = {"id": "opp-no-asm", "title": "Test", "status": "aligning", "type": "hypothesis"}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        svc = WorkspaceService(tmp_data_dir)
        result = svc.get_opportunity("opp-no-asm")
        assert "assumptions" not in result or result.get("assumptions") is None


class TestVotesAndDecisionBrief:
    """WorkspaceService.get_votes() and get_decision_brief() tests."""

    def _make_workspace_with_votes(self, tmp_data_dir, opp_id="opp-votes-test"):
        ws_dir = tmp_data_dir / "workspaces" / opp_id
        ws_dir.mkdir(parents=True)
        (ws_dir / "votes").mkdir()
        (ws_dir / "artifacts").mkdir()
        (ws_dir / "opportunity.json").write_text(json.dumps({
            "id": opp_id, "title": "Test", "status": "scoring", "type": "hypothesis",
        }))
        return ws_dir

    def test_get_votes_returns_list(self, tmp_data_dir):
        ws_dir = self._make_workspace_with_votes(tmp_data_dir)
        vote = {"id": "vote-data-20260412-170000", "voter_function": "data", "votes": []}
        (ws_dir / "votes" / "data-vote.json").write_text(json.dumps(vote))
        svc = WorkspaceService(tmp_data_dir)
        votes = svc.get_votes("opp-votes-test")
        assert len(votes) == 1
        assert votes[0]["voter_function"] == "data"

    def test_get_votes_empty(self, tmp_data_dir):
        self._make_workspace_with_votes(tmp_data_dir, "opp-empty-votes")
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_votes("opp-empty-votes") == []

    def test_get_votes_multiple(self, tmp_data_dir):
        ws_dir = self._make_workspace_with_votes(tmp_data_dir, "opp-multi-votes")
        for fn in ("data", "engineering", "design"):
            vote = {"id": f"vote-{fn}-20260412-170000", "voter_function": fn}
            (ws_dir / "votes" / f"{fn}-vote.json").write_text(json.dumps(vote))
        svc = WorkspaceService(tmp_data_dir)
        votes = svc.get_votes("opp-multi-votes")
        assert len(votes) == 3

    def test_get_votes_no_workspace(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_votes("opp-nonexistent") == []

    def test_get_decision_brief_returns_content(self, tmp_data_dir):
        ws_dir = self._make_workspace_with_votes(tmp_data_dir, "opp-brief-test")
        (ws_dir / "artifacts" / "decision-brief.md").write_text("# Decision Brief\nTest content")
        svc = WorkspaceService(tmp_data_dir)
        brief = svc.get_decision_brief("opp-brief-test")
        assert "Decision Brief" in brief

    def test_get_decision_brief_not_found(self, tmp_data_dir):
        self._make_workspace_with_votes(tmp_data_dir, "opp-no-brief")
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_decision_brief("opp-no-brief") is None

    def test_get_decision_brief_no_workspace(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_decision_brief("opp-nonexistent") is None


class TestSignalPreservation:
    """get_opportunity() should preserve success_signals and kill_signals arrays as-is."""

    def test_success_signals_preserved(self, tmp_data_dir):
        ws_dir = tmp_data_dir / "workspaces" / "opp-signals"
        ws_dir.mkdir(parents=True)
        signals = ["Metric A improves", "Metric B increases"]
        opp = {"id": "opp-signals", "title": "Test", "status": "assembled",
               "type": "hypothesis", "success_signals": signals}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        svc = WorkspaceService(tmp_data_dir)
        result = svc.get_opportunity("opp-signals")
        assert result["success_signals"] == signals

    def test_kill_signals_preserved(self, tmp_data_dir):
        ws_dir = tmp_data_dir / "workspaces" / "opp-kill"
        ws_dir.mkdir(parents=True)
        signals = ["Cannibalization detected", "Negative feedback"]
        opp = {"id": "opp-kill", "title": "Test", "status": "assembled",
               "type": "hypothesis", "kill_signals": signals}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        svc = WorkspaceService(tmp_data_dir)
        result = svc.get_opportunity("opp-kill")
        assert result["kill_signals"] == signals

    def test_empty_signals_preserved(self, tmp_data_dir):
        ws_dir = tmp_data_dir / "workspaces" / "opp-empty-sig"
        ws_dir.mkdir(parents=True)
        opp = {"id": "opp-empty-sig", "title": "Test", "status": "aligning",
               "type": "hypothesis", "success_signals": [], "kill_signals": []}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        svc = WorkspaceService(tmp_data_dir)
        result = svc.get_opportunity("opp-empty-sig")
        assert result["success_signals"] == []
        assert result["kill_signals"] == []
