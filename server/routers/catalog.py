"""Catalog REST endpoints — agent catalog, roster templates, tool registry."""

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("")
def get_catalog(request: Request):
    return request.app.state.workspace_svc.get_config()


@router.get("/agents")
def get_agents(request: Request):
    config = request.app.state.workspace_svc.get_config()
    return config.get("available_agents", {})


@router.get("/templates")
def get_templates(request: Request):
    config = request.app.state.workspace_svc.get_config()
    return config.get("roster_templates", {})


@router.get("/tools")
def get_tools(request: Request):
    config = request.app.state.workspace_svc.get_config()
    return config.get("tool_registry", {})
