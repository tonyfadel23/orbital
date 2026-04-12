"""Quality router — evaluate and manage quality gates."""

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


router = APIRouter(tags=["quality"])


# --- Per-workspace quality endpoints ---


@router.get("/api/workspaces/{opp_id}/quality")
def get_quality_report(opp_id: str, request: Request):
    quality_svc = request.app.state.quality_gate_svc
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")

    report = quality_svc.evaluate_all(opp_id)
    report_dict = report.to_dict()

    return {
        "opp_id": opp_id,
        "timestamp": report_dict["timestamp"],
        "layer_1": {
            "overall_passed": report_dict["overall_passed"],
            "overall_score": report_dict["overall_score"],
            "gates": report_dict["gates"],
        },
        "layer_2": None,
        "layer_3": None,
    }


@router.get("/api/workspaces/{opp_id}/quality/gates")
def get_quality_gates(opp_id: str, request: Request):
    quality_svc = request.app.state.quality_gate_svc
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")

    report = quality_svc.evaluate_all(opp_id)
    report_dict = report.to_dict()
    return {
        "overall_passed": report_dict["overall_passed"],
        "overall_score": report_dict["overall_score"],
        "gates": report_dict["gates"],
    }


@router.post("/api/workspaces/{opp_id}/quality/evaluate")
async def evaluate_layer2(opp_id: str, request: Request):
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    llm_judge_svc = getattr(request.app.state, "llm_judge_svc", None)
    if llm_judge_svc is None:
        raise HTTPException(501, "LLM Judge service not configured")
    report = await llm_judge_svc.evaluate_all(opp_id)
    return report.to_dict()


@router.post("/api/workspaces/{opp_id}/quality/judge")
def launch_judge(opp_id: str, request: Request):
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    judge_svc = request.app.state.judge_agent_svc
    try:
        launched = judge_svc.launch_judge(opp_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return {"launched": launched, "opp_id": opp_id}


@router.get("/api/workspaces/{opp_id}/quality/judge")
def get_judge_status(opp_id: str, request: Request):
    workspace_svc = request.app.state.workspace_svc
    opp = workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    judge_svc = request.app.state.judge_agent_svc
    return judge_svc.get_judge_status(opp_id)


# --- Quality config endpoints ---


class QualityConfigUpdate(BaseModel):
    enabled: bool | None = None
    blocking_mode: str | None = None
    layer_1: dict | None = None


@router.get("/api/quality/config")
def get_quality_config(request: Request):
    workspace_svc = request.app.state.workspace_svc
    config = workspace_svc.get_config()
    return config.get("quality_gates", {})


@router.patch("/api/quality/config")
def patch_quality_config(body: QualityConfigUpdate, request: Request):
    workspace_svc = request.app.state.workspace_svc
    config = workspace_svc.get_config()
    qg = config.get("quality_gates", {})

    if body.enabled is not None:
        qg["enabled"] = body.enabled
    if body.blocking_mode is not None:
        qg["blocking_mode"] = body.blocking_mode
    if body.layer_1 is not None:
        existing_l1 = qg.get("layer_1", {})
        for gate_name, gate_updates in body.layer_1.items():
            if gate_name in existing_l1 and isinstance(gate_updates, dict):
                existing_l1[gate_name].update(gate_updates)
            else:
                existing_l1[gate_name] = gate_updates
        qg["layer_1"] = existing_l1

    config["quality_gates"] = qg
    workspace_svc.config_path.write_text(json.dumps(config, indent=2))

    # Rebuild the service config
    request.app.state.quality_gate_svc._qg_config = qg
    request.app.state.quality_gate_svc._l1 = qg.get("layer_1", {})

    return qg
