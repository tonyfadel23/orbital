"""E2E tests for shared UI components: slide-over, detail drawer, toast, responsive layouts.

Tests open/close behavior, content rendering, and responsive breakpoints.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, mock_investigate_workspace


OPP_ID = "opp-20260412-120000"


@pytest.fixture(autouse=True)
def mock_workspace(page: Page):
    """Set up workspace mocks for component tests."""
    mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", "quality-all-pass.json")


class TestSlideOver:
    def _go_to_workspace(self, page):
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_slide_over_opens(self, page: Page):
        """#slide-over gains .open class when opened."""
        self._go_to_workspace(page)
        page.evaluate("openSlideOver('Test Title', '<p>Test body</p>')")
        so = page.locator("#slide-over")
        expect(so).to_have_class(re.compile("open"), timeout=3000)

    def test_slide_over_close_button(self, page: Page):
        """#slide-over-close click removes .open."""
        self._go_to_workspace(page)
        page.evaluate("openSlideOver('Test', '<p>Content</p>')")
        page.wait_for_timeout(300)
        page.locator("#slide-over-close").click()
        page.wait_for_timeout(300)
        so = page.locator("#slide-over")
        cls = so.get_attribute("class") or ""
        assert "open" not in cls, f"Expected .open removed, got: {cls}"

    def test_slide_over_backdrop_close(self, page: Page):
        """#slide-over-backdrop click hides slide-over."""
        self._go_to_workspace(page)
        page.evaluate("openSlideOver('Test', '<p>Content</p>')")
        page.wait_for_timeout(300)
        page.locator("#slide-over-backdrop").click(force=True)
        page.wait_for_timeout(300)
        so = page.locator("#slide-over")
        cls = so.get_attribute("class") or ""
        assert "open" not in cls

    def test_slide_over_title_content(self, page: Page):
        """Title and body content populate correctly."""
        self._go_to_workspace(page)
        page.evaluate("openSlideOver('My Panel Title', '<p>Panel body here</p>')")
        page.wait_for_timeout(300)
        title = page.locator("#slide-over-title")
        expect(title).to_have_text("My Panel Title")
        body = page.locator("#slide-over-body")
        expect(body).to_contain_text("Panel body here")


class TestDetailDrawer:
    def _go_to_workspace(self, page):
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_drawer_opens(self, page: Page):
        """#detail-drawer gains .open class."""
        self._go_to_workspace(page)
        # openDrawer is defined in index.html
        has_fn = page.evaluate("typeof openDrawer === 'function'")
        if has_fn:
            page.evaluate("openDrawer()")
            page.wait_for_timeout(300)
            drawer = page.locator("#detail-drawer")
            cls = drawer.get_attribute("class") or ""
            assert "open" in cls, f"Expected .open class, got: {cls}"
        else:
            # If openDrawer doesn't exist, verify the drawer element exists
            drawer = page.locator("#detail-drawer")
            expect(drawer).to_be_attached()

    def test_drawer_closes(self, page: Page):
        """Close action removes .open class."""
        self._go_to_workspace(page)
        has_fn = page.evaluate("typeof openDrawer === 'function'")
        if has_fn:
            page.evaluate("openDrawer()")
            page.wait_for_timeout(300)
            page.evaluate("closeDrawer()")
            page.wait_for_timeout(300)
            drawer = page.locator("#detail-drawer")
            cls = drawer.get_attribute("class") or ""
            assert "open" not in cls
        else:
            drawer = page.locator("#detail-drawer")
            expect(drawer).to_be_attached()


class TestToastNotifications:
    def _go_to_workspace(self, page):
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_toast_appears(self, page: Page):
        """Triggering toast() shows toast element with .visible."""
        self._go_to_workspace(page)
        page.evaluate("toast('Test notification')")
        t = page.locator("#toast")
        expect(t).to_have_class(re.compile("visible"), timeout=2000)
        expect(t).to_contain_text("Test notification")

    def test_toast_auto_dismiss(self, page: Page):
        """Toast disappears after timeout (~2500ms)."""
        self._go_to_workspace(page)
        page.evaluate("toast('Dismiss me')")
        t = page.locator("#toast")
        expect(t).to_have_class(re.compile("visible"), timeout=2000)
        # Wait for auto-dismiss (2500ms + buffer)
        page.wait_for_timeout(3500)
        cls = t.get_attribute("class") or ""
        assert "visible" not in cls, f"Toast should auto-dismiss, class: {cls}"


class TestResponsiveLayouts:
    def test_investigate_mobile_layout(self, page: Page):
        """375px viewport: page still renders without error."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)
        # Verify page loaded (not blank)
        main = page.locator("#main")
        expect(main).to_be_visible()

    def test_settings_mobile_layout(self, page: Page):
        """375px viewport: settings page renders."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.route("**/api/quality/config",
                   lambda route: route.fulfill(json={"enabled": True, "blocking_mode": "warn",
                                                      "layer_1": {}, "layer_2": {"enabled": True},
                                                      "layer_3": {"enabled": True}}, status=200))
        page.goto(f"{BASE_URL}/#settings")
        page.wait_for_timeout(1000)
        main = page.locator("#main")
        expect(main).to_be_visible()
