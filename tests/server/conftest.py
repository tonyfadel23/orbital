"""Shared test fixtures for Orbital server tests."""

import json
import shutil
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from server.config import get_project_root


@pytest.fixture
def project_root():
    """Real project root for integration tests."""
    return get_project_root()


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Temporary data directory with minimal test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Config
    config = {
        "version": "0.2.0",
        "roster_templates": {
            "core": {"agents": ["product", "design", "data", "engineering"]},
            "market_entry": {"agents": ["product", "data", "analyst", "commercial-strategy"]}
        },
        "available_agents": {
            "product": {"display_name": "Product", "role": "Orchestrator", "default_tool_access": ["google-drive"], "always_included": True},
            "design": {"display_name": "Design", "role": "Experience audit", "default_tool_access": ["figma"], "always_included": False},
            "data": {"display_name": "Data", "role": "Baselines", "default_tool_access": ["google-sheets"], "always_included": False},
            "engineering": {"display_name": "Engineering", "role": "Feasibility", "default_tool_access": ["github"], "always_included": False}
        },
        "tool_registry": {
            "figma": {"mcp_server": "plugin:figma:figma", "capabilities": ["design"]},
            "github": {"mcp_server": "github", "capabilities": ["code"]}
        },
        "quality_gates": {
            "enabled": True,
            "blocking_mode": "warn",
            "layer_1": {
                "assumption_coverage": {"enabled": True, "min_coverage": 1.0, "blocking": True},
                "confidence_floor": {"enabled": True, "threshold": 0.4, "blocking": True},
                "solution_distinctiveness": {"enabled": True, "max_jaccard": 0.7, "blocking": False},
                "evidence_freshness": {"enabled": True, "max_age_days": 180, "blocking": False},
                "vote_quorum": {"enabled": True, "min_pct": 0.8, "blocking": True},
                "finding_density": {"enabled": True, "min_findings": 3, "blocking": True}
            },
            "layer_2": {"enabled": True, "model": "claude-haiku-4-5-20251001", "rubrics": ["coherence"], "pass_threshold": 0.6},
            "layer_3": {"enabled": True, "rubrics": ["strategic_alignment"]}
        }
    }
    (data_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Context layers
    for layer, name, content in [
        ("L1", "global", {"id": "L1-global", "type": "global", "name": "Global", "content": {}, "sufficiency": {"status": "sufficient", "gaps": []}, "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}),
        ("L2a", "groceries", {"id": "L2a-groceries", "type": "business_line", "name": "Groceries", "content": {}, "sufficiency": {"status": "sufficient", "gaps": []}, "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}),
        ("L2b", "ae", {"id": "L2b-ae", "type": "market", "name": "UAE", "content": {}, "sufficiency": {"status": "sufficient", "gaps": []}, "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}),
        ("L2a", "gr", {"id": "L2a-gr", "type": "business_line", "name": "grocery & retail", "content": {"product_overview": "Commercial levers: promotions, pricing strategy, and top-of-funnel growth constructs."}, "sufficiency": {"status": "gaps_identified", "gaps": [{"field": "goals", "severity": "important", "description": "No quantitative targets — unit economics all TBD."}]}, "created_at": "2026-04-12T00:00:00Z", "updated_at": "2026-04-12T00:00:00Z"}),
    ]:
        layer_dir = data_dir / "context" / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        (layer_dir / f"{name}.json").write_text(json.dumps(content, indent=2))

    # Sample workspace
    ws_dir = data_dir / "workspaces" / "opp-20260405-120000"
    ws_dir.mkdir(parents=True)
    (ws_dir / "contributions").mkdir()
    (ws_dir / "reviews").mkdir()
    (ws_dir / "artifacts").mkdir()

    opp = {
        "id": "opp-20260405-120000",
        "type": "hypothesis",
        "title": "Test opportunity for server tests",
        "description": "This is a test opportunity used in automated tests.",
        "context_refs": ["L1-global"],
        "assumptions": [
            {"id": "asm-001", "content": "Test assumption content here", "status": "untested", "importance": "critical"}
        ],
        "success_signals": ["Metric improves by 10%"],
        "kill_signals": ["No measurable change at week 4"],
        "status": "orbiting",
        "roster": [
            {"function": "product", "rationale": "Orchestrates investigation", "investigation_tracks": [{"track": "opportunity framing", "question": "What is the core question?", "expected_artifacts": ["product.md"]}], "tool_access": ["google-drive"]},
            {"function": "data", "rationale": "Baseline analysis", "investigation_tracks": [{"track": "baseline analysis", "question": "What are the current metrics?", "expected_artifacts": ["data.md"]}], "tool_access": ["google-sheets"]},
            {"function": "design", "rationale": "Experience audit", "investigation_tracks": [{"track": "experience audit", "question": "What are the UX gaps?", "expected_artifacts": ["design.md"]}], "tool_access": ["figma"]},
            {"function": "engineering", "rationale": "Feasibility check", "investigation_tracks": [{"track": "feasibility", "question": "Can we build this?", "expected_artifacts": ["engineering.md"]}], "tool_access": ["github"]}
        ],
        "decision": None,
        "created_at": "2026-04-05T12:00:00Z",
        "updated_at": "2026-04-05T14:00:00Z"
    }
    (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

    # A contribution
    contrib = {
        "id": "contrib-data-20260405-140000",
        "opportunity_id": "opp-20260405-120000",
        "agent_function": "data",
        "round": 1,
        "findings": [
            {"id": "find-001", "type": "measurement", "content": "Add-to-cart rate is 12% blended across all users", "confidence": 0.9, "source": "analytics dashboard", "assumptions_addressed": ["asm-001"], "direction": "neutral"}
        ],
        "artifacts_produced": [],
        "cross_references": [],
        "self_review": {"self_checked": True, "self_check_notes": "Verified data sources are current"},
        "created_at": "2026-04-05T14:00:00Z"
    }
    (ws_dir / "contributions" / "data-round-1.json").write_text(json.dumps(contrib, indent=2))

    # An artifact
    (ws_dir / "artifacts" / "data.md").write_text("# Data Agent — Baselines\n\nBaseline ATC: 12%\n")

    return data_dir


@pytest.fixture
def tmp_project_root(tmp_path, tmp_data_dir):
    """Temporary project root with data and schemas."""
    # Copy schemas
    real_schemas = get_project_root() / "schemas"
    shutil.copytree(real_schemas, tmp_path / "schemas")
    return tmp_path


@pytest.fixture
def app(tmp_project_root):
    """FastAPI app configured with temp data."""
    from server.app import create_app
    return create_app(root=tmp_project_root)


@pytest.fixture
async def client(app):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
