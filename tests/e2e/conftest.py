"""Playwright E2E test fixtures for Orbital."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


def load_fixture_raw(name: str) -> str:
    """Load a fixture file as raw text."""
    return (FIXTURES_DIR / name).read_text()


def wrap_workspace(raw):
    """Wrap a raw opportunity fixture into workspace API response format.

    The GET /api/workspaces/{id} endpoint returns:
      {"opportunity": opp, "contributions": [...], "reviews": [], "artifacts": [],
       "synthesis": ..., "evidence": []}
    But test fixtures store the opportunity object directly.
    """
    if "opportunity" in raw:
        return raw  # already wrapped
    # Build contribution file listings from embedded contribution data
    contrib_listings = []
    if "contributions" in raw:
        contrib_listings = [
            {"filename": f"{c['function']}-round-{c.get('round', 1)}.json", "type": "json"}
            for c in raw["contributions"]
        ]
    # Build opportunity (exclude top-level workspace fields)
    opp = {k: v for k, v in raw.items() if k not in ("contributions",)}
    return {
        "opportunity": opp,
        "contributions": contrib_listings,
        "reviews": [],
        "artifacts": [],
        "synthesis": raw.get("synthesis"),
        "evidence": [],
    }


def mock_investigate_workspace(page, opp_id, workspace_fixture, quality_fixture=None):
    """Mock APIs for investigate phase with optional quality data."""
    raw = load_fixture(workspace_fixture)
    ws = wrap_workspace(raw)
    page.route(f"**/api/workspaces/{opp_id}", lambda route: route.fulfill(json=ws, status=200))
    page.route(f"**/api/launch/{opp_id}/status", lambda route: route.fulfill(
        json={"function_outputs": {}}, status=200
    ))
    page.route("**/api/processes", lambda route: route.fulfill(json=[], status=200))
    if quality_fixture:
        qr = load_fixture(quality_fixture)
        page.route(f"**/api/workspaces/{opp_id}/quality", lambda route: route.fulfill(
            json=qr, status=200
        ))
        page.route(f"**/api/workspaces/{opp_id}/quality/gates", lambda route: route.fulfill(
            json=qr.get("layer_1", {}), status=200
        ))
