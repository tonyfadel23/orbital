"""AgentLauncher — subprocess management for Claude Code agents."""

import json
import subprocess
import threading
import time
from collections import deque
from pathlib import Path


class AgentLauncher:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._processes: dict[str, subprocess.Popen] = {}
        self._output: dict[str, deque] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._session_ids: dict[str, str] = {}
        self._last_output_time: dict[str, float] = {}

    def launch(self, opp_id: str, command: str) -> bool:
        if opp_id in self._processes and self._processes[opp_id].poll() is None:
            return False  # already running

        # Add separator if relaunching after exit (resume)
        if opp_id in self._output and len(self._output[opp_id]) > 0:
            self._output[opp_id].append("--- RESUMED ---")

        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(self.project_root),
        )
        self._processes[opp_id] = proc
        if opp_id not in self._output:
            self._output[opp_id] = deque(maxlen=200)

        thread = threading.Thread(
            target=self._read_output, args=(opp_id, proc), daemon=True
        )
        thread.start()
        self._threads[opp_id] = thread
        return True

    def is_running(self, opp_id: str) -> bool:
        proc = self._processes.get(opp_id)
        if proc is None:
            return False
        return proc.poll() is None

    def stop(self, opp_id: str) -> bool:
        proc = self._processes.get(opp_id)
        if proc is None:
            return False
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        return True

    def is_stale(self, opp_id: str, threshold_seconds: int = 300) -> bool:
        """Return True if process is running but hasn't produced output recently."""
        proc = self._processes.get(opp_id)
        if proc is None or proc.poll() is not None:
            return False
        last = self._last_output_time.get(opp_id)
        if last is None:
            return False
        return (time.time() - last) > threshold_seconds

    def restart(self, opp_id: str) -> bool:
        """Stop process, clear output buffer. Returns True if process existed."""
        proc = self._processes.get(opp_id)
        if proc is None:
            return False
        self.stop(opp_id)
        if opp_id in self._output:
            self._output[opp_id].clear()
        self._last_output_time.pop(opp_id, None)
        self._session_ids.pop(opp_id, None)
        return True

    def send_input(self, opp_id: str, text: str) -> bool:
        proc = self._processes.get(opp_id)
        if proc is None or proc.poll() is not None:
            return False
        try:
            proc.stdin.write(text + "\n")
            proc.stdin.flush()
            return True
        except (OSError, BrokenPipeError):
            return False

    def get_output(self, opp_id: str, lines: int = 20) -> list[str]:
        buf = self._output.get(opp_id)
        if not buf:
            return []
        return list(buf)[-lines:]

    def get_full_output(self, opp_id: str) -> list[str]:
        """Return all output across all turns (including resumed sessions)."""
        buf = self._output.get(opp_id)
        if not buf:
            return []
        return [line for line in buf if line != "--- RESUMED ---"]

    def get_latest_output(self, opp_id: str, lines: int = 200) -> list[str]:
        """Return output after the last --- RESUMED --- separator."""
        buf = self._output.get(opp_id)
        if not buf:
            return []
        all_lines = list(buf)
        # Find last separator
        last_sep = -1
        for i, line in enumerate(all_lines):
            if line == "--- RESUMED ---":
                last_sep = i
        if last_sep >= 0:
            return all_lines[last_sep + 1:][-lines:]
        return all_lines[-lines:]

    def get_session_id(self, opp_id: str) -> str | None:
        return self._session_ids.get(opp_id)

    def launch_parallel(self, opp_id: str, commands: dict[str, str]) -> dict[str, bool]:
        """Launch one subprocess per function using compound key opp_id:function."""
        results = {}
        for fn, cmd in commands.items():
            key = f"{opp_id}:{fn}"
            results[fn] = self.launch(key, cmd)
        return results

    def launch_staggered(self, opp_id: str, commands: dict[str, str],
                         delay_seconds: int = 15) -> dict[str, bool]:
        """Launch subprocesses with delay between each to avoid rate limits.

        Launches the first agent immediately and returns. Remaining agents
        are launched in a background thread with ``delay_seconds`` between each.
        The returned dict contains all function names mapped to ``True``
        (optimistic — failures are logged but not propagated).
        """
        items = list(commands.items())
        if not items:
            return {}

        # Launch the first agent synchronously so the caller knows it started
        first_fn, first_cmd = items[0]
        results = {fn: True for fn, _ in items}
        self.launch(f"{opp_id}:{first_fn}", first_cmd)

        # Launch the rest in a background thread with delays
        if len(items) > 1:
            remaining = items[1:]
            thread = threading.Thread(
                target=self._launch_remaining,
                args=(opp_id, remaining, delay_seconds),
                daemon=True,
            )
            thread.start()

        return results

    def _launch_remaining(self, opp_id: str, items: list[tuple[str, str]],
                          delay_seconds: int):
        """Background worker — launches agents with delays between each."""
        for fn, cmd in items:
            time.sleep(delay_seconds)
            self.launch(f"{opp_id}:{fn}", cmd)

    def is_any_function_running(self, opp_id: str) -> bool:
        """Return True if any function subprocess for this opp_id is still alive."""
        prefix = f"{opp_id}:"
        for key, proc in self._processes.items():
            if key.startswith(prefix) and proc.poll() is None:
                return True
        return False

    def get_function_outputs(self, opp_id: str) -> dict[str, list[str]]:
        """Return output per function for this opp_id."""
        prefix = f"{opp_id}:"
        result = {}
        for key, buf in self._output.items():
            if key.startswith(prefix):
                fn = key[len(prefix):]
                result[fn] = list(buf)
        return result

    def list_processes(self) -> list[dict]:
        """Return info about all tracked processes."""
        result = []
        for key, proc in self._processes.items():
            parts = key.split(":", 1)
            opp_id = parts[0]
            function = parts[1] if len(parts) > 1 else None
            result.append({
                "key": key,
                "opp_id": opp_id,
                "function": function,
                "running": proc.poll() is None,
                "exit_code": proc.returncode,
            })
        return result

    def _read_output(self, opp_id: str, proc: subprocess.Popen):
        try:
            for line in proc.stdout:
                stripped = line.rstrip("\n")
                self._output[opp_id].append(stripped)
                self._last_output_time[opp_id] = time.time()
                # Extract session_id from stream-json output
                if opp_id not in self._session_ids:
                    try:
                        data = json.loads(stripped)
                        if isinstance(data, dict) and "session_id" in data:
                            self._session_ids[opp_id] = data["session_id"]
                    except (json.JSONDecodeError, TypeError):
                        pass
        except (ValueError, OSError):
            pass
