"""Workspace REST endpoints — read and write operations."""

import re

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, HTMLResponse

from server.services.strategy_doc import StrategyDocBuilder


class CreateWorkspaceRequest(BaseModel):
    type: str
    title: str = Field(min_length=10)
    description: str = ""
    context_refs: list[str] = []
    assumptions: list[dict] = []
    success_signals: list[str] = []
    kill_signals: list[str] = []
    enabled_tools: list[str] = []


class UpdateOpportunityRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    type: str | None = None
    status: str | None = None
    context_refs: list[str] | None = None
    assumptions: list[dict] | None = None
    success_signals: list[str] | None = None
    kill_signals: list[str] | None = None
    roster: list[dict] | None = None
    refinement_history: list[dict] | None = None


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("")
def list_workspaces(request: Request):
    return request.app.state.workspace_svc.list_workspaces()


@router.post("", status_code=201)
def create_workspace(body: CreateWorkspaceRequest, request: Request):
    opp = request.app.state.workspace_svc.create_workspace(body.model_dump())
    return opp


@router.delete("/{opp_id}")
def delete_workspace(opp_id: str, request: Request):
    deleted = request.app.state.workspace_svc.delete_workspace(opp_id)
    if not deleted:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    return {"deleted": opp_id}


@router.get("/{opp_id}")
def get_workspace(opp_id: str, request: Request):
    state = request.app.state.workspace_svc.get_workspace_state(opp_id)
    if state is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    return state


@router.get("/{opp_id}/opportunity")
def get_opportunity(opp_id: str, request: Request):
    opp = request.app.state.workspace_svc.get_opportunity(opp_id)
    if opp is None:
        raise HTTPException(404, f"Opportunity {opp_id} not found")
    return opp


@router.patch("/{opp_id}/opportunity")
def update_opportunity(opp_id: str, body: UpdateOpportunityRequest, request: Request):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    opp = request.app.state.workspace_svc.update_opportunity(opp_id, updates)
    if opp is None:
        raise HTTPException(404, f"Opportunity {opp_id} not found")
    return opp


@router.get("/{opp_id}/contributions")
def list_contributions(opp_id: str, request: Request):
    return request.app.state.workspace_svc.list_contributions(opp_id)


@router.get("/{opp_id}/contributions/{filename}")
def get_contribution(opp_id: str, filename: str, request: Request):
    data = request.app.state.workspace_svc.get_file(opp_id, "contributions", filename)
    if data is None:
        raise HTTPException(404, f"Contribution {filename} not found")
    return data


@router.get("/{opp_id}/reviews")
def list_reviews(opp_id: str, request: Request):
    return request.app.state.workspace_svc.list_reviews(opp_id)


@router.get("/{opp_id}/reviews/{filename}")
def get_review(opp_id: str, filename: str, request: Request):
    data = request.app.state.workspace_svc.get_file(opp_id, "reviews", filename)
    if data is None:
        raise HTTPException(404, f"Review {filename} not found")
    return data


@router.get("/{opp_id}/synthesis")
def get_synthesis(opp_id: str, request: Request):
    data = request.app.state.workspace_svc.get_file(opp_id, "", "synthesis.json")
    if data is None:
        raise HTTPException(404, f"Synthesis not found for {opp_id}")
    return data


@router.get("/{opp_id}/artifacts")
def list_artifacts(opp_id: str, request: Request):
    return request.app.state.workspace_svc.list_artifacts(opp_id)


@router.get("/{opp_id}/artifacts/{filename}")
def get_artifact(opp_id: str, filename: str, request: Request):
    content = request.app.state.workspace_svc.get_artifact(opp_id, filename)
    if content is None:
        raise HTTPException(404, f"Artifact {filename} not found")
    if filename.endswith(".json"):
        import json
        return json.loads(content)
    return PlainTextResponse(content)


@router.get("/{opp_id}/strategy-doc")
def get_strategy_doc(opp_id: str, request: Request):
    svc = request.app.state.workspace_svc
    state = svc.get_workspace_state(opp_id)
    if state is None:
        raise HTTPException(404, f"Workspace {opp_id} not found")
    votes = svc.get_votes(opp_id)
    prototypes = {}
    for a in state.get("artifacts", []):
        if re.search(r'prototype|\.html$', a["filename"], re.IGNORECASE):
            content = svc.get_artifact(opp_id, a["filename"])
            if content:
                prototypes[a["filename"]] = content
    builder = StrategyDocBuilder(state, votes, prototypes)
    html_content = builder.build()
    return HTMLResponse(content=html_content, headers={
        "Content-Disposition": f'inline; filename="strategy-{opp_id}.html"'
    })
