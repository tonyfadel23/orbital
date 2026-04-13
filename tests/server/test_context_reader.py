"""Tests for MarkdownContextReader — reads product_lines/ _context.md files."""

import pytest
from pathlib import Path

from server.services.context_reader import MarkdownContextReader


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


@pytest.fixture
def product_lines(tmp_path):
    """Minimal product_lines tree for testing."""
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
    gr_uae = gr / "countries" / "uae"
    gr_uae.mkdir(parents=True)
    (gr_uae / "_context.md").write_text(BL_COUNTRY_CONTEXT)

    # pro BL (minimal)
    pro = pl / "pro"
    pro.mkdir(parents=True)
    (pro / "_context.md").write_text("# Pro\n> Level: BUSINESS LINE\n> Last updated: March 2026\n\n## BL Strategy & Narrative\nPro strategy.\n")

    return pl


class TestListLayers:
    def test_returns_all(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layers = reader.list_layers()
        ids = {l["id"] for l in layers}
        assert "company-global" in ids
        assert "bl-groceries" in ids
        assert "bl-pro" in ids
        assert "country-uae" in ids
        assert "bl-country-groceries-uae" in ids

    def test_skips_shared(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layers = reader.list_layers()
        ids = {l["id"] for l in layers}
        assert not any("shared" in i for i in ids)

    def test_filter_by_type_bl(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layers = reader.list_layers(layer_type="bl")
        assert all(l["layer_type"] == "bl" for l in layers)
        ids = {l["id"] for l in layers}
        assert "bl-groceries" in ids
        assert "bl-pro" in ids
        assert "company-global" not in ids

    def test_filter_by_type_country(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layers = reader.list_layers(layer_type="country")
        assert len(layers) == 1
        assert layers[0]["id"] == "country-uae"


class TestGetLayer:
    def test_get_company(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("company", "global")
        assert layer is not None
        assert layer["id"] == "company-global"
        assert layer["type"] == "global"
        assert "content" in layer
        assert layer["content"].get("strategy")

    def test_get_bl(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl", "groceries")
        assert layer is not None
        assert layer["id"] == "bl-groceries"
        assert layer["type"] == "business_line"
        content = layer["content"]
        # product_overview from BL Strategy section
        assert content.get("product_overview")
        # personas from Customer Segments table
        assert len(content.get("personas", [])) == 2
        assert content["personas"][0]["name"] == "Weekly Basket Builder"
        # competitors from Competitors table
        assert len(content.get("competitors", [])) == 2
        assert content["competitors"][0]["name"] == "Noon Minutes"
        # goals from JTBD numbered list
        assert len(content.get("goals", [])) == 3

    def test_get_bl_country(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl-country", "groceries-uae")
        assert layer is not None
        assert layer["id"] == "bl-country-groceries-uae"

    def test_get_country(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("country", "uae")
        assert layer is not None
        assert layer["id"] == "country-uae"
        assert layer["type"] == "country"

    def test_not_found(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        assert reader.get_layer("bl", "nonexistent") is None

    def test_voc_parsed(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl", "groceries")
        voc = layer["content"].get("voice_of_customer", {})
        assert len(voc.get("love", [])) >= 1
        assert len(voc.get("frustration", [])) >= 1

    def test_sources_parsed(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        layer = reader.get_layer("bl", "groceries")
        sources = layer.get("sources", [])
        assert len(sources) >= 2

    def test_sufficiency_computed(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        # groceries has many sections
        layer = reader.get_layer("bl", "groceries")
        suf = layer.get("sufficiency", {})
        assert suf["status"] in ("sufficient", "gaps_identified")
        # pro is minimal
        layer2 = reader.get_layer("bl", "pro")
        suf2 = layer2.get("sufficiency", {})
        assert suf2["status"] in ("gaps_identified", "insufficient")
        assert len(suf2.get("gaps", [])) > 0


class TestParsing:
    def test_parse_markdown_table(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        table = """| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |"""
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

    def test_parse_empty_table(self, product_lines):
        reader = MarkdownContextReader(product_lines)
        assert reader._parse_markdown_table("no table here") == []
