"""Context layer REST endpoints."""

from fastapi import APIRouter, HTTPException, Request


router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("")
def list_context(request: Request):
    return request.app.state.workspace_svc.list_context_layers()


@router.get("/{layer_type}")
def list_context_by_type(layer_type: str, request: Request):
    return request.app.state.workspace_svc.list_context_layers(layer_type=layer_type)


@router.get("/{layer_type}/{name}")
def get_context_layer(layer_type: str, name: str, request: Request):
    data = request.app.state.workspace_svc.get_context_layer(layer_type, name)
    if data is None:
        raise HTTPException(404, f"Context layer {layer_type}/{name} not found")
    return data
