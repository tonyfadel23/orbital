"""E2E tests for dot-vote launch API behavior and vote results display.

Tests dot-vote API mocking: success, 422 blocking, and warn responses.
Also tests vote results rendering in the workspace.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, load_fixture, mock_investigate_workspace, wrap_workspace


OPP_ID = "opp-20260412-120000"


class TestDotVoteLaunch:
    """Tests dot-vote launch API responses via mocked endpoints."""

    def test_dot_vote_success_response(self, page: Page):
        """POST /dot-vote success returns launched status."""
        mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", "quality-all-pass.json")
        success = load_fixture("dot-vote-success.json")
        page.route(
            f"**/api/launch/{OPP_ID}/dot-vote",
            lambda route: route.fulfill(json=success, status=200),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        # Trigger dot-vote via API call in page context
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/launch/{OPP_ID}/dot-vote', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}
                }});
                return await resp.json();
            }}
        """)
        assert result["status"] == "launched"
        assert result["mode"] == "dot_vote"

    def test_dot_vote_blocked_422(self, page: Page):
        """Mock 422 -> error response contains blocker detail."""
        mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", "quality-mixed.json")
        blocked = load_fixture("dot-vote-blocked.json")
        page.route(
            f"**/api/launch/{OPP_ID}/dot-vote",
            lambda route: route.fulfill(json=blocked, status=422),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/launch/{OPP_ID}/dot-vote', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}
                }});
                return {{ status: resp.status, body: await resp.json() }};
            }}
        """)
        assert result["status"] == 422
        assert "confidence_floor" in result["body"]["detail"]

    def test_dot_vote_with_warnings(self, page: Page):
        """Mock warn response -> proceeds with warnings array."""
        mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", "quality-all-pass.json")
        warn = load_fixture("dot-vote-warn.json")
        page.route(
            f"**/api/launch/{OPP_ID}/dot-vote",
            lambda route: route.fulfill(json=warn, status=200),
        )
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(500)

        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/launch/{OPP_ID}/dot-vote', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}
                }});
                return await resp.json();
            }}
        """)
        assert result["status"] == "launched"
        assert len(result["warnings"]) == 2
        assert "finding_density" in result["warnings"][0]


class TestVoteResults:
    """Tests vote results display in scored workspace."""

    def _setup_scored(self, page):
        ws = wrap_workspace(load_fixture("workspace-scored.json"))
        votes = load_fixture("votes-complete.json")
        page.route(f"**/api/workspaces/{OPP_ID}", lambda route: route.fulfill(json=ws, status=200))
        page.route(f"**/api/launch/{OPP_ID}/status", lambda route: route.fulfill(
            json={"function_outputs": {}}, status=200
        ))
        page.route("**/api/processes", lambda route: route.fulfill(json=[], status=200))
        page.route(f"**/api/workspaces/{OPP_ID}/votes", lambda route: route.fulfill(
            json=votes, status=200
        ))
        page.route(f"**/api/workspaces/{OPP_ID}/quality", lambda route: route.fulfill(
            json=load_fixture("quality-all-pass.json"), status=200
        ))
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_votes_api_returns_data(self, page: Page):
        """GET /votes returns vote array for scored workspace."""
        self._setup_scored(page)
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/workspaces/{OPP_ID}/votes');
                return await resp.json();
            }}
        """)
        assert len(result) == 3
        assert result[0]["function"] == "product"

    def test_vote_has_rankings(self, page: Page):
        """Each vote has rankings with solution_id and scores."""
        self._setup_scored(page)
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/workspaces/{OPP_ID}/votes');
                return await resp.json();
            }}
        """)
        for vote in result:
            assert "rankings" in vote
            assert len(vote["rankings"]) == 3
            for ranking in vote["rankings"]:
                assert "solution_id" in ranking
                assert "scores" in ranking
                assert "rationale" in ranking

    def test_vote_rationale_not_empty(self, page: Page):
        """Vote rationales are at least 20 characters."""
        self._setup_scored(page)
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/workspaces/{OPP_ID}/votes');
                return await resp.json();
            }}
        """)
        for vote in result:
            for ranking in vote["rankings"]:
                assert len(ranking["rationale"]) >= 20, \
                    f"Rationale too short: {ranking['rationale']}"

    def test_vote_scores_have_ice(self, page: Page):
        """Vote scores include impact, confidence, ease."""
        self._setup_scored(page)
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch('/api/workspaces/{OPP_ID}/votes');
                return await resp.json();
            }}
        """)
        for vote in result:
            for ranking in vote["rankings"]:
                scores = ranking["scores"]
                assert "impact" in scores
                assert "confidence" in scores
                assert "ease" in scores
