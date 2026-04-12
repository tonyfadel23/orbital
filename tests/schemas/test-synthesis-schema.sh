#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIR/../.venv/bin/python3"
VALIDATE="$DIR/validate.py"
SCHEMA="$DIR/../schemas/synthesis.schema.json"

echo "=== Synthesis Schema Tests ==="
echo ""
echo "--- Valid syntheses (should all pass) ---"
"$PYTHON" "$VALIDATE" "$SCHEMA" "$DIR/fixtures/syntheses/"
echo ""
echo "--- Invalid syntheses (should all be rejected) ---"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/synthesis-missing-recommendation.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/synthesis-bad-ice-score.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/synthesis-too-few-solutions.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/synthesis-bad-archetype.json"
echo ""
echo "=== All synthesis tests passed ==="
