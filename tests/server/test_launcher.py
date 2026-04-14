"""Tests for AgentLauncher — subprocess management for Claude agents."""

import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from server.services.launcher import AgentLauncher


class TestAgentLauncher:
    def test_launch_starts_process(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None  # still running
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            result = launcher.launch("opp-001", "echo hello")
            assert result is True
            mock_popen.assert_called_once()

    def test_launch_prevents_duplicate(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo hello")
            result = launcher.launch("opp-001", "echo hello again")
            assert result is False
            assert mock_popen.call_count == 1

    def test_is_running_true(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo hello")
            assert launcher.is_running("opp-001") is True

    def test_is_running_false_not_launched(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        assert launcher.is_running("opp-001") is False

    def test_is_running_false_after_exit(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # exited
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo hello")
            assert launcher.is_running("opp-001") is False

    def test_stop_kills_process(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo hello")
            result = launcher.stop("opp-001")
            assert result is True
            mock_proc.terminate.assert_called_once()

    def test_stop_nonexistent(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        assert launcher.stop("opp-999") is False

    def test_get_output_empty(self, tmp_path):
        launcher = AgentLauncher(tmp_path)
        assert launcher.get_output("opp-001") == []

    def test_get_output_captures_lines(self, tmp_path):
        """Integration test: real subprocess writes to stdout."""
        launcher = AgentLauncher(tmp_path)
        # Use a real command that produces output
        launcher.launch("opp-001", "echo 'line1' && echo 'line2'")
        # Give the reader thread time to capture
        time.sleep(0.5)
        output = launcher.get_output("opp-001")
        assert len(output) >= 1
        assert any("line1" in l for l in output)
        launcher.stop("opp-001")

    def test_send_input_to_running_process(self, tmp_path):
        """send_input writes text to running process stdin."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "cat")
            result = launcher.send_input("opp-001", "hello world")
            assert result is True
            mock_proc.stdin.write.assert_called_once_with("hello world\n")
            mock_proc.stdin.flush.assert_called_once()

    def test_send_input_not_running(self, tmp_path):
        """send_input returns False for non-existent process."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.send_input("opp-999", "hello") is False

    def test_send_input_exited_process(self, tmp_path):
        """send_input returns False for exited process."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # exited
            mock_proc.stdout.readline.return_value = ""
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo done")
            result = launcher.send_input("opp-001", "hello")
            assert result is False

    def test_launch_preserves_output_on_relaunch(self, tmp_path):
        """Output deque should not be reset when relaunching after exit."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # exited
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo first")
            launcher._output["opp-001"].append("line1")
            launcher._output["opp-001"].append("line2")

            # Re-launch after exit — output should be preserved
            launcher.launch("opp-001", "echo second")
            output = list(launcher._output["opp-001"])
            assert "line1" in output
            assert "line2" in output

    def test_session_id_extraction(self, tmp_path):
        """Launcher extracts session_id from stream-json output."""
        import json
        launcher = AgentLauncher(tmp_path)
        # Simulate stream-json output with session_id
        session_line = json.dumps({"type": "system", "session_id": "abc-123-def"})
        launcher.launch(
            "opp-001",
            f"echo '{session_line}'"
        )
        time.sleep(0.5)
        assert launcher.get_session_id("opp-001") == "abc-123-def"

    def test_session_id_none_when_not_launched(self, tmp_path):
        """get_session_id returns None for unknown opp_id."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.get_session_id("opp-999") is None

    def test_relaunch_adds_separator(self, tmp_path):
        """Relaunching after exit adds a --- RESUMED --- separator."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # exited
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo first")
            launcher._output["opp-001"].append("old output")

            # Re-launch after exit
            launcher.launch("opp-001", "echo second")
            output = list(launcher._output["opp-001"])
            assert "--- RESUMED ---" in output

    def test_get_latest_output(self, tmp_path):
        """get_latest_output returns only content after last separator."""
        launcher = AgentLauncher(tmp_path)
        launcher._output["opp-001"] = deque(maxlen=200)
        launcher._output["opp-001"].append("old line 1")
        launcher._output["opp-001"].append("old line 2")
        launcher._output["opp-001"].append("--- RESUMED ---")
        launcher._output["opp-001"].append("new line 1")
        launcher._output["opp-001"].append("new line 2")

        latest = launcher.get_latest_output("opp-001")
        assert latest == ["new line 1", "new line 2"]

    def test_get_latest_output_no_separator(self, tmp_path):
        """get_latest_output returns all content when no separator exists."""
        launcher = AgentLauncher(tmp_path)
        launcher._output["opp-001"] = deque(maxlen=200)
        launcher._output["opp-001"].append("line 1")
        launcher._output["opp-001"].append("line 2")

        latest = launcher.get_latest_output("opp-001")
        assert latest == ["line 1", "line 2"]

    def test_get_latest_output_empty(self, tmp_path):
        """get_latest_output returns empty list for unknown opp_id."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.get_latest_output("opp-999") == []

    def test_launch_parallel_starts_all(self, tmp_path):
        """launch_parallel starts one process per function."""
        launcher = AgentLauncher(tmp_path)
        cmds = {
            "product": "echo product",
            "data": "echo data",
            "design": "echo design",
        }
        results = launcher.launch_parallel("opp-001", cmds)
        assert results == {"product": True, "data": True, "design": True}

    def test_launch_parallel_uses_compound_key(self, tmp_path):
        """Each function process is tracked under opp_id:function key."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p", "data": "echo d"}
        launcher.launch_parallel("opp-001", cmds)
        assert "opp-001:product" in launcher._processes
        assert "opp-001:data" in launcher._processes

    def test_is_any_function_running(self, tmp_path):
        """is_any_function_running returns True if any function process is alive."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None  # running
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc
            launcher.launch_parallel("opp-001", {"product": "echo p"})
            assert launcher.is_any_function_running("opp-001") is True

    def test_is_any_function_running_false_when_all_done(self, tmp_path):
        """is_any_function_running returns False if all function processes exited."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0  # exited
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc
            launcher.launch_parallel("opp-001", {"product": "echo p"})
            assert launcher.is_any_function_running("opp-001") is False

    def test_get_function_outputs(self, tmp_path):
        """get_function_outputs returns output per function."""
        launcher = AgentLauncher(tmp_path)
        launcher._output["opp-001:product"] = deque(["line1"])
        launcher._output["opp-001:data"] = deque(["line2"])
        outputs = launcher.get_function_outputs("opp-001")
        assert "product" in outputs
        assert "data" in outputs
        assert outputs["product"] == ["line1"]
        assert outputs["data"] == ["line2"]

    def test_launch_staggered_returns_immediately(self, tmp_path):
        """launch_staggered launches first agent synchronously, returns immediately."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p", "data": "echo d", "design": "echo ds"}
        launch_event = threading.Event()
        original_launch = launcher.launch

        def blocking_launch(key, cmd):
            result = original_launch(key, cmd)
            if "product" not in key:
                launch_event.wait(timeout=2)  # Block remaining agents
            return result

        with patch.object(launcher, "launch", side_effect=blocking_launch):
            results = launcher.launch_staggered("opp-001", cmds, delay_seconds=0)
        # Returns immediately with optimistic results, even though remaining agents are blocked
        assert results == {"product": True, "data": True, "design": True}
        launch_event.set()  # Unblock background thread

    def test_launch_staggered_background_launches_remaining(self, tmp_path):
        """launch_staggered spawns a background thread for remaining agents."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p", "data": "echo d", "design": "echo ds"}
        calls = []
        def fake_launch(key, cmd):
            calls.append(key)
            return True
        with patch.object(launcher, "launch", side_effect=fake_launch):
            with patch("server.services.launcher.time.sleep"):
                launcher.launch_staggered("opp-001", cmds, delay_seconds=0)
        # Give background thread time to finish
        time.sleep(0.2)
        assert "opp-001:product" in calls
        assert "opp-001:data" in calls
        assert "opp-001:design" in calls

    def test_launch_staggered_background_delays(self, tmp_path):
        """Background thread sleeps before each remaining agent."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p", "data": "echo d", "design": "echo ds"}
        sleep_calls = []
        real_sleep = time.sleep

        def tracking_sleep(seconds):
            sleep_calls.append(seconds)

        with patch.object(launcher, "launch", return_value=True):
            with patch("server.services.launcher.time.sleep", side_effect=tracking_sleep):
                launcher.launch_staggered("opp-001", cmds, delay_seconds=15)
                real_sleep(0.2)  # Wait for background thread
        # Background thread sleeps once before each remaining agent (2 agents)
        assert sleep_calls == [15, 15]

    def test_launch_staggered_uses_compound_key(self, tmp_path):
        """launch_staggered passes compound key (opp_id:function) to launch()."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p", "data": "echo d"}
        calls = []
        def fake_launch(key, cmd):
            calls.append(key)
            return True
        with patch.object(launcher, "launch", side_effect=fake_launch):
            with patch("server.services.launcher.time.sleep"):
                launcher.launch_staggered("opp-001", cmds, delay_seconds=0)
        time.sleep(0.2)
        assert "opp-001:product" in calls
        assert "opp-001:data" in calls

    def test_launch_staggered_single_agent_no_thread(self, tmp_path):
        """launch_staggered with one agent launches synchronously, no background thread."""
        launcher = AgentLauncher(tmp_path)
        cmds = {"product": "echo p"}
        with patch.object(launcher, "launch", return_value=True) as mock_launch:
            with patch("server.services.launcher.time.sleep") as mock_sleep:
                results = launcher.launch_staggered("opp-001", cmds)
        assert results == {"product": True}
        mock_launch.assert_called_once()
        mock_sleep.assert_not_called()

    def test_launch_staggered_empty_commands(self, tmp_path):
        """launch_staggered returns empty dict for empty commands."""
        launcher = AgentLauncher(tmp_path)
        results = launcher.launch_staggered("opp-001", {})
        assert results == {}

    def test_list_processes_empty(self, tmp_path):
        """list_processes returns empty list when nothing tracked."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.list_processes() == []

    def test_list_processes_running(self, tmp_path):
        """list_processes returns running process with correct structure."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.returncode = None
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo hello")
            procs = launcher.list_processes()
            assert len(procs) == 1
            assert procs[0]["key"] == "opp-001"
            assert procs[0]["opp_id"] == "opp-001"
            assert procs[0]["function"] is None
            assert procs[0]["running"] is True
            assert procs[0]["exit_code"] is None

    def test_list_processes_compound_key(self, tmp_path):
        """list_processes extracts function from compound key."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.returncode = None
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001:product", "echo hello")
            procs = launcher.list_processes()
            assert len(procs) == 1
            assert procs[0]["key"] == "opp-001:product"
            assert procs[0]["opp_id"] == "opp-001"
            assert procs[0]["function"] == "product"

    def test_list_processes_exited(self, tmp_path):
        """list_processes shows exited process with exit_code."""
        launcher = AgentLauncher(tmp_path)
        with patch("server.services.launcher.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 0
            mock_proc.returncode = 0
            mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
            mock_popen.return_value = mock_proc

            launcher.launch("opp-001", "echo done")
            procs = launcher.list_processes()
            assert len(procs) == 1
            assert procs[0]["running"] is False
            assert procs[0]["exit_code"] == 0

    def test_list_processes_mixed(self, tmp_path):
        """list_processes returns both running and exited processes."""
        launcher = AgentLauncher(tmp_path)
        running = MagicMock()
        running.poll.return_value = None
        running.returncode = None
        exited = MagicMock()
        exited.poll.return_value = 0
        exited.returncode = 0
        launcher._processes["opp-001"] = running
        launcher._processes["opp-002:data"] = exited
        procs = launcher.list_processes()
        assert len(procs) == 2
        keys = {p["key"] for p in procs}
        assert keys == {"opp-001", "opp-002:data"}


class TestLauncherResilience:
    """Tests for SIGKILL fallback, stale detection, and restart."""

    def test_stop_sends_sigkill_if_terminate_fails(self, tmp_path):
        """stop() should SIGKILL after terminate if process doesn't exit."""
        launcher = AgentLauncher(tmp_path)
        mock_proc = MagicMock()
        # Process stays alive after terminate (poll returns None), then dies after kill
        mock_proc.poll.return_value = None
        mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
        launcher._processes["opp-001"] = mock_proc

        launcher.stop("opp-001")
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()

    def test_stop_no_sigkill_if_terminate_works(self, tmp_path):
        """stop() should not SIGKILL if terminate succeeds within timeout."""
        launcher = AgentLauncher(tmp_path)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.wait.return_value = 0  # exits cleanly after terminate
        launcher._processes["opp-001"] = mock_proc

        launcher.stop("opp-001")
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_not_called()

    def test_last_output_time_tracked(self, tmp_path):
        """_last_output_time is updated when output is read."""
        launcher = AgentLauncher(tmp_path)
        launcher.launch("opp-001", "echo hello")
        time.sleep(0.5)
        assert "opp-001" in launcher._last_output_time
        assert launcher._last_output_time["opp-001"] > 0
        launcher.stop("opp-001")

    def test_is_stale_true_when_no_output(self, tmp_path):
        """is_stale returns True when process hasn't produced output recently."""
        launcher = AgentLauncher(tmp_path)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        launcher._processes["opp-001"] = mock_proc
        # Set last output time to 10 minutes ago
        launcher._last_output_time["opp-001"] = time.time() - 600

        assert launcher.is_stale("opp-001", threshold_seconds=300) is True

    def test_is_stale_false_when_recent_output(self, tmp_path):
        """is_stale returns False when process produced output recently."""
        launcher = AgentLauncher(tmp_path)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # still running
        launcher._processes["opp-001"] = mock_proc
        launcher._last_output_time["opp-001"] = time.time()  # just now

        assert launcher.is_stale("opp-001", threshold_seconds=300) is False

    def test_is_stale_false_when_not_running(self, tmp_path):
        """is_stale returns False for non-running processes."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.is_stale("opp-999") is False

    def test_restart_kills_and_clears(self, tmp_path):
        """restart() stops the process and clears output buffer."""
        launcher = AgentLauncher(tmp_path)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.wait.return_value = 0
        launcher._processes["opp-001"] = mock_proc
        launcher._output["opp-001"] = deque(["old line 1", "old line 2"])
        launcher._last_output_time["opp-001"] = time.time() - 600

        result = launcher.restart("opp-001")
        assert result is True
        mock_proc.terminate.assert_called_once()
        assert len(launcher._output["opp-001"]) == 0

    def test_restart_nonexistent(self, tmp_path):
        """restart() returns False for unknown opp_id."""
        launcher = AgentLauncher(tmp_path)
        assert launcher.restart("opp-999") is False
