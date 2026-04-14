"""FastAPI application factory for Orbital server."""

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from server.config import get_project_root, get_data_dir
from server.services.workspace import WorkspaceService
from server.services.validator import SchemaValidator
from server.services.cli_bridge import CliBridge
from server.services.launcher import AgentLauncher
from server.services.watcher import WorkspaceWatcher
from server.services.quality_gates import QualityGateService
from server.services.judge_agent import JudgeAgentService
from server.services.llm_judge import LLMJudgeService
from server.ws.handler import ConnectionManager
from server.routers import workspaces, context, catalog, launch, evidence
from server.routers import quality

logger = logging.getLogger(__name__)


def create_app(root: Path | None = None) -> FastAPI:
    root = root or get_project_root()
    app = FastAPI(title="Orbital", version="0.2.0")

    # Services
    app.state.workspace_svc = WorkspaceService(get_data_dir(root))
    app.state.validator = SchemaValidator(root / "schemas")
    app.state.cli_bridge = CliBridge(root)
    app.state.launcher = AgentLauncher(root)
    app.state.watcher = WorkspaceWatcher(get_data_dir(root) / "workspaces")
    app.state.ws_manager = ConnectionManager()
    app.state.root = root
    config = app.state.workspace_svc.get_config()
    app.state.quality_gate_svc = QualityGateService(app.state.workspace_svc, config)
    app.state.judge_agent_svc = JudgeAgentService(app.state.cli_bridge, app.state.launcher)
    import os
    app.state.llm_judge_svc = LLMJudgeService(
        app.state.workspace_svc, config, api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    # Routers
    app.include_router(workspaces.router)
    app.include_router(context.router)
    app.include_router(catalog.router)
    app.include_router(launch.router)
    app.include_router(evidence.router)
    app.include_router(quality.router)

    # WebSocket endpoint
    @app.websocket("/ws/workspace/{opp_id}")
    async def workspace_ws(websocket: WebSocket, opp_id: str):
        manager = app.state.ws_manager
        watcher = app.state.watcher
        loop = asyncio.get_event_loop()

        def on_change(event):
            loop.call_soon_threadsafe(
                asyncio.ensure_future, manager.broadcast(opp_id, event)
            )

        await manager.connect(opp_id, websocket)
        watcher.subscribe(opp_id, on_change)
        # Start watcher if this is the first connection for this opp_id
        if opp_id not in watcher._tasks:
            await watcher.start(opp_id)

        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(opp_id, websocket)
            watcher.unsubscribe(opp_id, on_change)
            if not manager._connections.get(opp_id):
                await watcher.stop(opp_id)
        except Exception as exc:
            logger.error("WebSocket error for %s: %s", opp_id, exc)
            manager.disconnect(opp_id, websocket)
            watcher.unsubscribe(opp_id, on_change)
            if not manager._connections.get(opp_id):
                await watcher.stop(opp_id)

    # Heartbeat lifecycle
    @app.on_event("startup")
    async def start_heartbeat():
        await app.state.ws_manager.start_heartbeat(interval=15.0)

    @app.on_event("shutdown")
    async def stop_heartbeat():
        await app.state.ws_manager.stop_heartbeat()

    # Static files (frontend)
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
