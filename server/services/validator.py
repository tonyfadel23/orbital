"""JSON Schema validation service — wraps jsonschema library."""

import json
from pathlib import Path

from jsonschema import validate, ValidationError, SchemaError


class SchemaValidator:
    def __init__(self, schemas_dir: Path):
        self.schemas_dir = schemas_dir

    def validate(self, data: dict, schema_type: str) -> list[str]:
        schema_path = self.schemas_dir / f"{schema_type}.schema.json"
        if not schema_path.exists():
            return [f"Schema not found: {schema_type}"]
        schema = json.loads(schema_path.read_text())
        try:
            validate(instance=data, schema=schema)
            return []
        except ValidationError as e:
            path = " -> ".join(str(p) for p in e.absolute_path) or "(root)"
            return [f"At {path}: {e.message}"]
        except SchemaError as e:
            return [f"Schema error: {e.message}"]
