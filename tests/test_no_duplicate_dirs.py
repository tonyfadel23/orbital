"""Assert no BL directory contains a child with the same name (nested duplicate)."""

from pathlib import Path

from server.config import get_project_root


PRODUCT_LINES_DIR = get_project_root() / "data" / "context" / "product_lines"
SKIP_DIRS = {"_company", "_shared"}


def test_no_nested_duplicate_dirs():
    """Every BL folder (groceries/, pro/, etc.) must NOT contain a child folder with the same name."""
    if not PRODUCT_LINES_DIR.exists():
        return
    duplicates = []
    for bl_dir in sorted(PRODUCT_LINES_DIR.iterdir()):
        if not bl_dir.is_dir() or bl_dir.name in SKIP_DIRS or bl_dir.name.startswith("."):
            continue
        nested = bl_dir / bl_dir.name
        if nested.is_dir():
            duplicates.append(str(nested.relative_to(PRODUCT_LINES_DIR)))
    assert duplicates == [], f"Nested duplicate directories found: {duplicates}"
