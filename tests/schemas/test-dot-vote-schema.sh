#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIR/../.venv/bin/python3"
VALIDATE="$DIR/validate.py"
SCHEMA="$DIR/../schemas/dot-vote.schema.json"

echo "=== Dot-Vote Schema Tests ==="
echo ""
echo "--- Valid votes (should all pass) ---"
"$PYTHON" "$VALIDATE" "$SCHEMA" "$DIR/fixtures/votes/"
echo ""
echo "--- Invalid votes (should all be rejected) ---"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/vote-missing-function.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/vote-bad-score.json"
"$PYTHON" "$VALIDATE" --expect-fail "$SCHEMA" "$DIR/fixtures/invalid/vote-empty-votes.json"
echo ""
echo "=== All dot-vote tests passed ==="
