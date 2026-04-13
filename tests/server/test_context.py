"""Tests for context layer service and router."""

import pytest

from server.services.workspace import WorkspaceService


class TestContextService:
    def test_list_context_layers(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        layers = svc.list_context_layers()
        assert len(layers) == 4
        ids = {l["id"] for l in layers}
        assert ids == {"L1-global", "L2a-groceries", "L2a-gr", "L2b-ae"}

    def test_list_context_includes_file_name_and_sufficiency(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        layers = svc.list_context_layers()
        gr = next(l for l in layers if l["id"] == "L2a-gr")
        assert gr["file_name"] == "gr"
        assert gr["sufficiency"]["status"] == "gaps_identified"
        assert len(gr["sufficiency"]["gaps"]) == 1
        global_layer = next(l for l in layers if l["id"] == "L1-global")
        assert global_layer["file_name"] == "global"
        assert global_layer["sufficiency"]["status"] == "sufficient"

    def test_list_context_by_type(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        layers = svc.list_context_layers(layer_type="L2a")
        assert len(layers) == 2
        ids = {l["id"] for l in layers}
        assert "L2a-gr" in ids

    def test_get_gr_context_layer(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        ctx = svc.get_context_layer("L2a", "gr")
        assert ctx is not None
        assert ctx["id"] == "L2a-gr"
        assert ctx["type"] == "business_line"
        assert ctx["name"] == "grocery & retail"
        assert "product_overview" in ctx["content"]
        assert ctx["sufficiency"]["status"] == "gaps_identified"

    def test_get_context_layer(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        ctx = svc.get_context_layer("L1", "global")
        assert ctx["id"] == "L1-global"
        assert ctx["type"] == "global"

    def test_get_context_layer_not_found(self, tmp_data_dir):
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_context_layer("L1", "nonexistent") is None


@pytest.mark.asyncio
class TestContextRouter:
    async def test_list_all_context(self, client):
        resp = await client.get("/api/context")
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    async def test_list_context_by_type(self, client):
        resp = await client.get("/api/context/L2b")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "L2b-ae"

    async def test_get_context_layer(self, client):
        resp = await client.get("/api/context/L1/global")
        assert resp.status_code == 200
        assert resp.json()["type"] == "global"

    async def test_get_context_not_found(self, client):
        resp = await client.get("/api/context/L1/nonexistent")
        assert resp.status_code == 404
