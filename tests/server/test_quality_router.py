"""Tests for quality API router."""

import json
from datetime import datetime, timezone

import pytest


# --- Helpers ---

def _make_quality_workspace_for_router(tmp_data_dir, opp_id="opp-qr-test"):
    """Create a workspace with sufficient data for quality gate evaluation."""
    ws_dir = tmp_data_dir / "workspaces" / opp_id
    ws_dir.mkdir(parents=True, exist_ok=True)
    for d in ("contributions", "reviews", "artifacts", "votes", "evidence"):
        (ws_dir / d).mkdir(exist_ok=True)

    opp = {
        "id": opp_id,
        "type": "hypothesis",
        "title": "Quality router test",
        "description": "Testing quality router",
        "context_refs": [],
        "assumptions": [
            {"id": "asm-001", "content": "Test assumption", "status": "untested", "importance": "critical"},
        ],
        "success_signals": ["Metric improves"],
        "kill_signals": ["No change"],
        "status": "orbiting",
        "roster": [
            {"function": "product", "rationale": "test", "investigation_tracks": [], "tool_access": []},
            {"function": "data", "rationale": "test", "investigation_tracks": [], "tool_access": []},
        ],
        "decision": None,
        "created_at": "2026-04-05T12:00:00Z",
        "updated_at": "2026-04-05T14:00:00Z",
    }
    (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

    contrib = {
        "id": "contrib-1", "opportunity_id": opp_id,
        "agent_function": "data", "round": 1,
        "findings": [
            {"id": "f1", "type": "measurement", "content": "x", "confidence": 0.8,
             "source": "test", "assumptions_addressed": ["asm-001"], "direction": "supports"},
            {"id": "f2", "type": "measurement", "content": "y", "confidence": 0.7,
             "source": "test", "assumptions_addressed": [], "direction": "supports"},
            {"id": "f3", "type": "measurement", "content": "z", "confidence": 0.6,
             "source": "test", "assumptions_addressed": [], "direction": "supports"},
        ],
        "artifacts_produced": [], "cross_references": [],
        "self_review": {"self_checked": True, "self_check_notes": "ok"},
        "created_at": "2026-04-05T14:00:00Z",
    }
    (ws_dir / "contributions" / "data-round-1.json").write_text(json.dumps(contrib, indent=2))

    return ws_dir


@pytest.mark.asyncio
class TestQualityRouter:
    # --- GET /api/workspaces/{opp_id}/quality ---

    async def test_get_quality_full_report(self, client, tmp_data_dir):
        _make_quality_workspace_for_router(tmp_data_dir)
        resp = await client.get("/api/workspaces/opp-qr-test/quality")
        assert resp.status_code == 200
        data = resp.json()
        assert data["opp_id"] == "opp-qr-test"
        assert "layer_1" in data
        assert "overall_passed" in data["layer_1"]
        assert "gates" in data["layer_1"]
        assert data["layer_2"] is None
        assert data["layer_3"] is None

    async def test_get_quality_not_found(self, client):
        resp = await client.get("/api/workspaces/opp-nonexistent/quality")
        assert resp.status_code == 404

    # --- GET /api/workspaces/{opp_id}/quality/gates ---

    async def test_get_quality_gates_only(self, client, tmp_data_dir):
        _make_quality_workspace_for_router(tmp_data_dir)
        resp = await client.get("/api/workspaces/opp-qr-test/quality/gates")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_passed" in data
        assert "gates" in data
        assert isinstance(data["gates"], list)
        assert len(data["gates"]) == 6

    async def test_get_quality_gates_not_found(self, client):
        resp = await client.get("/api/workspaces/opp-nonexistent/quality/gates")
        assert resp.status_code == 404

    # --- POST /api/workspaces/{opp_id}/quality/evaluate ---

    async def test_evaluate_layer2_returns_report(self, client, tmp_data_dir):
        _make_quality_workspace_for_router(tmp_data_dir)
        resp = await client.post("/api/workspaces/opp-qr-test/quality/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["opp_id"] == "opp-qr-test"
        assert "overall_passed" in data
        assert "overall_score" in data

    # --- POST /api/workspaces/{opp_id}/quality/judge ---

    async def test_judge_layer3_launches(self, client, tmp_data_dir):
        _make_quality_workspace_for_router(tmp_data_dir)
        resp = await client.post("/api/workspaces/opp-qr-test/quality/judge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["launched"] is True

    async def test_judge_layer3_not_found(self, client):
        resp = await client.post("/api/workspaces/opp-nonexistent/quality/judge")
        assert resp.status_code == 404

    # --- GET /api/workspaces/{opp_id}/quality/judge ---

    async def test_judge_status(self, client, tmp_data_dir):
        _make_quality_workspace_for_router(tmp_data_dir)
        resp = await client.get("/api/workspaces/opp-qr-test/quality/judge")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert "results" in data

    async def test_judge_status_with_results(self, client, tmp_data_dir):
        ws_dir = _make_quality_workspace_for_router(tmp_data_dir)
        quality_dir = ws_dir / "quality"
        quality_dir.mkdir(exist_ok=True)
        results = {
            "opp_id": "opp-qr-test",
            "rubrics": {
                "contradictions_surfaced": {"score": 0.8, "rationale": "Good", "evidence_refs": []},
                "minority_viewpoints": {"score": 0.7, "rationale": "Ok", "evidence_refs": []},
                "evidence_based_recommendation": {"score": 0.9, "rationale": "Strong", "evidence_refs": []},
                "risk_weighting": {"score": 0.6, "rationale": "Decent", "evidence_refs": []},
                "solution_diversity": {"score": 0.5, "rationale": "Mixed", "evidence_refs": []},
            },
            "overall_score": 0.7,
            "overall_passed": True,
            "timestamp": "2026-04-12T10:00:00Z",
        }
        (quality_dir / "judge-evaluation.json").write_text(json.dumps(results, indent=2))
        resp = await client.get("/api/workspaces/opp-qr-test/quality/judge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is False
        assert data["results"]["overall_score"] == 0.7
        assert data["results"]["overall_passed"] is True

    # --- GET /api/quality/config ---

    async def test_get_quality_config(self, client):
        resp = await client.get("/api/quality/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert "blocking_mode" in data
        assert "layer_1" in data

    async def test_get_quality_config_has_all_default_gates(self, client):
        """Config returns all 6 Layer 1 gates with their settings."""
        resp = await client.get("/api/quality/config")
        assert resp.status_code == 200
        l1 = resp.json()["layer_1"]
        expected = {"assumption_coverage", "confidence_floor", "solution_distinctiveness",
                    "evidence_freshness", "vote_quorum", "finding_density"}
        assert set(l1.keys()) == expected

    # --- PATCH /api/quality/config ---

    async def test_patch_quality_config(self, client):
        resp = await client.patch("/api/quality/config", json={
            "blocking_mode": "block"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["blocking_mode"] == "block"

    async def test_patch_quality_config_gate_setting(self, client):
        resp = await client.patch("/api/quality/config", json={
            "layer_1": {
                "assumption_coverage": {"min_coverage": 0.8}
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["layer_1"]["assumption_coverage"]["min_coverage"] == 0.8

    async def test_patch_quality_config_layer2(self, client):
        resp = await client.patch("/api/quality/config", json={
            "layer_2": {"enabled": False}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["layer_2"]["enabled"] is False

    async def test_patch_quality_config_layer3(self, client):
        resp = await client.patch("/api/quality/config", json={
            "layer_3": {"enabled": False}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["layer_3"]["enabled"] is False

    # --- GET /api/workspaces/{opp_id}/quality/framing ---

    async def test_framing_quality_empty(self, client, tmp_data_dir):
        """Empty opportunity returns low framing score."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-frame-api"
        ws_dir.mkdir(parents=True)
        opp = {"id": "opp-frame-api", "title": "", "status": "aligning", "type": None,
               "description": "", "assumptions": [], "success_signals": [],
               "kill_signals": [], "context_refs": []}
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        resp = await client.get("/api/workspaces/opp-frame-api/quality/framing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["opp_id"] == "opp-frame-api"
        assert data["framing_score"] < 0.1
        assert data["ready"] is False
        assert "dimensions" in data
        assert len(data["dimensions"]) == 7

    async def test_framing_quality_complete(self, client, tmp_data_dir):
        """Fully framed opportunity returns high score and ready=True."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-frame-api2"
        ws_dir.mkdir(parents=True)
        opp = {
            "id": "opp-frame-api2", "status": "aligning",
            "title": "HMW make fresh groceries habitual on tMart?",
            "type": "hypothesis",
            "description": "Investigate whether recipe-based merchandising can shift grocery from transactional to habitual purchasing behavior among UAE users.",
            "assumptions": [
                {"id": "asm-001", "content": "Recipe content drives basket size", "status": "untested", "importance": "critical"},
                {"id": "asm-002", "content": "Users browse before buying", "status": "untested", "importance": "medium"},
                {"id": "asm-003", "content": "Fresh produce quality is top concern", "status": "untested", "importance": "high"},
            ],
            "success_signals": ["ATC +15%", "Repeat +20%", "Engagement >30s"],
            "kill_signals": ["No basket change", "Bounce >80%", "Support tickets up"],
            "context_refs": ["L1/global", "L2a/groceries"],
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        resp = await client.get("/api/workspaces/opp-frame-api2/quality/framing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["framing_score"] >= 0.8
        assert data["ready"] is True

    async def test_framing_quality_dimensions_have_numeric_scores(self, client, tmp_data_dir):
        """Each dimension must return a numeric score and details string for UI breakdowns."""
        ws_dir = tmp_data_dir / "workspaces" / "opp-frame-dims"
        ws_dir.mkdir(parents=True)
        opp = {
            "id": "opp-frame-dims", "status": "aligning",
            "title": "HMW reduce churn in UAE Pro subscribers?",
            "type": "hypothesis",
            "description": "Investigate churn patterns among UAE Pro users who cancel within 3 months.",
            "assumptions": [
                {"id": "asm-001", "content": "Price is main churn driver", "status": "untested", "importance": "critical"},
            ],
            "success_signals": ["Retention +10%"],
            "kill_signals": ["No change"],
            "context_refs": [],
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        resp = await client.get("/api/workspaces/opp-frame-dims/quality/framing")
        assert resp.status_code == 200
        data = resp.json()
        dims = data["dimensions"]
        expected_keys = {"hmw_title", "type_set", "assumptions", "success_signals",
                         "kill_signals", "context_refs", "description_depth"}
        assert set(dims.keys()) == expected_keys
        for key, dim in dims.items():
            assert isinstance(dim["score"], (int, float)), f"{key} score must be numeric"
            assert 0 <= dim["score"] <= 1.0, f"{key} score must be 0-1"
            assert isinstance(dim["passed"], bool), f"{key} passed must be bool"
            assert isinstance(dim["details"], str), f"{key} details must be string"
            assert len(dim["details"]) > 0, f"{key} details must not be empty"

    async def test_framing_quality_not_found(self, client):
        resp = await client.get("/api/workspaces/opp-nonexistent/quality/framing")
        assert resp.status_code == 404
