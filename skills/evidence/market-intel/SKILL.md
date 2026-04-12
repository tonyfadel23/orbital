---
name: evidence-market-intel
description: >
  Gathers external market intelligence — competitor analysis, industry
  benchmarks, market sizing, regulatory context — via web search and
  public sources.
compatibility:
  mcp_servers: []
---

# Evidence: Market Intelligence

Search the web for external evidence — competitor moves, industry benchmarks, market data, regulatory context.

## When to Use

- Need competitive benchmarks or market sizing
- Want to understand what competitors are doing in this space
- Looking for industry trends or best practices
- Regulatory or market context for a specific geography

## Input

- `query`: What to research (e.g. "Q-commerce fresh food trust benchmarks MENA")
- `opportunity_id`: The workspace this evidence belongs to

## Process

1. **Web search** — use WebSearch for recent industry reports, news, and analysis
2. **Fetch key sources** — use WebFetch for the most relevant pages
3. **Extract data points** — competitor features, market sizes, growth rates, benchmarks
4. **Cross-reference** — verify claims across multiple sources where possible
5. **Write evidence file** — to `data/workspaces/{opportunity_id}/evidence/{id}.json`

## Output

Same schema with `source_type: "market-intel"`. Source detail should reference URLs or publication names. Set `sample_size: 0` for market intel (not sample-based).

## Confidence Assessment

- **High**: Multiple credible sources agree, data from reputable research firms, <12 months old
- **Medium**: Single source, or unverified claims, or older data
- **Low**: Blog posts without citations, press releases (inherently biased), or very old data

## Anti-Patterns

- Do NOT treat press releases as objective data — they're marketing
- Do NOT present competitor claims without noting they're unverified
- Do NOT extrapolate from different markets without noting the context difference
