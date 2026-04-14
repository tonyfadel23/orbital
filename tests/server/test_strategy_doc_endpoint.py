"""Tests for the strategy-doc endpoint."""

import pytest


@pytest.mark.asyncio
class TestStrategyDocEndpoint:

    async def test_strategy_doc_returns_html(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/strategy-doc")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert resp.text.startswith("<!DOCTYPE html>")

    async def test_strategy_doc_has_content_disposition(self, client):
        resp = await client.get("/api/workspaces/opp-20260405-120000/strategy-doc")
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "strategy-opp-20260405-120000.html" in cd

    async def test_strategy_doc_404_for_missing_workspace(self, client):
        resp = await client.get("/api/workspaces/nonexistent/strategy-doc")
        assert resp.status_code == 404
