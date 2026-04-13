"""Tests for judge agent service and CLI bridge judge command."""

import json
from unittest.mock import MagicMock

import pytest

from server.services.cli_bridge import CliBridge


class TestGenerateJudgeCommand:
    """Tests for CliBridge.generate_judge_command()."""

    def test_generates_complete_command(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        # Core command structure
        assert "claude" in cmd
        assert "opp-20260405-120000" in cmd
        assert "data/workspaces/opp-20260405-120000" in cmd
        assert "--output-format stream-json" in cmd
        assert "--verbose" in cmd
        assert "--permission-mode acceptEdits" in cmd
        # References opportunity context
        assert "Test opportunity for server tests" in cmd
        # Output target
        assert "quality/judge-evaluation.json" in cmd

    def test_command_covers_all_rubrics_and_inputs(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        lower = cmd.lower()
        # All 5 rubrics mentioned
        for rubric in ("contradictions", "minority", "evidence", "risk", "diversity"):
            assert rubric in lower
        # Reads the right inputs
        for input_type in ("contributions", "synthesis", "votes"):
            assert input_type in lower
        # Scoping rule
        assert "do not read other workspaces" in lower

    def test_raises_on_missing_workspace(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_judge_command("opp-nonexistent")


class TestJudgeAgentService:
    """Tests for JudgeAgentService."""

    def test_launch_judge(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.launch.return_value = True
        svc = JudgeAgentService(bridge, launcher)
        assert svc.launch_judge("opp-20260405-120000") is True
        launcher.launch.assert_called_once()
        key, cmd = launcher.launch.call_args[0]
        assert "judge" in key
        assert "opp-20260405-120000" in key

    def test_launch_judge_already_running(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.launch.return_value = False
        svc = JudgeAgentService(bridge, launcher)
        assert svc.launch_judge("opp-20260405-120000") is False

    def test_launch_judge_raises_on_missing_workspace(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        svc = JudgeAgentService(bridge, launcher)
        with pytest.raises(FileNotFoundError):
            svc.launch_judge("opp-nonexistent")

    def test_get_judge_status_not_running(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.is_running.return_value = False
        svc = JudgeAgentService(bridge, launcher)
        status = svc.get_judge_status("opp-20260405-120000")
        assert status["running"] is False
        assert status["results"] is None

    def test_get_judge_status_reads_results(self, tmp_project_root, tmp_data_dir):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.is_running.return_value = False

        quality_dir = tmp_data_dir / "workspaces" / "opp-20260405-120000" / "quality"
        quality_dir.mkdir(parents=True)
        results = {
            "opp_id": "opp-20260405-120000",
            "rubrics": {
                "contradictions_surfaced": {"score": 0.8, "rationale": "Good"},
                "minority_viewpoints": {"score": 0.6, "rationale": "Fair"},
                "evidence_based_recommendation": {"score": 0.9, "rationale": "Strong"},
                "risk_weighting": {"score": 0.7, "rationale": "Acceptable"},
                "solution_diversity": {"score": 0.5, "rationale": "Needs work"}
            },
            "overall_score": 0.7,
            "overall_passed": True,
            "timestamp": "2026-04-12T15:00:00Z"
        }
        (quality_dir / "judge-evaluation.json").write_text(json.dumps(results))

        svc = JudgeAgentService(bridge, launcher)
        status = svc.get_judge_status("opp-20260405-120000")
        assert status["running"] is False
        assert status["results"]["overall_score"] == 0.7
        assert status["results"]["overall_passed"] is True
        assert len(status["results"]["rubrics"]) == 5
