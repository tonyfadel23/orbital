"""Tests for quality gate integration in launch router — dot-vote and decision-brief blocking."""

import json
from unittest.mock import patch, MagicMock

import pytest


def _make_workspace_for_gate_test(tmp_data_dir, opp_id, status="converging",
                                   with_synthesis=True, with_contributions=True,
                                   with_votes=False, assumption_coverage=True,
                                   finding_density_ok=True):
    """Create workspace with configurable quality gate pass/fail scenarios."""
    ws_dir = tmp_data_dir / "workspaces" / opp_id
    ws_dir.mkdir(parents=True, exist_ok=True)
    for d in ("contributions", "reviews", "artifacts", "votes", "evidence"):
        (ws_dir / d).mkdir(exist_ok=True)

    assumptions = [
        {"id": "asm-001", "content": "Test assumption", "status": "untested", "importance": "critical"},
    ]

    roster = [
        {"function": "product", "rationale": "test", "investigation_tracks": [{"track": "t", "question": "q", "expected_artifacts": []}], "tool_access": []},
        {"function": "data", "rationale": "test", "investigation_tracks": [{"track": "t", "question": "q", "expected_artifacts": []}], "tool_access": []},
    ]

    opp = {
        "id": opp_id, "type": "hypothesis",
        "title": "Gate integration test", "description": "Testing",
        "context_refs": [], "assumptions": assumptions,
        "success_signals": [], "kill_signals": [],
        "status": status, "roster": roster, "decision": None,
        "created_at": "2026-04-12T17:00:00Z",
        "updated_at": "2026-04-12T17:00:00Z",
    }
    (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

    if with_contributions:
        findings = [
            {"id": "f1", "type": "m", "content": "x", "confidence": 0.8, "source": "s",
             "assumptions_addressed": ["asm-001"] if assumption_coverage else [], "direction": "supports"},
        ]
        if finding_density_ok:
            findings.extend([
                {"id": "f2", "type": "m", "content": "y", "confidence": 0.7, "source": "s",
                 "assumptions_addressed": [], "direction": "supports"},
                {"id": "f3", "type": "m", "content": "z", "confidence": 0.6, "source": "s",
                 "assumptions_addressed": [], "direction": "supports"},
            ])
        contrib = {
            "id": "contrib-1", "opportunity_id": opp_id,
            "agent_function": "data", "round": 1,
            "findings": findings,
            "artifacts_produced": [], "cross_references": [],
            "self_review": {"self_checked": True, "self_check_notes": "ok"},
            "created_at": "2026-04-05T14:00:00Z",
        }
        (ws_dir / "contributions" / "data-round-1.json").write_text(json.dumps(contrib, indent=2))

    if with_synthesis:
        synthesis = {
            "id": "synth-test", "opportunity_id": opp_id, "status": "presented",
            "solutions": [{"id": "sol-001", "evidence_refs": ["ev-1"]},
                          {"id": "sol-002", "evidence_refs": ["ev-2"]},
                          {"id": "sol-003", "evidence_refs": ["ev-3"]}],
        }
        (ws_dir / "synthesis.json").write_text(json.dumps(synthesis, indent=2))

    if with_votes:
        for fn in ["product", "data"]:
            vote = {"id": f"vote-{fn}-1", "voter_function": fn, "votes": []}
            (ws_dir / "votes" / f"{fn}-vote.json").write_text(json.dumps(vote, indent=2))

    return ws_dir


def _set_blocking_mode(tmp_data_dir, mode):
    """Update config.json blocking_mode."""
    config_path = tmp_data_dir / "config.json"
    config = json.loads(config_path.read_text())
    config["quality_gates"]["blocking_mode"] = mode
    config_path.write_text(json.dumps(config, indent=2))


@pytest.mark.asyncio
class TestDotVoteGateIntegration:

    async def test_dot_vote_blocked_when_gates_fail_block_mode(self, client, app, tmp_data_dir):
        """POST /dot-vote returns 422 when quality gates fail and blocking_mode=block."""
        _set_blocking_mode(tmp_data_dir, "block")
        # Reload quality service config
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        # No contributions → finding_density and confidence_floor will fail
        _make_workspace_for_gate_test(tmp_data_dir, "opp-dv-block",
                                      with_contributions=False, with_synthesis=True)

        resp = await client.post("/api/launch/opp-dv-block/dot-vote")
        assert resp.status_code == 422
        data = resp.json()
        assert "quality" in data["detail"].lower() or "gate" in data["detail"].lower()

    async def test_dot_vote_proceeds_with_warnings_warn_mode(self, client, app, tmp_data_dir):
        """POST /dot-vote proceeds with warnings when blocking_mode=warn."""
        _set_blocking_mode(tmp_data_dir, "warn")
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        # Create workspace where non-blocking gates fail but blocking ones pass
        _make_workspace_for_gate_test(tmp_data_dir, "opp-dv-warn",
                                      with_contributions=True, with_synthesis=True,
                                      assumption_coverage=True, finding_density_ok=True)

        launcher = app.state.launcher
        with patch.object(launcher, "launch_staggered", return_value={"product": True, "data": True}):
            resp = await client.post("/api/launch/opp-dv-warn/dot-vote")
            assert resp.status_code == 200
            data = resp.json()
            assert "warnings" in data

    async def test_dot_vote_skips_checks_off_mode(self, client, app, tmp_data_dir):
        """POST /dot-vote skips all quality checks when blocking_mode=off."""
        _set_blocking_mode(tmp_data_dir, "off")
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        _make_workspace_for_gate_test(tmp_data_dir, "opp-dv-off",
                                      with_contributions=False, with_synthesis=True)

        launcher = app.state.launcher
        with patch.object(launcher, "launch_staggered", return_value={"product": True, "data": True}):
            resp = await client.post("/api/launch/opp-dv-off/dot-vote")
            assert resp.status_code == 200


@pytest.mark.asyncio
class TestDecisionBriefGateIntegration:

    async def test_decision_brief_blocked_when_quorum_fails_block_mode(self, client, app, tmp_data_dir):
        """POST /decision-brief returns 422 when vote_quorum fails and blocking_mode=block."""
        _set_blocking_mode(tmp_data_dir, "block")
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        # No votes → quorum fails
        _make_workspace_for_gate_test(tmp_data_dir, "opp-db-block",
                                      status="scoring",
                                      with_contributions=False, with_synthesis=True,
                                      with_votes=False)

        resp = await client.post("/api/launch/opp-db-block/decision-brief")
        assert resp.status_code == 422
        data = resp.json()
        assert "quality" in data["detail"].lower() or "gate" in data["detail"].lower()

    async def test_decision_brief_proceeds_with_warnings_warn_mode(self, client, app, tmp_data_dir):
        """POST /decision-brief proceeds with warnings when blocking_mode=warn."""
        _set_blocking_mode(tmp_data_dir, "warn")
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        _make_workspace_for_gate_test(tmp_data_dir, "opp-db-warn",
                                      status="scoring",
                                      with_contributions=True, with_synthesis=True,
                                      with_votes=True, assumption_coverage=True,
                                      finding_density_ok=True)

        launcher = app.state.launcher
        with patch.object(launcher, "launch", return_value=True):
            resp = await client.post("/api/launch/opp-db-warn/decision-brief")
            assert resp.status_code == 200
            data = resp.json()
            assert "warnings" in data

    async def test_decision_brief_skips_checks_off_mode(self, client, app, tmp_data_dir):
        """POST /decision-brief skips quality checks when blocking_mode=off."""
        _set_blocking_mode(tmp_data_dir, "off")
        config = json.loads((tmp_data_dir / "config.json").read_text())
        app.state.quality_gate_svc._qg_config = config["quality_gates"]
        app.state.quality_gate_svc._l1 = config["quality_gates"]["layer_1"]

        _make_workspace_for_gate_test(tmp_data_dir, "opp-db-off",
                                      status="scoring",
                                      with_contributions=False, with_synthesis=True)

        launcher = app.state.launcher
        with patch.object(launcher, "launch", return_value=True):
            resp = await client.post("/api/launch/opp-db-off/decision-brief")
            assert resp.status_code == 200
