"""Workspace filesystem operations — list, read, write workspaces and context."""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkspaceService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.workspaces_dir = data_dir / "workspaces"
        self.context_dir = data_dir / "context"
        self.config_path = data_dir / "config.json"

        from server.services.context_reader import MarkdownContextReader
        product_lines_dir = self.context_dir / "product_lines"
        self._md_reader = MarkdownContextReader(product_lines_dir)

    def list_workspaces(self) -> list[dict]:
        if not self.workspaces_dir.exists():
            return []
        result = []
        for ws_dir in sorted(self.workspaces_dir.iterdir()):
            if not ws_dir.is_dir():
                continue
            opp_file = ws_dir / "opportunity.json"
            if not opp_file.exists():
                continue
            try:
                opp = json.loads(opp_file.read_text())
            except json.JSONDecodeError:
                logger.warning("Skipping workspace %s: corrupted opportunity.json", ws_dir.name)
                continue
            result.append({
                "id": opp.get("id", ws_dir.name),
                "title": opp.get("title", ""),
                "description": opp.get("description", ""),
                "status": opp.get("status", "unknown"),
                "type": opp.get("type", ""),
                "updated_at": opp.get("updated_at", ""),
                "roster_count": len(opp.get("roster") or []),
            })
        return result

    def get_opportunity(self, opp_id: str) -> dict | None:
        path = self.workspaces_dir / opp_id / "opportunity.json"
        if not path.exists():
            return None
        try:
            opp = json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted opportunity.json for %s", opp_id)
            return None
        if "assumptions" in opp and isinstance(opp["assumptions"], list):
            opp["assumptions"] = [
                self._normalize_assumption(a, i) for i, a in enumerate(opp["assumptions"])
            ]
        return opp

    @staticmethod
    def _normalize_assumption(a, index: int) -> dict:
        """Normalize assumption into {id, content, status, importance}.

        Handles three formats:
        - str: plain text from agent output
        - dict with 'content' key: already structured
        - dict with numeric keys: corrupted by JS spread on a string
        """
        if isinstance(a, str):
            return {"id": f"asm-{index + 1:03d}", "content": a, "status": "untested", "importance": "medium"}
        if isinstance(a, dict):
            if "content" in a:
                return a
            # Agents sometimes write {"text": "...", "status": "..."} instead of "content"
            if "text" in a:
                return {
                    "id": a.get("id", f"asm-{index + 1:03d}"),
                    "content": a["text"],
                    "status": a.get("status", "untested"),
                    "importance": a.get("importance", "medium"),
                    "confidence": a.get("confidence"),
                    "source": a.get("source"),
                }
            # Corrupted spread: {0:'T', 1:'h', ...} — reassemble
            if "0" in a:
                text = "".join(a[str(i)] for i in range(len(a)) if str(i) in a)
                return {"id": f"asm-{index + 1:03d}", "content": text, "status": "untested", "importance": "medium"}
        return {"id": f"asm-{index + 1:03d}", "content": str(a), "status": "untested", "importance": "medium"}

    def get_workspace_state(self, opp_id: str) -> dict | None:
        opp = self.get_opportunity(opp_id)
        if opp is None:
            return None
        return {
            "opportunity": opp,
            "contributions": self.list_contributions(opp_id),
            "reviews": self.list_reviews(opp_id),
            "artifacts": self.list_artifacts(opp_id),
            "synthesis": self._read_json_or_none(self.workspaces_dir / opp_id / "synthesis.json"),
            "evidence": self.list_evidence(opp_id),
        }

    def list_contributions(self, opp_id: str) -> list[dict]:
        return self._list_json_files(opp_id, "contributions")

    def list_reviews(self, opp_id: str) -> list[dict]:
        return self._list_json_files(opp_id, "reviews")

    def list_artifacts(self, opp_id: str) -> list[dict]:
        artifacts_dir = self.workspaces_dir / opp_id / "artifacts"
        if not artifacts_dir.exists():
            return []
        return [
            {"filename": f.name, "type": f.suffix.lstrip(".")}
            for f in sorted(artifacts_dir.iterdir())
            if f.is_file()
        ]

    def get_file(self, opp_id: str, subdir: str, filename: str) -> dict | None:
        path = self.workspaces_dir / opp_id / subdir / filename
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted JSON in %s/%s/%s", opp_id, subdir, filename)
            return None

    def get_votes(self, opp_id: str) -> list[dict]:
        """Read all vote JSON files from the workspace votes/ directory."""
        votes_dir = self.workspaces_dir / opp_id / "votes"
        if not votes_dir.exists():
            return []
        result = []
        for f in sorted(votes_dir.iterdir()):
            if f.suffix != ".json":
                continue
            try:
                result.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                logger.warning("Corrupted vote file %s/%s", opp_id, f.name)
        return result

    def get_decision_brief(self, opp_id: str) -> str | None:
        """Read the decision brief markdown artifact."""
        path = self.workspaces_dir / opp_id / "artifacts" / "decision-brief.md"
        if not path.exists():
            return None
        return path.read_text()

    def list_evidence(self, opp_id: str) -> list[dict]:
        ev_dir = self.workspaces_dir / opp_id / "evidence"
        if not ev_dir.exists():
            return []
        result = []
        for f in sorted(ev_dir.iterdir()):
            if f.suffix != ".json":
                continue
            try:
                result.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                logger.warning("Corrupted evidence file %s/%s", opp_id, f.name)
        return result

    def get_artifact(self, opp_id: str, filename: str) -> str | None:
        path = self.workspaces_dir / opp_id / "artifacts" / filename
        if not path.exists():
            return None
        return path.read_text()

    # --- Write operations ---

    def create_workspace(self, data: dict) -> dict:
        now = datetime.now(timezone.utc)
        opp_id = f"opp-{now.strftime('%Y%m%d-%H%M%S')}"
        ts = now.isoformat().replace("+00:00", "Z")

        opp = {
            "id": opp_id,
            "type": data["type"],
            "title": data["title"],
            "description": data.get("description", ""),
            "context_refs": data.get("context_refs", []),
            "assumptions": data.get("assumptions", []),
            "success_signals": data.get("success_signals", []),
            "kill_signals": data.get("kill_signals", []),
            "enabled_tools": data.get("enabled_tools", []),
            "status": "aligning",
            "decision": None,
            "created_at": ts,
            "updated_at": ts,
        }

        ws_dir = self.workspaces_dir / opp_id
        ws_dir.mkdir(parents=True)
        (ws_dir / "contributions").mkdir()
        (ws_dir / "reviews").mkdir()
        (ws_dir / "artifacts").mkdir()
        (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

        return opp

    _OPPORTUNITY_FIELDS = {
        "type", "title", "description", "context_refs", "assumptions",
        "success_signals", "kill_signals", "status", "decision",
        "roster", "refinement_history",
    }

    def update_opportunity(self, opp_id: str, updates: dict) -> dict | None:
        path = self.workspaces_dir / opp_id / "opportunity.json"
        if not path.exists():
            return None

        try:
            opp = json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted opportunity.json for %s, cannot update", opp_id)
            return None
        for key, value in updates.items():
            if key in self._OPPORTUNITY_FIELDS:
                opp[key] = value
        opp["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        path.write_text(json.dumps(opp, indent=2))
        return opp

    def delete_workspace(self, opp_id: str) -> bool:
        ws_dir = self.workspaces_dir / opp_id
        if not ws_dir.exists():
            return False
        shutil.rmtree(ws_dir)
        return True

    # --- Context layers ---

    def list_context_layers(self, layer_type: str | None = None) -> list[dict]:
        return self._md_reader.list_layers(layer_type=layer_type)

    def get_context_layer(self, layer_type: str, name: str) -> dict | None:
        return self._md_reader.get_layer(layer_type, name)

    # --- Config ---

    def get_config(self) -> dict:
        try:
            return json.loads(self.config_path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted config.json at %s", self.config_path)
            return {}

    # --- Quality ---

    def get_quality_results(self, opp_id: str) -> dict | None:
        path = self.workspaces_dir / opp_id / "quality" / "evaluation.json"
        return self._read_json_or_none(path)

    def save_quality_results(self, opp_id: str, results: dict) -> None:
        quality_dir = self.workspaces_dir / opp_id / "quality"
        quality_dir.mkdir(parents=True, exist_ok=True)
        (quality_dir / "evaluation.json").write_text(json.dumps(results, indent=2))

    # --- Helpers ---

    def _list_json_files(self, opp_id: str, subdir: str) -> list[dict]:
        d = self.workspaces_dir / opp_id / subdir
        if not d.exists():
            return []
        return [
            {"filename": f.name}
            for f in sorted(d.iterdir())
            if f.suffix == ".json"
        ]

    def _read_json_or_none(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted JSON at %s", path)
            return None
