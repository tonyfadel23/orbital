"""Tests for schema validation service."""

import pytest

from server.services.validator import SchemaValidator


class TestSchemaValidator:
    def test_validate_valid_opportunity(self, tmp_project_root, tmp_data_dir):
        validator = SchemaValidator(tmp_project_root / "schemas")
        opp = {
            "id": "opp-20260412-100000",
            "type": "hypothesis",
            "title": "Test opportunity title",
            "description": "Test opportunity description text",
            "context_refs": ["L1-global"],
            "assumptions": [{"id": "asm-001", "content": "Some assumption text here", "status": "untested", "importance": "critical"}],
            "success_signals": ["Something works"],
            "kill_signals": ["Nothing works"],
            "status": "aligning",
            "decision": None,
            "created_at": "2026-04-12T10:00:00Z",
            "updated_at": "2026-04-12T10:00:00Z"
        }
        errors = validator.validate(opp, "opportunity")
        assert errors == []

    def test_validate_invalid_opportunity(self, tmp_project_root):
        validator = SchemaValidator(tmp_project_root / "schemas")
        bad = {"id": "bad", "type": "wrong"}
        errors = validator.validate(bad, "opportunity")
        assert len(errors) > 0

    def test_validate_unknown_schema(self, tmp_project_root):
        validator = SchemaValidator(tmp_project_root / "schemas")
        errors = validator.validate({}, "nonexistent")
        assert len(errors) == 1
        assert "not found" in errors[0].lower()
