"""Judge agent service — Layer 3 quality evaluation via agent subprocess."""

import json
from pathlib import Path

from server.services.cli_bridge import CliBridge
from server.services.launcher import AgentLauncher


class JudgeAgentService:
    def __init__(self, cli_bridge: CliBridge, launcher: AgentLauncher):
        self.cli_bridge = cli_bridge
        self.launcher = launcher

    def launch_judge(self, opp_id: str) -> bool:
        """Spawn judge agent subprocess. Returns True if launched, False if already running."""
        command = self.cli_bridge.generate_judge_command(opp_id)
        key = f"judge:{opp_id}"
        return self.launcher.launch(key, command)

    def get_judge_status(self, opp_id: str) -> dict:
        """Check judge subprocess status and read results if available."""
        key = f"judge:{opp_id}"
        running = self.launcher.is_running(key)

        results = None
        results_path = (
            self.cli_bridge.workspaces_dir / opp_id / "quality" / "judge-evaluation.json"
        )
        if results_path.exists():
            try:
                results = json.loads(results_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        return {"running": running, "results": results}
