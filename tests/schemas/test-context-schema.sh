#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIR/../.venv/bin/python3"
VALIDATE="$DIR/validate.py"
SCHEMA="$DIR/../schemas/context.schema.json"

echo "=== Context Schema Tests ==="
echo ""
echo "--- Valid contexts (should all pass) ---"
"$PYTHON" "$VALIDATE" "$SCHEMA" "$DIR/fixtures/contexts/"
echo ""
echo "--- Invalid contexts (should all be rejected) ---"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/context-bad-type.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/context-missing-sufficiency.json"
echo ""
echo "=== All context tests passed ==="
