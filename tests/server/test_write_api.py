"""Tests for write APIs — create and update workspaces."""

import json

import pytest


@pytest.mark.asyncio
class TestCreateWorkspace:
    async def test_create_workspace(self, client, tmp_data_dir):
        payload = {
            "type": "hypothesis",
            "title": "New test opportunity created via API",
            "description": "Testing the workspace creation API endpoint",
            "context_refs": ["L1-global"],
            "assumptions": [
                {"id": "asm-001", "content": "This assumption is testable", "status": "untested", "importance": "high"}
            ],
            "success_signals": ["Metric improves"],
            "kill_signals": ["No change after 4 weeks"]
        }
        resp = await client.post("/api/workspaces", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"].startswith("opp-")
        assert data["status"] == "aligning"
        # Verify file was created on disk
        opp_path = tmp_data_dir / "workspaces" / data["id"] / "opportunity.json"
        assert opp_path.exists()

    async def test_create_workspace_missing_title(self, client):
        payload = {"type": "hypothesis", "description": "No title provided here"}
        resp = await client.post("/api/workspaces", json=payload)
        assert resp.status_code == 422

    async def test_create_workspace_with_enabled_tools(self, client, tmp_data_dir):
        payload = {
            "type": "hypothesis",
            "title": "Workspace with enabled tools for connectors",
            "description": "Testing that enabled_tools persists",
            "enabled_tools": ["figma", "bigquery"],
        }
        resp = await client.post("/api/workspaces", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        # Verify enabled_tools persisted on disk
        opp_path = tmp_data_dir / "workspaces" / data["id"] / "opportunity.json"
        import json
        opp_on_disk = json.loads(opp_path.read_text())
        assert opp_on_disk["enabled_tools"] == ["figma", "bigquery"]

    async def test_create_workspace_without_enabled_tools(self, client, tmp_data_dir):
        payload = {
            "type": "hypothesis",
            "title": "Workspace without enabled tools field",
            "description": "Testing default empty list",
        }
        resp = await client.post("/api/workspaces", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        opp_path = tmp_data_dir / "workspaces" / data["id"] / "opportunity.json"
        import json
        opp_on_disk = json.loads(opp_path.read_text())
        assert opp_on_disk["enabled_tools"] == []

    async def test_create_workspace_creates_subdirs(self, client, tmp_data_dir):
        payload = {
            "type": "question",
            "title": "Should we build this feature now",
            "description": "Testing that subdirectories are created properly",
            "context_refs": [],
            "assumptions": [],
            "success_signals": ["Users adopt it"],
            "kill_signals": ["No interest"]
        }
        resp = await client.post("/api/workspaces", json=payload)
        data = resp.json()
        ws_dir = tmp_data_dir / "workspaces" / data["id"]
        assert (ws_dir / "contributions").is_dir()
        assert (ws_dir / "reviews").is_dir()
        assert (ws_dir / "artifacts").is_dir()


@pytest.mark.asyncio
class TestUpdateOpportunity:
    async def test_patch_title(self, client):
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={"title": "Updated opportunity title for testing"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated opportunity title for testing"

    async def test_patch_add_roster(self, client):
        roster = [
            {
                "function": "product",
                "rationale": "Product orchestrates the investigation",
                "investigation_tracks": [{"track": "framing", "question": "Is the opportunity well-framed?", "expected_artifacts": ["product.md"]}],
                "tool_access": ["google-drive"]
            }
        ]
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={"roster": roster}
        )
        assert resp.status_code == 200
        assert resp.json()["roster"] is not None
        assert len(resp.json()["roster"]) == 1

    async def test_patch_status(self, client):
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={"status": "assembled"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "assembled"

    async def test_patch_context_refs(self, client):
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={"context_refs": ["L1-global", "L2a-groceries", "L2b-ae"]}
        )
        assert resp.status_code == 200
        assert resp.json()["context_refs"] == ["L1-global", "L2a-groceries", "L2b-ae"]

    async def test_patch_assumptions(self, client):
        new_assumptions = [
            {"id": "asm-001", "content": "Users want savings visibility", "status": "untested", "importance": "critical"},
            {"id": "asm-002", "content": "Gamification drives engagement", "status": "untested", "importance": "high"},
        ]
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={"assumptions": new_assumptions}
        )
        assert resp.status_code == 200
        assert len(resp.json()["assumptions"]) == 2
        assert resp.json()["assumptions"][1]["content"] == "Gamification drives engagement"

    async def test_patch_signals(self, client):
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={
                "success_signals": ["NPS +10", "Conversion +5%"],
                "kill_signals": ["No measurable change"],
            }
        )
        assert resp.status_code == 200
        assert len(resp.json()["success_signals"]) == 2
        assert resp.json()["kill_signals"] == ["No measurable change"]

    async def test_patch_multiple_fields(self, client):
        """Editing multiple fields at once — the edit panel's save flow."""
        resp = await client.patch(
            "/api/workspaces/opp-20260405-120000/opportunity",
            json={
                "title": "Refined title after editing",
                "description": "Updated description with more detail",
                "type": "problem",
                "context_refs": ["L1-global"],
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Refined title after editing"
        assert data["description"] == "Updated description with more detail"
        assert data["type"] == "problem"
        assert data["context_refs"] == ["L1-global"]

    async def test_patch_not_found(self, client):
        resp = await client.patch(
            "/api/workspaces/opp-nonexistent/opportunity",
            json={"title": "Does not matter"}
        )
        assert resp.status_code == 404
