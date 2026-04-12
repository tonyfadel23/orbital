#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIR/../.venv/bin/python3"
VALIDATE="$DIR/validate.py"
SCHEMA="$DIR/../schemas/contribution.schema.json"

echo "=== Contribution Schema Tests ==="
echo ""
echo "--- Valid contributions (should all pass) ---"
"$PYTHON" "$VALIDATE" "$SCHEMA" "$DIR/fixtures/contributions/"
echo ""
echo "--- Invalid contributions (should all be rejected) ---"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/contribution-missing-findings.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/contribution-bad-function.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/contribution-old-self-review.json"
echo ""
echo "=== All contribution tests passed ==="
