---
name: evidence-metrics-pull
description: >
  Pulls specific structured metrics from BigQuery — retention curves,
  conversion funnels, cohort analysis, segment breakdowns. More targeted
  than data-query: expects a specific metric with dimensions and filters.
compatibility:
  mcp_servers:
    - bigquery
---

# Evidence: Metrics Pull

Pull specific, structured metrics from BigQuery — not exploratory queries but targeted metric retrieval with known dimensions.

## When to Use

- Need a specific metric: "repeat rate for fresh-only baskets by cohort"
- Want a time series: "weekly active users for tmart, last 12 weeks"
- Need a funnel or conversion metric with segment breakdowns

## Input

- `query`: Specific metric request (e.g. "Repeat purchase rate for fresh-only baskets by monthly cohort")
- `opportunity_id`: The workspace this evidence belongs to

## Process

1. **Identify the metric** — what exactly is being measured, with what dimensions
2. **Find the table** — use `mcp__bigquery__list-tables` and `mcp__bigquery__describe-table`
3. **Build precise query** — with appropriate GROUP BY, filters, and time ranges
4. **Run and interpret** — execute query, structure results as findings
5. **Write evidence file** — to `data/workspaces/{opportunity_id}/evidence/{id}.json`

## Output

Same schema with `source_type: "metrics-pull"`. Each finding should have a `metric`, `value`, and optional `trend`. Include the raw SQL in `raw_query`.

## Confidence Assessment

Same as data-query — based on sample size, recency, and directness of the metric.

## Anti-Patterns

- Do NOT run wide exploratory queries — this skill is for specific metrics
- Do NOT aggregate away important segmentation — if cohorts differ, show that
- Do NOT ignore statistical significance — small cohorts need that caveat
