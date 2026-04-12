"""Tests for judge agent service and CLI bridge judge command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from server.services.cli_bridge import CliBridge


class TestGenerateJudgeCommand:
    """Tests for CliBridge.generate_judge_command()."""

    def test_generates_valid_command(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "claude" in cmd
        assert "opp-20260405-120000" in cmd

    def test_command_includes_workspace_path(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "data/workspaces/opp-20260405-120000" in cmd

    def test_command_references_quality_output(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "quality/judge-evaluation.json" in cmd

    def test_command_mentions_rubrics(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        lower = cmd.lower()
        assert "contradictions" in lower
        assert "minority" in lower
        assert "evidence" in lower
        assert "risk" in lower
        assert "diversity" in lower

    def test_command_includes_stream_json(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "--output-format stream-json" in cmd
        assert "--verbose" in cmd

    def test_command_includes_scoping_rules(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "do NOT read other workspaces" in cmd or "Do NOT read other workspaces" in cmd

    def test_command_sets_accept_edits(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "--permission-mode acceptEdits" in cmd

    def test_raises_on_missing_workspace(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_judge_command("opp-nonexistent")

    def test_reads_opportunity_title(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "Test opportunity for server tests" in cmd

    def test_instructs_reading_contributions(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "contributions" in cmd.lower()

    def test_instructs_reading_synthesis(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "synthesis" in cmd.lower()

    def test_instructs_reading_votes(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_judge_command("opp-20260405-120000")
        assert "votes" in cmd.lower()


class TestJudgeAgentService:
    """Tests for JudgeAgentService."""

    def test_init(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        svc = JudgeAgentService(bridge, launcher)
        assert svc.cli_bridge is bridge
        assert svc.launcher is launcher

    def test_launch_judge_calls_launcher(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.launch.return_value = True
        svc = JudgeAgentService(bridge, launcher)
        result = svc.launch_judge("opp-20260405-120000")
        assert result is True
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
        result = svc.launch_judge("opp-20260405-120000")
        assert result is False

    def test_get_judge_status_not_running_no_results(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.is_running.return_value = False
        svc = JudgeAgentService(bridge, launcher)
        status = svc.get_judge_status("opp-20260405-120000")
        assert status["running"] is False
        assert status["results"] is None

    def test_get_judge_status_running(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.is_running.return_value = True
        svc = JudgeAgentService(bridge, launcher)
        status = svc.get_judge_status("opp-20260405-120000")
        assert status["running"] is True

    def test_get_judge_status_reads_results_file(self, tmp_project_root, tmp_data_dir):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        launcher.is_running.return_value = False

        # Create judge evaluation results
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
        assert status["results"] is not None
        assert status["results"]["overall_score"] == 0.7
        assert status["results"]["overall_passed"] is True
        assert len(status["results"]["rubrics"]) == 5

    def test_launch_judge_raises_on_missing_workspace(self, tmp_project_root):
        from server.services.judge_agent import JudgeAgentService
        bridge = CliBridge(tmp_project_root)
        launcher = MagicMock()
        svc = JudgeAgentService(bridge, launcher)
        with pytest.raises(FileNotFoundError):
            svc.launch_judge("opp-nonexistent")
