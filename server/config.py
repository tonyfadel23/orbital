"""Orbital server configuration — resolve project paths."""

import os
from pathlib import Path


def get_project_root() -> Path:
    """Return the Orbital project root (parent of server/)."""
    return Path(__file__).resolve().parent.parent


def get_data_dir(root: Path | None = None) -> Path:
    return (root or get_project_root()) / "data"


def get_schemas_dir(root: Path | None = None) -> Path:
    return (root or get_project_root()) / "schemas"


def get_workspaces_dir(root: Path | None = None) -> Path:
    return get_data_dir(root) / "workspaces"


def get_context_dir(root: Path | None = None) -> Path:
    return get_data_dir(root) / "context"


def get_config_path(root: Path | None = None) -> Path:
    return get_data_dir(root) / "config.json"


def get_port() -> int:
    return int(os.environ.get("ORBITAL_PORT", "5111"))
