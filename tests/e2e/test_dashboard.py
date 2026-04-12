"""E2E tests for dashboard, navigation, and deletion flows.

These tests run against a live server at localhost:8000. They test
the frontend rendering and navigation without requiring agent subprocesses.
"""

import re

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def navigate_to_dashboard(page: Page):
    """Navigate to dashboard before each test."""
    page.goto(f"{BASE_URL}/#")
    page.wait_for_selector(".workspace-card, .setup-chat-empty", timeout=5000)


class TestDashboard:
    def test_workspace_cards_render(self, page: Page):
        """Dashboard shows workspace cards with correct structure."""
        page.wait_for_selector(".workspace-card", timeout=5000)
        cards = page.locator(".workspace-card")
        count = cards.count()
        assert count > 0, "Expected at least one workspace card"

        # Each card has a status pill
        first_card = cards.first
        expect(first_card.locator(".status-pill").first).to_be_visible()

    def test_heading_shows_count(self, page: Page):
        """Dashboard heading shows correct investigation count."""
        heading = page.locator(".heading").first
        expect(heading).to_be_visible()
        text = heading.text_content()
        assert "Orb" in text

    def test_new_investigation_button(self, page: Page):
        """'+ New Orb' button is visible and navigates."""
        btn = page.get_by_text("New Orb").first
        expect(btn).to_be_visible()
        btn.click()
        page.wait_for_url(re.compile(r"#orb/new"))

    def test_card_click_navigates(self, page: Page):
        """Clicking a workspace card navigates to orb view."""
        card = page.locator(".workspace-card").first
        card.click()
        page.wait_for_url(re.compile(r"#orb/"))


class TestNavigation:
    def test_hash_routing_dashboard(self, page: Page):
        """Hash route '#' renders dashboard."""
        page.goto(f"{BASE_URL}/#")
        expect(page.locator(".workspace-card").first).to_be_visible()

    def test_hash_routing_new_investigation(self, page: Page):
        """Hash route '#orb/new' renders agree phase."""
        page.goto(f"{BASE_URL}/#orb/new")
        expect(page.get_by_text("New Orb")).to_be_visible()
        expect(page.get_by_placeholder("What should we investigate?")).to_be_visible()

    def test_back_link_text_and_navigation(self, page: Page):
        """Back link shows 'All Orbs' and navigates to dashboard."""
        page.goto(f"{BASE_URL}/#orb/new")
        back = page.get_by_text("All Orbs")
        expect(back).to_be_visible()
        back.click()
        page.wait_for_url(re.compile(r"#$|#/$"))

    def test_logo_navigates_to_dashboard(self, page: Page):
        """Clicking ORBITAL logo navigates from orb to dashboard."""
        page.goto(f"{BASE_URL}/#orb/new")
        page.locator("#logo").click()
        page.wait_for_url(re.compile(r"#$|#/$"))

    def test_workspace_redirect(self, page: Page):
        """'#workspace/' routes redirect to '#orb/'."""
        # Get a valid opp_id from dashboard cards
        page.goto(f"{BASE_URL}/#")
        card = page.locator(".workspace-card").first
        card_id = card.get_attribute("data-opp-id") or card.get_attribute("onclick")
        if card_id:
            # Extract opp-id from onclick or data attribute
            import re as r
            match = r.search(r"opp-\d{8}-\d{6}", str(card_id))
            if match:
                opp_id = match.group()
                page.goto(f"{BASE_URL}/#workspace/{opp_id}")
                page.wait_for_url(re.compile(r"#orb/"))


class TestAgreePhase:
    def test_agree_phase_layout(self, page: Page):
        """Agree phase has split layout: chat + setup cards."""
        page.goto(f"{BASE_URL}/#orb/new")

        # Left: chat panel
        expect(page.get_by_placeholder("What should we investigate?")).to_be_visible()

        # Right: setup cards
        expect(page.get_by_text("Progress")).to_be_visible()
        expect(page.get_by_text("Opportunity")).to_be_visible()
        expect(page.get_by_text("Context", exact=True)).to_be_visible()
        expect(page.get_by_text("Connectors")).to_be_visible()

    def test_connectors_visible(self, page: Page):
        """All 12 connector toggles render in agree phase."""
        page.goto(f"{BASE_URL}/#orb/new")
        connectors = ["figma", "github", "google-drive", "google-sheets",
                       "gmail", "linear", "slack", "jira",
                       "bigquery", "looker", "tableau", "miro"]
        for name in connectors:
            expect(page.get_by_text(name, exact=True).first).to_be_visible()


class TestDeletion:
    def test_delete_cancel(self, page: Page):
        """Canceling deletion keeps the workspace."""
        cards_before = page.locator(".workspace-card").count()
        if cards_before == 0:
            pytest.skip("No workspaces to test deletion")

        # Handle the confirm dialog — click Cancel
        page.on("dialog", lambda d: d.dismiss())
        page.locator(".workspace-card .delete-btn, .workspace-card [onclick*='delete']").first.click()

        cards_after = page.locator(".workspace-card").count()
        assert cards_after == cards_before

    def test_delete_confirm(self, page: Page):
        """Confirming deletion removes the workspace."""
        cards_before = page.locator(".workspace-card").count()
        if cards_before == 0:
            pytest.skip("No workspaces to test deletion")

        # Handle the confirm dialog — click OK
        page.on("dialog", lambda d: d.accept())
        page.locator(".workspace-card .delete-btn, .workspace-card [onclick*='delete']").first.click()

        # Wait for card removal
        page.wait_for_timeout(1000)
        cards_after = page.locator(".workspace-card").count()
        assert cards_after == cards_before - 1


class TestResponsive:
    def test_mobile_stacking(self, page: Page):
        """Mobile viewport stacks layout vertically."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/#orb/new")

        # Chat input should still be accessible
        expect(page.get_by_placeholder("What should we investigate?")).to_be_visible()
        # Cards should be visible (scrollable)
        expect(page.get_by_text("Progress")).to_be_visible()
