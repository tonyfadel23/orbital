"""Tests for context index generator."""

import pytest
from pathlib import Path

from server.services.context_index import (
    generate_index,
    _score_completeness,
    _extract_last_updated,
    _detect_staleness,
)


FULL_CONTEXT = """# Groceries — Business Line Context
> Level: BUSINESS LINE
> Last updated: April 2026

## BL Strategy & Narrative
Strategy text here.

## Jobs to Be Done
1. Stock confidence
2. Speed over supermarket

## Customer Segments
| Segment | Description |
|---------|-------------|
| Builder | Builds baskets |

## Competitors (BL-wide)
| Competitor | Model |
|------------|-------|
| Noon | Dark stores |

## Unit Economics
| Metric | Value |
|--------|-------|
| Orders | 4.76M |

## Trade-offs
1. Speed vs assortment

## Experiment History
Running experiments.

### Sources
- Google Drive — Strategy doc

### Propagation History
| Date | What Changed | Source | Direction |
|------|-------------|--------|-----------|
| Apr 2026 | Initial | Seed | Inbound |
"""

SPARSE_CONTEXT = """# Peet — Business Line Context
> Level: BUSINESS LINE
> Last updated: January 2025

## BL Strategy & Narrative
Strategy text only.

### Sources
- Internal doc
"""


@pytest.fixture
def product_lines_tree(tmp_path):
    """Minimal product_lines tree for testing."""
    pl = tmp_path / "product_lines"

    # _company
    (pl / "_company").mkdir(parents=True)
    (pl / "_company" / "_context.md").write_text("# Company\n> Last updated: March 2026\n\n## Strategy\nCompany strategy.\n")

    # _shared (should be skipped)
    (pl / "_shared").mkdir(parents=True)
    (pl / "_shared" / "CLAUDE.md").write_text("# Shared\n")

    # groceries — full
    (pl / "groceries").mkdir(parents=True)
    (pl / "groceries" / "_context.md").write_text(FULL_CONTEXT)
    (pl / "groceries" / "WIKI.md").write_text("# Wiki\n")
    (pl / "groceries" / "_sources").mkdir()

    # peet — sparse
    (pl / "peet").mkdir(parents=True)
    (pl / "peet" / "_context.md").write_text(SPARSE_CONTEXT)

    # pro — moderate
    (pl / "pro").mkdir(parents=True)
    (pl / "pro" / "_context.md").write_text(
        "# Pro\n> Last updated: March 2026\n\n## BL Strategy & Narrative\nPro strategy.\n\n## Jobs to Be Done\n1. Save money\n\n## Competitors\n| Comp | Model |\n|------|-------|\n| X | Y |\n\n### Sources\n- Doc\n"
    )

    return pl


class TestGenerateIndex:
    def test_lists_all_bls(self, product_lines_tree):
        index = generate_index(product_lines_tree)
        assert "groceries" in index
        assert "peet" in index
        assert "pro" in index
        # _shared and _company should not appear as BLs
        assert "| _shared" not in index

    def test_completeness_scoring(self, product_lines_tree):
        index = generate_index(product_lines_tree)
        # groceries has all sections, peet has very few
        # The index should show higher score for groceries
        lines = index.split("\n")
        groceries_line = next(l for l in lines if "groceries" in l and "|" in l)
        peet_line = next(l for l in lines if "peet" in l and "|" in l)
        # Extract scores like "8/9" → numerator
        import re
        g_match = re.search(r"(\d+)/(\d+)", groceries_line)
        p_match = re.search(r"(\d+)/(\d+)", peet_line)
        assert g_match and p_match
        assert int(g_match.group(1)) > int(p_match.group(1))

    def test_staleness_detection(self, product_lines_tree):
        index = generate_index(product_lines_tree)
        # peet last updated Jan 2025 — should be flagged as stale
        assert "peet" in index
        # The staleness alerts section should mention peet
        assert "Stale" in index or "stale" in index

    def test_wiki_link_present(self, product_lines_tree):
        index = generate_index(product_lines_tree)
        # groceries has WIKI.md, pro does not
        lines = index.split("\n")
        groceries_line = next(l for l in lines if "groceries" in l and "|" in l)
        pro_line = next(l for l in lines if "pro" in l and "|" in l)
        assert "WIKI" in groceries_line
        assert "WIKI" not in pro_line


class TestHelpers:
    def test_score_completeness_full(self):
        filled, total = _score_completeness(FULL_CONTEXT)
        assert total == 9
        assert filled >= 8  # all canonical sections present

    def test_score_completeness_sparse(self):
        filled, total = _score_completeness(SPARSE_CONTEXT)
        assert total == 9
        assert filled <= 2

    def test_extract_last_updated(self):
        assert _extract_last_updated(FULL_CONTEXT) == "April 2026"
        assert _extract_last_updated("# No date\nHello") is None

    def test_detect_staleness_old(self):
        assert _detect_staleness("January 2025", threshold_days=30) is True

    def test_detect_staleness_recent(self):
        assert _detect_staleness("April 2026", threshold_days=30) is False

    def test_detect_staleness_none(self):
        assert _detect_staleness(None, threshold_days=30) is True
