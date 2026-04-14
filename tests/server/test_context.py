"""Tests for context layer service, reader, index generator, and router."""

import re

import pytest
from pathlib import Path

from server.services.workspace import WorkspaceService
from server.services.context_reader import MarkdownContextReader
from server.services.context_index import (
    generate_index,
    _score_completeness,
    _extract_last_updated,
    _detect_staleness,
)


# ── Inline markdown fixtures for MarkdownContextReader / context_index ──────

COMPANY_CONTEXT = """# Company Context — Talabat
> Level: COMPANY
> Last updated: March 2026

---

## Strategy
Talabat is the leading food and Q-commerce platform in the GCC.
Three pillars: super-app depth, profitability, AI-native product.

## Platform Capabilities

| Capability | Owner | Maturity | Notes |
|------------|-------|----------|-------|
| TalabatPay | Fintech | Production | Credit, cashback |
| Fun with Flags | PEET | Production | Feature flagging |

### Sources
- Google Drive — Strategy doc, Jan 2026
- Internal deck — Platform review, Feb 2026

### Propagation History
| Date | What Changed | Source | Direction |
|------|-------------|--------|-----------|
| Mar 2026 | Initial context | Seed | — |
"""

BL_CONTEXT = """# Groceries — Business Line Context
> Level: BUSINESS LINE
> Inherits: company/_context.md
> Last updated: April 2026

---

## BL Strategy & Narrative

Groceries is talabat's next growth engine. Two models:
- **tMart** (owned dark stores): Speed leader.
- **Local Shops** (partner supermarkets): Breadth leader.

## Jobs to Be Done

1. **Stock confidence**: "I need to know what I order actually arrives"
2. **Speed over supermarket**: "I need it faster than going myself"
3. **Habit replacement**: "Make this easier than my weekly run"

## Customer Segments

| Segment | Description | Behaviour | Primary Pain | JTBD |
|---------|-------------|-----------|-------------|------|
| Weekly Basket Builder | 35-50, family | Compares prices | Stock accuracy | Habit replacement |
| Quick-Run Shopper | 25-35 | Values speed | Speed guarantee | Speed |

## Competitors (BL-wide)

| Competitor | Model | Markets | Strength | Weakness | Recent Moves |
|------------|-------|---------|----------|----------|-------------|
| Noon Minutes | Dark stores | UAE, KSA | Low pricing | Not profitable | Expansion |
| Amazon Now | Dark stores | UAE | Strong brand | New entrant | 19 stores |

## Unit Economics

| Metric | UAE | Kuwait |
|--------|-----|--------|
| Monthly orders | 4.76M | 2.42M |
| Monthly GMV | 100.7M | 70.7M |

## Trade-offs

1. **Speed vs. Assortment**: Wider SKU range vs. faster pick times.
2. **Owned vs. Marketplace**: Control vs. breadth.

## Experiment History

- **Fresh & Ultra Fresh** — AE only. +3.3% tMart ATC/user.
- **Flash Sales Reactivation** — EG. +9.86% grocery reactivation.

## Key Pain Points (from VoC & Flow Audit)

**What users love**:
- tMart 15-min delivery
- Curated assortment

**What breaks trust**:
1. Silent substitutions
2. Out-of-stock items shown after ordering
3. Fresh produce quality is a gamble

### Sources
- Google Drive — Strategy doc, Jan 2026
- BigQuery — fct_order, Apr 2026
- Slack — grocery channels, Apr 2026

### Propagation History
| Date | What Changed | Source | Direction |
|------|-------------|--------|-----------|
| Apr 2026 | Initial BL context | Strategy + Seed | Inbound |
"""

COUNTRY_CONTEXT = """# UAE — Country Context
> Level: COUNTRY
> Last updated: March 2026

## Regulations
- Data privacy: UAE Federal Decree 45/2021
- VAT: 5%

## Payment Infrastructure
Apple Pay, Samsung Pay, card-on-file dominant.

### Sources
- Legal team briefing, Mar 2026
"""

