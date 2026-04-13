"""Launch router — generate and execute CLI commands for investigations."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/launch", tags=["launch"])


# ── Process management (must be before /{opp_id} routes) ──────


@router.get("/processes")
def list_processes(request: Request):
    launcher = request.app.state.launcher
    return {"processes": launcher.list_processes()}


class StopByKey(BaseModel):
    key: str


@router.post("/processes/stop")
def stop_by_key(body: StopByKey, request: Request):
    launcher = request.app.state.launcher
    return {"stopped": launcher.stop(body.key)}


# ── Per-workspace routes ──────────────────────────────────────


@router.post("/{opp_id}")
def generate_launch_command(opp_id: str, request: Request):
    bridge = request.app.state.cli_bridge
    try:
        command = bridge.generate_command(opp_id)
        return {"command": command, "opp_id": opp_id}
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{opp_id}/start")
def launch_start(opp_id: str, request: Request):
    bridge = request.app.state.cli_bridge
    launcher = request.app.state.launcher

    # Check if opportunity has a roster — if so, use parallel launch
    try:
        fn_cmds = bridge.generate_function_commands(opp_id)
        # Has roster — parallel Phase 2: server owns assembled → orbiting transition
        workspace_svc = request.app.state.workspace_svc
        workspace_svc.update_opportunity(opp_id, {"status": "orbiting"})
        results = launcher.launch_staggered(opp_id, fn_cmds)
        all_launched = all(results.values())
        return {
            "status": "launched" if all_launched else "partially_launched",
            "mode": "parallel",
            "opp_id": opp_id,
            "functions": results,
        }
    except ValueError:
        # No roster — single-agent Phase 0
        pass
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")

    try:
        command = bridge.generate_command(opp_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))

    launched = launcher.launch(opp_id, command)
    return {
        "status": "launched" if launched else "already_running",
        "opp_id": opp_id,
    }


@router.post("/{opp_id}/assemble")
def launch_assemble(opp_id: str, request: Request):
    bridge = request.app.state.cli_bridge
    launcher = request.app.state.launcher
    try:
        command = bridge.generate_assemble_command(opp_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    launched = launcher.launch(opp_id, command)
    return {
        "status": "launched" if launched else "already_running",
        "opp_id": opp_id,
    }


@router.post("/{opp_id}/dot-vote")
def launch_dot_vote(opp_id: str, request: Request):
    bridge = request.app.state.cli_bridge
    launcher = request.app.state.launcher
    quality_svc = request.app.state.quality_gate_svc
    blocking_mode = quality_svc._qg_config.get("blocking_mode", "warn")

    gate_warnings = []
    if blocking_mode != "off":
        try:
            can, blockers, gate_warnings = quality_svc.can_transition(opp_id, "scoring")
            if not can and blocking_mode == "block":
                raise HTTPException(422, f"Quality gates failed: {'; '.join(blockers)}")
        except ValueError:
            pass  # workspace not found — let downstream handler raise 404

    try:
        cmds = bridge.generate_dot_vote_commands(opp_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    results = launcher.launch_staggered(opp_id, cmds)
    all_launched = all(results.values())
    response = {
        "status": "launched" if all_launched else "partially_launched",
        "mode": "dot_vote",
        "opp_id": opp_id,
        "functions": results,
    }
    if blocking_mode == "warn":
        response["warnings"] = gate_warnings
    return response


@router.post("/{opp_id}/decision-brief")
def launch_decision_brief(opp_id: str, request: Request):
    bridge = request.app.state.cli_bridge
    launcher = request.app.state.launcher
    quality_svc = request.app.state.quality_gate_svc
    blocking_mode = quality_svc._qg_config.get("blocking_mode", "warn")

    gate_warnings = []
    if blocking_mode != "off":
        try:
            can, blockers, gate_warnings = quality_svc.can_transition(opp_id, "decision_brief")
            if not can and blocking_mode == "block":
                raise HTTPException(422, f"Quality gates failed: {'; '.join(blockers)}")
        except ValueError:
            pass  # workspace not found — let downstream handler raise 404

    try:
        command = bridge.generate_decision_brief_command(opp_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    launched = launcher.launch(opp_id, command)
    response = {
        "status": "launched" if launched else "already_running",
        "opp_id": opp_id,
    }
    if blocking_mode == "warn":
        response["warnings"] = gate_warnings
    return response


@router.get("/{opp_id}/status")
def launch_status(opp_id: str, request: Request, lines: int = 100, full: bool = False):
    launcher = request.app.state.launcher
    fn_outputs = launcher.get_function_outputs(opp_id)
    if fn_outputs:
        return {
            "running": launcher.is_any_function_running(opp_id),
            "function_outputs": fn_outputs,
            "stale": launcher.is_stale(opp_id),
        }
    output = (launcher.get_full_output(opp_id) if full
              else launcher.get_latest_output(opp_id, lines=min(lines, 200)))
    return {
        "running": launcher.is_running(opp_id),
        "output": output,
        "stale": launcher.is_stale(opp_id),
    }


@router.post("/{opp_id}/stop")
def launch_stop(opp_id: str, request: Request):
    launcher = request.app.state.launcher
    return {"stopped": launcher.stop(opp_id)}


@router.post("/{opp_id}/restart")
def launch_restart(opp_id: str, request: Request):
    launcher = request.app.state.launcher
    return {"restarted": launcher.restart(opp_id)}


@router.post("/{opp_id}/approve")
def launch_approve(opp_id: str, request: Request):
    launcher = request.app.state.launcher
    # Send approval to the agent's stdin to continue past plan mode
    sent = launcher.send_input(opp_id, "yes")
    return {"approved": sent}


class SendMessage(BaseModel):
    message: str


@router.post("/{opp_id}/send")
def launch_send(opp_id: str, body: SendMessage, request: Request):
    launcher = request.app.state.launcher
    if launcher.is_running(opp_id):
        return {"sent": launcher.send_input(opp_id, body.message)}
    # Process exited — resume conversation with --resume
    bridge = request.app.state.cli_bridge
    session_id = launcher.get_session_id(opp_id)
    cmd = bridge.generate_resume_command(body.message, session_id=session_id)
    launched = launcher.launch(opp_id, cmd)
    return {"sent": launched}
