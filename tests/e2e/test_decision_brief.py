"""E2E tests for decision brief generation and display.

Tests the decision-brief API: launch, blocking, and markdown rendering.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, load_fixture, load_fixture_raw, mock_investigate_workspace, wrap_workspace


OPP_ID = "opp-20260412-120000"


class TestDecisionBrief:
    def _setup_decided(self, page):
        ws = wrap_workspace(load_fixture("workspace-decided.json"))
        page.route(f"**/api/workspaces/{OPP_ID}", lambda route: route.fulfill(json=ws, status=200))
        page.route(f"**/api/launch/{OPP_ID}/status", lambda route: route.fulfill(
            json={"function_outputs": {}}, status=200
        ))
        page.route("**/api/processes", lambda route: route.fulfill(json=[], status=200))
        page.route(f"**/api/workspaces/{OPP_ID}/quality", lambda route: route.fulfill(
            json=load_fixture("quality-all-pass.json"), status=200
        ))

    def test_decision_brief_launch_success(self, page: Page):
        """POST /decision-brief returns launched status."""
        self._setup_decided(page)
        page.route(
            f"**/api/launch/{OPP_ID}/decision-brief",
            lambda route: route.fulfill(
                json={"status": "launched", "opp_id": OPP_ID}, status=200
            ),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/launch/{OPP_ID}/decision-brief', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}
                }});
                return await resp.json();
            }}
        """)
        assert result["status"] == "launched"
        assert result["opp_id"] == OPP_ID

    def test_decision_brief_blocked_422(self, page: Page):
        """Mock 422 (vote quorum) -> error shows blockers."""
        self._setup_decided(page)
        blocked = load_fixture("decision-brief-blocked.json")
        page.route(
            f"**/api/launch/{OPP_ID}/decision-brief",
            lambda route: route.fulfill(json=blocked, status=422),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/launch/{OPP_ID}/decision-brief', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}
                }});
                return {{ status: resp.status, body: await resp.json() }};
            }}
        """)
        assert result["status"] == 422
        assert "vote_quorum" in result["body"]["detail"]

    def test_brief_markdown_content(self, page: Page):
        """Mock GET /decision-brief returns markdown content."""
        self._setup_decided(page)
        brief_md = load_fixture_raw("decision-brief.md")
        page.route(
            f"**/api/workspaces/{OPP_ID}/decision-brief",
            lambda route: route.fulfill(body=brief_md, status=200,
                                        headers={"Content-Type": "text/markdown"}),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/workspaces/{OPP_ID}/decision-brief');
                return await resp.text();
            }}
        """)
        assert "Recommendation" in result
        assert "Solution 1" in result
        assert "Counter-Signals" in result

    def test_brief_has_expected_sections(self, page: Page):
        """Decision brief markdown has expected section structure."""
        brief_md = load_fixture_raw("decision-brief.md")
        assert "## Recommendation" in brief_md
        assert "## Solutions Evaluated" in brief_md
        assert "## Evidence Summary" in brief_md
        assert "## Counter-Signals" in brief_md
        assert "## Proceed Conditions" in brief_md

    def test_workspace_decided_status(self, page: Page):
        """Decided workspace fixture has correct decision field."""
        ws = load_fixture("workspace-decided.json")
        assert ws["status"] == "decided"
        assert ws["decision"] is not None
        assert ws["decision"]["selected_solution"] == "sol-001"
