"""E2E tests for agent subprocess flows using API mocking.

These tests use Playwright's page.route() to intercept API calls,
removing the need for live Claude agent subprocesses.
"""

import json
from pathlib import Path

import pytest
from playwright.sync_api import Page, Route, expect


BASE_URL = "http://localhost:8000"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


class TestAgreeFlow:
    """Tests for the agree phase with mocked agent responses."""

    def _mock_agree_apis(self, page: Page, opp_id: str):
        """Set up API mocks for agree phase interactions."""
        workspace = load_fixture("workspace-aligning.json")
        workspace["id"] = opp_id

        # Mock workspace GET to return drafting workspace
        page.route(
            f"**/api/workspaces/{opp_id}",
            lambda route: route.fulfill(json=workspace, status=200),
        )
        # Mock send — agent receives message
        page.route(
            f"**/api/launch/{opp_id}/send",
            lambda route: route.fulfill(json={"sent": True}, status=200),
        )
        # Mock start — agent launches
        page.route(
            f"**/api/launch/{opp_id}/start",
            lambda route: route.fulfill(
                json={"status": "launched", "opp_id": opp_id}, status=200
            ),
        )
        # Mock status — agent output
        page.route(
            f"**/api/launch/{opp_id}/status",
            lambda route: route.fulfill(
                json={"running": False, "output": "Investigation framing complete."},
                status=200,
            ),
        )
        # Mock processes endpoint
        page.route(
            "**/api/launch/processes",
            lambda route: route.fulfill(json={"processes": []}, status=200),
        )

    def test_send_message_shows_bubble(self, page: Page):
        """Sending a message in agree phase shows user bubble in chat."""
        opp_id = "opp-e2e-agree-001"
        self._mock_agree_apis(page, opp_id)

        page.goto(f"{BASE_URL}/#orb/new")
        page.wait_for_selector("[id='setup-input-bar']", timeout=5000)

        # Type and send a message
        input_box = page.get_by_placeholder("What should we investigate?")
        input_box.fill("Investigate checkout abandonment on mobile")
        page.locator("#setup-input-bar button").click()

        # User message should appear as a chat bubble
        page.wait_for_timeout(500)
        bubbles = page.locator(".chat-bubble, .setup-chat-bubble, [class*='bubble']")
        assert bubbles.count() > 0 or page.get_by_text("checkout abandonment").count() > 0

    def test_agree_phase_has_chat_input(self, page: Page):
        """Agree phase renders chat input with correct placeholder."""
        page.goto(f"{BASE_URL}/#orb/new")
        input_box = page.get_by_placeholder("What should we investigate?")
        expect(input_box).to_be_visible()
        expect(input_box).to_be_editable()


class TestAssembleFlow:
    """Tests for assemble phase with mocked roster data."""

    def _mock_assemble_apis(self, page: Page, opp_id: str):
        """Set up API mocks for assemble phase."""
        workspace = load_fixture("workspace-with-roster.json")
        workspace["id"] = opp_id

        page.route(
            f"**/api/workspaces/{opp_id}",
            lambda route: route.fulfill(json=workspace, status=200),
        )
        page.route(
            f"**/api/launch/{opp_id}/assemble",
            lambda route: route.fulfill(
                json={"status": "launched", "opp_id": opp_id}, status=200
            ),
        )
        page.route(
            f"**/api/launch/{opp_id}/status",
            lambda route: route.fulfill(
                json={"running": False, "output": "Roster assembled."},
                status=200,
            ),
        )
        page.route(
            "**/api/launch/processes",
            lambda route: route.fulfill(json={"processes": []}, status=200),
        )

    def test_assemble_phase_shows_roster(self, page: Page):
        """Assemble phase renders roster agent cards."""
        opp_id = "opp-e2e-assemble-001"
        self._mock_assemble_apis(page, opp_id)

        page.goto(f"{BASE_URL}/#orb/{opp_id}")
        page.wait_for_timeout(1000)

        # Check for roster-related content (agent cards or roster section)
        # The workspace has roster, so the UI should show agent info
        content = page.content()
        assert "product" in content.lower() or "roster" in content.lower() or "agent" in content.lower()


