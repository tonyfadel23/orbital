"""Evidence router — gather evidence for investigations."""

import json
from enum import Enum

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/evidence", tags=["evidence"])


class GatherRequest(BaseModel):
    source_type: str
    query: str


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class EvidenceApproval(BaseModel):
    approval_status: ApprovalStatus


@router.post("/{opp_id}/gather")
def gather_evidence(opp_id: str, body: GatherRequest, request: Request):
    bridge = request.app.state.cli_bridge
    launcher = request.app.state.launcher
    try:
        command = bridge.generate_evidence_command(opp_id, body.source_type, body.query)
    except FileNotFoundError:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    except ValueError as e:
        raise HTTPException(400, str(e))

    key = f"ev:{opp_id}:{body.source_type}"
    launched = launcher.launch(key, command)
    return {
        "status": "launched" if launched else "already_running",
        "opp_id": opp_id,
        "source_type": body.source_type,
    }


@router.get("/{opp_id}/status")
def evidence_status(opp_id: str, request: Request):
    launcher = request.app.state.launcher
    prefix = f"ev:{opp_id}:"
    outputs = {}
    any_running = False
    for key, buf in launcher._output.items():
        if key.startswith(prefix):
            src = key[len(prefix):]
            outputs[src] = list(buf)[-20:]
    for key, proc in launcher._processes.items():
        if key.startswith(prefix) and proc.poll() is None:
            any_running = True
            break
    return {
        "running": any_running,
        "evidence_outputs": outputs,
    }


@router.patch("/{opp_id}/{evidence_id}")
def update_evidence(opp_id: str, evidence_id: str, body: EvidenceApproval, request: Request):
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    ev_dir = workspace_svc.data_dir / "workspaces" / opp_id / "evidence"
    if not ev_dir.exists():
        raise HTTPException(404, f"Evidence {evidence_id} not found")
    for f in ev_dir.glob("*.json"):
        data = json.loads(f.read_text())
        if data.get("id") == evidence_id:
            data["approval_status"] = body.approval_status.value
            f.write_text(json.dumps(data, indent=2))
            return data
    raise HTTPException(404, f"Evidence {evidence_id} not found")