BL_COUNTRY_CONTEXT = """# Groceries UAE — BL Country Context
> Level: BL+COUNTRY
> Last updated: April 2026

## Local Competitors

| Competitor | Model | Strength |
|------------|-------|----------|
| Noon Minutes | Dark stores | Low pricing |

## BL Performance

| Metric | Value |
|--------|-------|
| Orders | 4.76M |
| GMV | 100.7M EUR |

### Sources
- BigQuery pull, Apr 2026
"""

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


# ── Shared fixture for MarkdownContextReader tests ──────────────────────────

@pytest.fixture
def product_lines(tmp_path):
    """Minimal product_lines tree for reader and index tests."""
    pl = tmp_path / "product_lines"

    # _company
    company = pl / "_company"
    company.mkdir(parents=True)
    (company / "_context.md").write_text(COMPANY_CONTEXT)
    country_dir = company / "countries" / "uae"
    country_dir.mkdir(parents=True)
    (country_dir / "_context.md").write_text(COUNTRY_CONTEXT)

    # _shared (should be skipped)
    (pl / "_shared").mkdir(parents=True)
    (pl / "_shared" / "CLAUDE.md").write_text("# Shared config")

    # groceries BL
    gr = pl / "groceries"
    gr.mkdir(parents=True)
    (gr / "_context.md").write_text(BL_CONTEXT)
    (gr / "WIKI.md").write_text("# Wiki\n")
    (gr / "_sources").mkdir()
    gr_uae = gr / "countries" / "uae"
    gr_uae.mkdir(parents=True)
    (gr_uae / "_context.md").write_text(BL_COUNTRY_CONTEXT)

    # pro BL (minimal)
    pro = pl / "pro"
    pro.mkdir(parents=True)
    (pro / "_context.md").write_text(
        "# Pro\n> Level: BUSINESS LINE\n> Last updated: March 2026\n\n"
        "## BL Strategy & Narrative\nPro strategy.\n\n"
        "## Jobs to Be Done\n1. Save money\n\n"
        "## Competitors\n| Comp | Model |\n|------|-------|\n| X | Y |\n\n"
        "### Sources\n- Doc\n"
    )

    # peet BL (sparse — for index staleness detection)
    (pl / "peet").mkdir(parents=True)
    (pl / "peet" / "_context.md").write_text(SPARSE_CONTEXT)

    return pl


# ═══════════════════════════════════════════════════════════════════
# MarkdownContextReader (product_lines/ _context.md files)
# ═══════════════════════════════════════════════════════════════════


