"""Filesystem watcher for workspace changes using watchfiles."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from watchfiles import awatch, Change


class WorkspaceWatcher:
    def __init__(self, workspaces_dir: Path):
        self.workspaces_dir = workspaces_dir
        self._subscribers: dict[str, list] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def subscribe(self, opp_id: str, callback):
        self._subscribers.setdefault(opp_id, []).append(callback)

    def unsubscribe(self, opp_id: str, callback):
        if opp_id in self._subscribers:
            try:
                self._subscribers[opp_id].remove(callback)
            except ValueError:
                pass

    async def start(self, opp_id: str):
        ws_dir = self.workspaces_dir / opp_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        self._tasks[opp_id] = asyncio.create_task(self._watch(opp_id, ws_dir))

    async def stop(self, opp_id: str):
        task = self._tasks.pop(opp_id, None)
        if task:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    async def _watch(self, opp_id: str, ws_dir: Path):
        async for changes in awatch(ws_dir, debounce=500):
            for change_type, path_str in changes:
                if change_type not in (Change.added, Change.modified):
                    continue
                path = Path(path_str)
                if not path.is_file():
                    continue
                event = self._build_event(ws_dir, path)
                for cb in self._subscribers.get(opp_id, []):
                    cb(event)

    def _build_event(self, ws_dir: Path, path: Path) -> dict:
        rel = path.relative_to(ws_dir)
        file_type = self._classify(rel)
        return {
            "event": "file_changed",
            "path": str(rel),
            "type": file_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _classify(rel: Path) -> str:
        parts = rel.parts
        if parts[0] == "contributions":
            return "contribution"
        if parts[0] == "reviews":
            return "review"
        if parts[0] == "artifacts":
            return "artifact"
        if parts[0] == "votes":
            return "vote"
        if rel.name == "synthesis.json":
            return "synthesis"
        if rel.name == "opportunity.json":
            return "opportunity"
        return "unknown"
