"""Playwright E2E test fixtures for Orbital."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


def load_fixture_raw(name: str) -> str:
    """Load a fixture file as raw text."""
    return (FIXTURES_DIR / name).read_text()
