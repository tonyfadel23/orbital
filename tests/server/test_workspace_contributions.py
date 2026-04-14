"""Tests for enriched list_contributions() returning findings inline."""

import json
from pathlib import Path

import pytest

from server.services.workspace import WorkspaceService


OPP_ID = "opp-20260405-120000"


class TestListContributions:
    def test_returns_agent_function_and_findings(self, tmp_data_dir):
        """list_contributions() should include agent_function and findings from JSON."""
        svc = WorkspaceService(tmp_data_dir)
        contribs = svc.list_contributions(OPP_ID)

        assert len(contribs) == 1
        c = contribs[0]
        assert c["filename"] == "data-round-1.json"
        assert c["agent_function"] == "data"
        assert isinstance(c["findings"], list)
        assert len(c["findings"]) == 1
        assert c["findings"][0]["type"] == "measurement"

    def test_empty_findings_when_none_present(self, tmp_data_dir):
        """Contribution with no findings key returns empty list."""
        contrib_dir = tmp_data_dir / "workspaces" / OPP_ID / "contributions"
        no_findings = {"agent_function": "design", "round": 1}
        (contrib_dir / "design-round-1.json").write_text(json.dumps(no_findings))

        svc = WorkspaceService(tmp_data_dir)
        contribs = svc.list_contributions(OPP_ID)

        design = [c for c in contribs if c["agent_function"] == "design"]
        assert len(design) == 1
        assert design[0]["findings"] == []

    def test_skips_corrupted_json(self, tmp_data_dir):
        """Corrupted JSON files are skipped gracefully."""
        contrib_dir = tmp_data_dir / "workspaces" / OPP_ID / "contributions"
        (contrib_dir / "bad-round-1.json").write_text("{corrupted json!!")

        svc = WorkspaceService(tmp_data_dir)
        contribs = svc.list_contributions(OPP_ID)

        filenames = [c["filename"] for c in contribs]
        assert "bad-round-1.json" not in filenames
        assert "data-round-1.json" in filenames

    def test_empty_when_no_contributions_dir(self, tmp_data_dir):
        """Returns empty list when contributions directory doesn't exist."""
        svc = WorkspaceService(tmp_data_dir)
        assert svc.list_contributions("nonexistent-opp") == []
