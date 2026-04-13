"""Tests for evidence API router."""

import json

import pytest


def _make_evidence_workspace(tmp_data_dir, opp_id="opp-20260405-120000"):
    """Create evidence files in an existing workspace."""
    ws_dir = tmp_data_dir / "workspaces" / opp_id
    ev_dir = ws_dir / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)

    evidence = {
        "id": "ev-20260413-100000",
        "opportunity_id": opp_id,
        "source_type": "data-query",
        "query": "NPS scores for fresh food orders",
        "status": "completed",
        "findings": [
            {"metric": "NPS", "value": 34, "content": "Overall NPS is 34, trending up"}
        ],
        "summary": "NPS trending positive at 34 with strong repeat buyer signal.",
        "confidence": "high",
        "created_at": "2026-04-13T10:00:00Z",
        "completed_at": "2026-04-13T10:00:15Z",
    }
    (ev_dir / "ev-20260413-100000.json").write_text(json.dumps(evidence, indent=2))
    return ev_dir


@pytest.mark.asyncio
class TestEvidenceApproval:

    async def test_approve_evidence(self, client, tmp_data_dir):
        _make_evidence_workspace(tmp_data_dir)
        resp = await client.patch(
            "/api/evidence/opp-20260405-120000/ev-20260413-100000",
            json={"approval_status": "approved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_status"] == "approved"
        assert data["id"] == "ev-20260413-100000"

    async def test_reject_evidence(self, client, tmp_data_dir):
        _make_evidence_workspace(tmp_data_dir)
        resp = await client.patch(
            "/api/evidence/opp-20260405-120000/ev-20260413-100000",
            json={"approval_status": "rejected"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_status"] == "rejected"

    async def test_approval_persists_to_file(self, client, tmp_data_dir):
        ev_dir = _make_evidence_workspace(tmp_data_dir)
        await client.patch(
            "/api/evidence/opp-20260405-120000/ev-20260413-100000",
            json={"approval_status": "approved"},
        )
        saved = json.loads((ev_dir / "ev-20260413-100000.json").read_text())
        assert saved["approval_status"] == "approved"

    async def test_approve_not_found_workspace(self, client):
        resp = await client.patch(
            "/api/evidence/opp-nonexistent/ev-20260413-100000",
            json={"approval_status": "approved"},
        )
        assert resp.status_code == 404

    async def test_approve_not_found_evidence(self, client, tmp_data_dir):
        _make_evidence_workspace(tmp_data_dir)
        resp = await client.patch(
            "/api/evidence/opp-20260405-120000/ev-99999999-999999",
            json={"approval_status": "approved"},
        )
        assert resp.status_code == 404

    async def test_approve_invalid_status(self, client, tmp_data_dir):
        _make_evidence_workspace(tmp_data_dir)
        resp = await client.patch(
            "/api/evidence/opp-20260405-120000/ev-20260413-100000",
            json={"approval_status": "maybe"},
        )
        assert resp.status_code == 422
