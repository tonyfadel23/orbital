"""Tests for catalog router (config.json: agents, templates, tools)."""

import pytest


@pytest.mark.asyncio
class TestCatalogRouter:
    async def test_get_full_catalog(self, client):
        resp = await client.get("/api/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert "roster_templates" in data
        assert "available_agents" in data
        assert "tool_registry" in data

    async def test_get_agents(self, client):
        resp = await client.get("/api/catalog/agents")
        assert resp.status_code == 200
        agents = resp.json()
        assert "product" in agents
        assert agents["product"]["always_included"] is True
        assert "design" in agents

    async def test_get_templates(self, client):
        resp = await client.get("/api/catalog/templates")
        assert resp.status_code == 200
        templates = resp.json()
        assert "core" in templates
        assert "product" in templates["core"]["agents"]

    async def test_get_tools(self, client):
        resp = await client.get("/api/catalog/tools")
        assert resp.status_code == 200
        tools = resp.json()
        assert "figma" in tools
