#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIR/../.venv/bin/python3"
VALIDATE="$DIR/validate.py"
SCHEMA="$DIR/../schemas/review.schema.json"

echo "=== Review Schema Tests ==="
echo ""
echo "--- Valid reviews (should all pass) ---"
"$PYTHON" "$VALIDATE" "$SCHEMA" "$DIR/fixtures/reviews/"
echo ""
echo "--- Invalid reviews (should all be rejected) ---"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/review-missing-issues.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/review-bad-reviewer.json"
echo ""
echo "=== All review tests passed ==="