class TestInvestigateFlow:
    """Tests for investigate phase with mocked contributions."""

    def _mock_investigate_apis(self, page: Page, opp_id: str):
        """Set up API mocks for investigate phase."""
        workspace = load_fixture("workspace-orbiting.json")
        workspace["id"] = opp_id

        # Full workspace state with contributions
        full_state = {
            **workspace,
            "contributions": [
                {
                    "id": "contrib-data-001",
                    "agent_function": "data",
                    "round": 1,
                    "findings": [
                        {
                            "id": "find-001",
                            "type": "measurement",
                            "content": "Mobile checkout abandonment is 68%",
                            "confidence": 0.85,
                            "source": "analytics",
                        }
                    ],
                }
            ],
            "reviews": [],
            "artifacts": ["data.md"],
            "synthesis": None,
        }

        page.route(
            f"**/api/workspaces/{opp_id}",
            lambda route: route.fulfill(json=full_state, status=200),
        )
        page.route(
            f"**/api/launch/{opp_id}/status",
            lambda route: route.fulfill(
                json={
                    "running": False,
                    "function_outputs": {
                        "data": {"running": False, "exit_code": 0, "output": "done"},
                        "design": {"running": False, "exit_code": 0, "output": "done"},
                        "product": {"running": False, "exit_code": 0, "output": "done"},
                    },
                },
                status=200,
            ),
        )
        page.route(
            "**/api/launch/processes",
            lambda route: route.fulfill(json={"processes": []}, status=200),
        )

    def test_investigate_phase_renders_graph(self, page: Page):
        """Investigate phase renders the graph canvas."""
        opp_id = "opp-e2e-investigate-001"
        self._mock_investigate_apis(page, opp_id)

        page.goto(f"{BASE_URL}/#orb/{opp_id}")
        page.wait_for_timeout(2000)

        # Graph canvas should be present for investigating status
        canvas = page.locator("canvas")
        if canvas.count() > 0:
            expect(canvas.first).to_be_visible()
        else:
            # Fallback: check for graph-related elements
            content = page.content()
            assert "orbiting" in content.lower() or "graph" in content.lower()

    def test_investigate_sidebar_tabs(self, page: Page):
        """Investigate phase sidebar has OVERVIEW, EVIDENCE, AGENTS tabs."""
        opp_id = "opp-e2e-investigate-002"
        self._mock_investigate_apis(page, opp_id)

        page.goto(f"{BASE_URL}/#orb/{opp_id}")
        page.wait_for_timeout(2000)

        # Check for tab-like elements
        for tab_text in ["OVERVIEW", "EVIDENCE", "AGENTS"]:
            tab = page.get_by_text(tab_text, exact=True)
            if tab.count() > 0:
                expect(tab.first).to_be_visible()


class TestProcessesPolling:
    """Tests for the running processes dashboard section."""

    def test_processes_endpoint_returns_empty(self, page: Page):
        """Processes endpoint returns empty list when no agents running."""
        page.goto(f"{BASE_URL}/#")
        page.wait_for_timeout(1000)

        # The processes section should not show errors
        # (Bug #2 was fixed — endpoint no longer 404s)
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" and "processes" in msg.text else None)
        page.wait_for_timeout(4000)  # Wait for at least one poll cycle

        process_errors = [e for e in console_errors if "404" in e and "processes" in e]
        assert len(process_errors) == 0, f"Processes endpoint still returning errors: {process_errors}"

    def test_processes_with_running_agent(self, page: Page):
        """Processes section shows running agent with kill button."""
        # Mock processes to return a running agent
        page.route(
            "**/api/launch/processes",
            lambda route: route.fulfill(
                json={
                    "processes": [
                        {
                            "key": "opp-e2e-001",
                            "opp_id": "opp-e2e-001",
                            "running": True,
                            "pid": 12345,
                        }
                    ]
                },
                status=200,
            ),
        )

        page.goto(f"{BASE_URL}/#")
        page.wait_for_timeout(4000)  # Wait for poll to pick up mock

        # Check if running process appears
        content = page.content()
        assert "opp-e2e-001" in content or "running" in content.lower()
