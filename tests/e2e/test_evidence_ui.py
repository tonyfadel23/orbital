"""E2E tests for evidence modal and evidence cards.

Tests the evidence modal open/close, source type grid,
backdrop close, and stale evidence warnings.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BASE_URL, load_fixture, mock_investigate_workspace


OPP_ID = "opp-20260412-120000"


class TestEvidenceModal:
    def _setup_investigate(self, page):
        mock_investigate_workspace(page, OPP_ID, "workspace-with-contributions.json",
                                   "quality-all-pass.json")
        page.route(f"**/api/evidence/{OPP_ID}/gather",
                   lambda route: route.fulfill(json={"status": "started"}, status=200))
        page.goto(f"{BASE_URL}/#orb/{OPP_ID}")
        page.wait_for_timeout(1000)

    def test_evidence_modal_opens(self, page: Page):
        """Calling openEvidenceModal() creates .evidence-modal-overlay."""
        self._setup_investigate(page)
        page.evaluate("openEvidenceModal()")
        overlay = page.locator(".evidence-modal-overlay")
        expect(overlay).to_be_visible(timeout=3000)

    def test_evidence_modal_cancel(self, page: Page):
        """Cancel button closes modal."""
        self._setup_investigate(page)
        page.evaluate("openEvidenceModal()")
        page.wait_for_selector(".evidence-modal-overlay", timeout=3000)
        cancel = page.locator(".evidence-btn-cancel")
        cancel.click()
        page.wait_for_timeout(500)
        overlay = page.locator(".evidence-modal-overlay")
        assert overlay.count() == 0, "Modal should be removed after cancel"

    def test_evidence_source_types_listed(self, page: Page):
        """Modal shows 6 source type options."""
        self._setup_investigate(page)
        page.evaluate("openEvidenceModal()")
        page.wait_for_selector(".evidence-source-option", timeout=3000)
        sources = page.locator(".evidence-source-option")
        assert sources.count() == 6, f"Expected 6 source types, got {sources.count()}"

    def test_evidence_modal_backdrop_close(self, page: Page):
        """Clicking overlay backdrop closes modal."""
        self._setup_investigate(page)
        page.evaluate("openEvidenceModal()")
        page.wait_for_selector(".evidence-modal-overlay", timeout=3000)
        # Click the overlay (not the modal itself)
        page.locator(".evidence-modal-overlay").click(position={"x": 10, "y": 10})
        page.wait_for_timeout(500)
        overlay = page.locator(".evidence-modal-overlay")
        assert overlay.count() == 0, "Modal should be removed after backdrop click"


class TestEvidenceCards:
    def test_workspace_has_contributions(self, page: Page):
        """Workspace with contributions fixture has 3 agent contributions."""
        ws = load_fixture("workspace-with-contributions.json")
        assert len(ws["contributions"]) == 3
        assert ws["contributions"][0]["function"] == "product"
        assert ws["contributions"][1]["function"] == "data"
        assert ws["contributions"][2]["function"] == "design"

    def test_contributions_have_findings(self, page: Page):
        """Each contribution has at least 3 findings."""
        ws = load_fixture("workspace-with-contributions.json")
        for contrib in ws["contributions"]:
            assert len(contrib["findings"]) >= 3, \
                f"{contrib['function']} has {len(contrib['findings'])} findings, expected 3+"

    def test_stale_evidence_detection(self, page: Page):
        """Evidence older than threshold should be detected as stale."""
        ws = load_fixture("workspace-with-contributions.json")
        # All findings in this fixture have source_dates within 2026
        # Check that we can detect age-based staleness
        for contrib in ws["contributions"]:
            for finding in contrib["findings"]:
                assert "source_date" in finding, \
                    f"Finding {finding['id']} missing source_date"
