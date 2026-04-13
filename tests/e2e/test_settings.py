"""E2E tests for the Settings page — quality gate configuration form.

Tests the #settings route: toggle controls, threshold inputs,
blocking mode dropdown, and save/PATCH behavior.
"""

import json
import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, load_fixture


@pytest.fixture(autouse=True)
def mock_settings_apis(page: Page):
    """Mock the quality config API for all settings tests.

    The API returns the quality_gates sub-object directly, but
    renderSettings() does config?.quality_gates || fallback.
    Wrap it so the frontend can find config.quality_gates.
    """
    config = {"quality_gates": load_fixture("quality-config.json")}
    page.route(
        "**/api/quality/config",
        lambda route: route.fulfill(json=config, status=200)
        if route.request.method == "GET"
        else route.fulfill(json={"ok": True}, status=200),
    )
    page.route("**/api/processes", lambda route: route.fulfill(json=[], status=200))


class TestSettingsNavigation:
    def test_settings_route_renders(self, page: Page):
        """#settings renders the Settings heading."""
        page.goto(f"{BASE_URL}/#settings")
        heading = page.get_by_text("Quality Gates").first
        expect(heading).to_be_visible(timeout=5000)

    def test_settings_back_to_dashboard(self, page: Page):
        """Navigating away from settings returns to dashboard."""
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_timeout(500)
        page.goto(f"{BASE_URL}/#")
        page.wait_for_selector(".workspace-card, .setup-chat-empty", timeout=5000)


class TestSettingsForm:
    def test_enabled_toggle_renders(self, page: Page):
        """#qg-enabled checkbox reflects config value."""
        page.goto(f"{BASE_URL}/#settings")
        toggle = page.locator("#qg-enabled")
        expect(toggle).to_be_visible(timeout=5000)
        assert toggle.is_checked(), "Expected enabled toggle to be checked"

    def test_blocking_mode_select(self, page: Page):
        """#qg-blocking-mode dropdown has 3 options."""
        page.goto(f"{BASE_URL}/#settings")
        select = page.locator("#qg-blocking-mode")
        expect(select).to_be_visible(timeout=5000)
        options = select.locator("option")
        assert options.count() == 3, f"Expected 3 blocking mode options, got {options.count()}"

    def test_layer1_gate_toggles(self, page: Page):
        """6 gate toggles render with .settings-toggle[data-gate]."""
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_selector(".settings-toggle[data-gate]", timeout=5000)
        toggles = page.locator(".settings-toggle[data-gate]")
        assert toggles.count() == 6, f"Expected 6 gate toggles, got {toggles.count()}"

    def test_layer1_threshold_inputs(self, page: Page):
        """Threshold inputs render with .settings-input[data-gate]."""
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_selector(".settings-input[data-gate]", timeout=5000)
        inputs = page.locator(".settings-input[data-gate]")
        assert inputs.count() > 0, "Expected at least one threshold input"

    def test_layer2_toggle(self, page: Page):
        """Layer 2 enabled toggle is present."""
        page.goto(f"{BASE_URL}/#settings")
        toggle = page.locator("#l2-enabled")
        expect(toggle).to_be_visible(timeout=5000)

    def test_layer3_toggle(self, page: Page):
        """Layer 3 enabled toggle is present."""
        page.goto(f"{BASE_URL}/#settings")
        toggle = page.locator("#l3-enabled")
        expect(toggle).to_be_visible(timeout=5000)

    def test_save_sends_patch(self, page: Page):
        """Click Save -> intercept PATCH /quality/config with correct payload."""
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_selector("#qg-enabled", timeout=5000)

        # Intercept the PATCH request
        patch_requests = []
        page.route(
            "**/api/quality/config",
            lambda route: (
                patch_requests.append(route.request.post_data)
                or route.fulfill(json={"ok": True}, status=200)
            )
            if route.request.method == "PATCH"
            else route.fulfill(json=load_fixture("quality-config.json"), status=200),
        )

        # Click save button
        save_btn = page.get_by_text("Save").first
        expect(save_btn).to_be_visible()
        save_btn.click()
        page.wait_for_timeout(1000)

        assert len(patch_requests) > 0, "Expected PATCH request to be sent"
        payload = json.loads(patch_requests[0])
        assert "quality_gates" in payload, "Expected payload to contain quality_gates key"

    def test_save_shows_toast(self, page: Page):
        """After save -> 'Settings saved' toast appears."""
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_selector("#qg-enabled", timeout=5000)

        save_btn = page.get_by_text("Save").first
        save_btn.click()

        toast = page.locator("#toast")
        expect(toast).to_have_class(re.compile("visible"), timeout=3000)