class TestContextReaderList:
    def test_returns_all_and_skips_shared(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layers = reader.list_layers()
        ids = {l["id"] for l in layers}
        assert "company-global" in ids
        assert "bl-groceries" in ids
        assert "bl-pro" in ids
        assert "country-uae" in ids
        assert "bl-country-groceries-uae" in ids
        assert not any("shared" in i for i in ids)

    def test_filter_by_type(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        bl_layers = reader.list_layers(layer_type="bl")
        assert all(l["layer_type"] == "bl" for l in bl_layers)
        assert "bl-groceries" in {l["id"] for l in bl_layers}
        assert "company-global" not in {l["id"] for l in bl_layers}
        country_layers = reader.list_layers(layer_type="country")
        assert len(country_layers) == 1
        assert country_layers[0]["id"] == "country-uae"


class TestContextReaderGet:
    def test_get_company(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("company", "global")
        assert layer["id"] == "company-global"
        assert layer["type"] == "global"
        assert layer["content"].get("strategy")

    def test_get_bl_full_parse(self, product_lines):
        """BL get includes parsed personas, competitors, goals, VoC, sources, sufficiency."""
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl", "groceries")
        assert layer["id"] == "bl-groceries"
        assert layer["type"] == "business_line"
        content = layer["content"]
        assert content.get("product_overview")
        assert len(content.get("personas", [])) == 2
        assert content["personas"][0]["name"] == "Weekly Basket Builder"
        assert len(content.get("competitors", [])) == 2
        assert len(content.get("goals", [])) == 3
        # VoC parsing
        voc = content.get("voice_of_customer", {})
        assert len(voc.get("love", [])) >= 1
        assert len(voc.get("frustration", [])) >= 1
        # Sources
        assert len(layer.get("sources", [])) >= 2
        # Sufficiency
        suf = layer.get("sufficiency", {})
        assert suf["status"] in ("sufficient", "gaps_identified")

    def test_get_bl_country_and_country(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl-country", "groceries-uae")
        assert layer["id"] == "bl-country-groceries-uae"
        country = reader.get_layer("country", "uae")
        assert country["id"] == "country-uae"
        assert country["type"] == "country"

    def test_not_found(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        assert reader.get_layer("bl", "nonexistent") is None

    def test_sufficiency_sparse_bl(self, product_lines):
        """Sparse BL (pro) should have gaps flagged."""
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl", "pro")
        suf = layer.get("sufficiency", {})
        assert suf["status"] in ("gaps_identified", "insufficient")
        assert len(suf.get("gaps", [])) > 0


class TestContextReaderFallbackResolution:
    """_resolve_path must handle raw directory names from agent tool-call detection.

    The frontend detects context reads like 'groceries/_context.md' from agent
    output and passes raw directory names (e.g. 'groceries', '_company', 'uae')
    as layer_type to GET /api/context/{layerType}/{name}. The resolver must
    handle these in addition to the canonical types (company, bl, country).
    """

    def test_underscore_company_resolves(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("_company", "_context")
        assert layer is not None
        assert layer["type"] == "global"

    def test_raw_bl_name_resolves(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("groceries", "_context")
        assert layer is not None

    def test_raw_country_name_resolves(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("uae", "_context")
        assert layer is not None

    def test_nonexistent_raw_name_returns_none(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        assert reader.get_layer("nonexistent", "_context") is None


class TestContextReaderParsing:
    def test_parse_markdown_table(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        table = ("| Name | Age | City |\n|------|-----|------|\n"
                 "| Alice | 30 | NYC |\n| Bob | 25 | LA |")
        rows = reader._parse_markdown_table(table)
        assert len(rows) == 2
        assert rows[0]["Name"] == "Alice"
        assert rows[1]["City"] == "LA"

    def test_parse_numbered_list(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        text = "1. **First item**: description\n2. Second item\n3. Third item"
        items = reader._parse_numbered_list(text)
        assert len(items) == 3
        assert "First item" in items[0]


# ═══════════════════════════════════════════════════════════════════
# Context Index Generator
# ═══════════════════════════════════════════════════════════════════


class TestGenerateIndex:
    def test_lists_all_bls(self, product_lines):
        index = generate_index(product_lines)
        assert "groceries" in index
        assert "peet" in index
        assert "pro" in index
        assert "| _shared" not in index

    def test_index_content(self, product_lines):
        """Completeness scoring, staleness detection, and wiki links all present."""
        index = generate_index(product_lines)
        lines = index.split("\n")
        groceries_line = next(l for l in lines if "groceries" in l and "|" in l)
        peet_line = next(l for l in lines if "peet" in l and "|" in l)
        # Groceries has more sections than peet
        g_match = re.search(r"(\d+)/(\d+)", groceries_line)
        p_match = re.search(r"(\d+)/(\d+)", peet_line)
        assert g_match and p_match
        assert int(g_match.group(1)) > int(p_match.group(1))
        # Peet is stale (Jan 2025)
        assert "stale" in index.lower()
        # Wiki link: groceries has WIKI.md, pro does not
        pro_line = next(l for l in lines if "pro" in l and "|" in l)
        assert "WIKI" in groceries_line
        assert "WIKI" not in pro_line


class TestIndexHelpers:
    def test_score_completeness(self):
        filled_full, total_full = _score_completeness(FULL_CONTEXT)
        assert total_full == 9
        assert filled_full >= 8
        filled_sparse, total_sparse = _score_completeness(SPARSE_CONTEXT)
        assert total_sparse == 9
        assert filled_sparse <= 2

    def test_extract_last_updated(self):
        assert _extract_last_updated(FULL_CONTEXT) == "April 2026"
        assert _extract_last_updated("# No date\nHello") is None

    def test_detect_staleness(self):
        assert _detect_staleness("January 2025", threshold_days=30) is True
        assert _detect_staleness("April 2026", threshold_days=30) is False
        assert _detect_staleness(None, threshold_days=30) is True


