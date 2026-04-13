"""E2E tests for the Quality tab in the investigate sidebar and the quality strip.

Tests gate cards rendering, layer 2/3 rubrics, score styling,
and action buttons (Run LLM Judge / Run Agent Judge).
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, load_fixture, mock_investigate_workspace


OPP_ID = "opp-20260412-120000"


class TestQualityTab:
    def _setup_quality(self, page, quality_fixture="quality-all-pass.json"):
        """Navigate to investigate view with quality data mocked."""
        mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", quality_fixture)
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def _open_quality_tab(self, page):
        """Click Quality tab and trigger data load.

        switchSidebarTab() only toggles CSS classes; loadQualityTab()
        is only called on initial render when activeTab === 'quality'.
        We must call it explicitly after switching tabs.
        """
        page.locator(".sidebar-tab", has_text="Quality").click()
        page.evaluate(f"loadQualityTab('{OPP_ID}')")
        page.wait_for_timeout(1000)

    def test_quality_tab_visible(self, page: Page):
        """4th sidebar tab 'Quality' is visible in investigate phase."""
        self._setup_quality(page)
        tab = page.locator(".sidebar-tab", has_text="Quality")
        expect(tab).to_be_visible(timeout=5000)

    def test_quality_tab_click_shows_content(self, page: Page):
        """Clicking Quality tab shows #quality-tab-content."""
        self._setup_quality(page)
        page.locator(".sidebar-tab", has_text="Quality").click()
        content = page.locator("#quality-tab-content")
        expect(content).to_be_visible(timeout=5000)

    def test_overall_score_renders_pass(self, page: Page):
        """All-pass fixture -> score shows green class."""
        self._setup_quality(page, "quality-all-pass.json")
        self._open_quality_tab(page)
        score = page.locator(".quality-score").first
        expect(score).to_be_visible()
        assert "100%" in score.text_content()

    def test_overall_score_renders_fail(self, page: Page):
        """Mixed fixture -> score shows red/amber class."""
        self._setup_quality(page, "quality-mixed.json")
        self._open_quality_tab(page)
        score = page.locator(".quality-score").first
        expect(score).to_be_visible()
        assert "67%" in score.text_content()

    def test_gate_cards_render(self, page: Page):
        """6 .quality-gate cards render with correct gate names."""
        self._setup_quality(page, "quality-all-pass.json")
        self._open_quality_tab(page)
        gates = page.locator(".quality-gate")
        assert gates.count() == 6, f"Expected 6 gate cards, got {gates.count()}"

    def test_gate_pass_styling(self, page: Page):
        """Passing gates have .quality-gate--pass class."""
        self._setup_quality(page, "quality-all-pass.json")
        self._open_quality_tab(page)
        pass_gates = page.locator(".quality-gate--pass")
        assert pass_gates.count() == 6, f"Expected 6 pass gates, got {pass_gates.count()}"

    def test_gate_fail_styling(self, page: Page):
        """Failing blocking gates have .quality-gate--fail class."""
        self._setup_quality(page, "quality-all-fail.json")
        self._open_quality_tab(page)
        fail_gates = page.locator(".quality-gate--fail")
        assert fail_gates.count() >= 4, f"Expected at least 4 fail gates, got {fail_gates.count()}"

    def test_gate_details_text(self, page: Page):
        """Gate detail text shows score info."""
        self._setup_quality(page, "quality-all-pass.json")
        self._open_quality_tab(page)
        values = page.locator(".quality-gate__value")
        assert values.count() > 0, "Expected gate detail values"
        first_detail = values.first.text_content()
        assert len(first_detail) > 0, "Expected non-empty detail text"

    def test_layer2_section_hidden_when_null(self, page: Page):
        """Layer 2 section hidden when layer_2 is null."""
        self._setup_quality(page, "quality-mixed.json")  # has layer_2: null
        self._open_quality_tab(page)
        rubrics = page.locator(".quality-rubric")
        assert rubrics.count() == 0, "Expected no rubrics when layer_2 is null"

    def test_layer2_rubrics_render(self, page: Page):
        """With layer2 fixture -> rubric badges appear."""
        self._setup_quality(page, "quality-with-layer2.json")
        self._open_quality_tab(page)
        rubrics = page.locator(".quality-rubric")
        assert rubrics.count() == 5, f"Expected 5 L2 rubrics, got {rubrics.count()}"

    def test_layer3_section_render(self, page: Page):
        """With layer3 fixture -> synthesis quality section visible."""
        self._setup_quality(page, "quality-with-layer3.json")
        self._open_quality_tab(page)
        rubrics = page.locator(".quality-rubric")
        # 5 from L2 + 5 from L3 = 10
        assert rubrics.count() == 10, f"Expected 10 rubrics (L2+L3), got {rubrics.count()}"

    def test_run_llm_judge_button(self, page: Page):
        """'Run LLM Judge' button visible."""
        self._setup_quality(page, "quality-all-pass.json")
        page.route(
            f"**/api/workspaces/{OPP_ID}/quality/evaluate",
            lambda route: route.fulfill(json={"status": "started"}, status=200),
        )
        self._open_quality_tab(page)
        btn = page.get_by_text("Run LLM Judge").first
        expect(btn).to_be_visible()

    def test_run_agent_judge_button(self, page: Page):
        """'Run Agent Judge' button visible."""
        self._setup_quality(page, "quality-all-pass.json")
        page.route(
            f"**/api/workspaces/{OPP_ID}/quality/judge",
            lambda route: route.fulfill(json={"status": "started"}, status=200),
        )
        self._open_quality_tab(page)
        btn = page.get_by_text("Run Agent Judge").first
        expect(btn).to_be_visible()


class TestQualityStrip:
    def _setup_with_strip(self, page, quality_fixture="quality-all-pass.json"):
        mock_investigate_workspace(page, OPP_ID, "workspace-orbiting.json", quality_fixture)
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_quality_strip_renders(self, page: Page):
        """#quality-strip shows gate pill counts."""
        self._setup_with_strip(page)
        strip = page.locator("#quality-strip")
        expect(strip).to_be_visible(timeout=5000)

    def test_quality_strip_click_switches_tab(self, page: Page):
        """Clicking strip switches to Quality tab."""
        self._setup_with_strip(page)
        strip = page.locator("#quality-strip")
        strip.click()
        content = page.locator("#quality-tab-content")
        expect(content).to_be_visible(timeout=5000)
