#!/usr/bin/env python3
# Use .venv/bin/python3 if available for jsonschema
"""Orbital JSON Schema validator.

Usage:
    validate.py <schema_file> <data_file_or_dir>
    validate.py --expect-fail <schema_file> <data_file_or_dir>

Modes:
    Default:       all files must pass validation (exit 0 = all valid)
    --expect-fail: all files must FAIL validation (exit 0 = all correctly rejected)

Exit codes:
    0 = success (all files met expectation)
    1 = failure (some files did not meet expectation)
    2 = usage/file error
"""

import json
import sys
from pathlib import Path

try:
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(2)


def validate_file(schema: dict, data_path: Path) -> list[str]:
    """Validate a single JSON file against a schema. Returns list of errors."""
    try:
        with open(data_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    try:
        validate(instance=data, schema=schema)
        return []
    except ValidationError as e:
        path = " -> ".join(str(p) for p in e.absolute_path) or "(root)"
        return [f"At {path}: {e.message}"]
    except SchemaError as e:
        return [f"Schema error: {e.message}"]


def main():
    args = sys.argv[1:]
    expect_fail = False
    if args and args[0] == "--expect-fail":
        expect_fail = True
        args = args[1:]

    if len(args) != 2:
        print(__doc__)
        sys.exit(2)

    schema_path = Path(args[0])
    target_path = Path(args[1])

    if not schema_path.exists():
        print(f"ERROR: Schema not found: {schema_path}")
        sys.exit(2)

    with open(schema_path) as f:
        schema = json.load(f)

    if target_path.is_dir():
        files = sorted(target_path.rglob("*.json"))
        if not files:
            print(f"WARNING: No .json files found in {target_path}")
            sys.exit(0)
    elif target_path.is_file():
        files = [target_path]
    else:
        print(f"ERROR: Not found: {target_path}")
        sys.exit(2)

    failures = 0
    for fp in files:
        errors = validate_file(schema, fp)
        if expect_fail:
            if errors:
                print(f"PASS (correctly rejected) {fp.name}")
                print(f"  Reason: {errors[0]}")
            else:
                print(f"FAIL (should have been rejected) {fp.name}")
                failures += 1
        else:
            if errors:
                print(f"FAIL {fp.name}")
                for err in errors:
                    print(f"  {err}")
                failures += 1
            else:
                print(f"PASS {fp.name}")

    if failures > 0:
        print(f"\n{failures} unexpected result(s) in {len(files)} file(s)")
        sys.exit(1)
    else:
        label = "correctly rejected" if expect_fail else "valid"
        print(f"\nAll {len(files)} file(s) {label}")
        sys.exit(0)


if __name__ == "__main__":
    main()
