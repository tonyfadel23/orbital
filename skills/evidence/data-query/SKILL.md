---
name: evidence-data-query
description: >
  Gathers quantitative evidence from BigQuery to support or challenge
  opportunity assumptions. Translates a natural-language question into
  SQL, runs the query, and returns structured findings with confidence
  assessment. Used inline during the Agree phase when the user needs
  data to answer the framing agent's questions.
compatibility:
  mcp_servers:
    - bigquery
---

# Evidence: Data Query

Query internal data (BigQuery) to gather quantitative evidence for an opportunity under investigation.

## When to Use

- The Agree agent asks "Do you have data on X?"
- The user wants to validate an assumption with metrics
- A claim needs quantitative backing before the opportunity moves forward

## Input

You will receive:
- `query`: Natural-language question (e.g. "NPS scores for tmart fresh food, last 6 months")
- `opportunity_id`: The workspace this evidence belongs to
- `opportunity.json`: Current opportunity framing for context

## Process

1. **Read the opportunity** — understand the hypothesis, assumptions, and what signal would be useful
2. **Translate to SQL** — convert the natural-language query into a BigQuery SQL statement
3. **Run the query** — use the BigQuery MCP tool (`mcp__bigquery__execute-query`)
4. **Interpret results** — extract key metrics, trends, and insights
5. **Assess confidence** — based on sample size, data recency, and relevance
6. **Write evidence file** — structured JSON to `data/workspaces/{opportunity_id}/evidence/`

## Output

Write a single JSON file to `data/workspaces/{opportunity_id}/evidence/{id}.json` following `schemas/evidence.schema.json`.

### Required fields for completed evidence:
```json
{
  "id": "ev-YYYYMMDD-HHMMSS",
  "opportunity_id": "opp-...",
  "source_type": "data-query",
  "query": "the user's original question",
  "status": "completed",
  "source_detail": "BigQuery: dataset.table_name",
  "period": "time range of data",
  "findings": [
    {
      "metric": "metric name",
      "value": 42,
      "trend": "+5 vs prior period",
      "content": "Human-readable insight explaining WHY this metric matters to the opportunity"
    }
  ],
  "summary": "One paragraph synthesizing what the data shows",
  "confidence": "high|medium|low",
  "sample_size": 12847,
  "raw_query": "SELECT ... FROM ...",
  "created_at": "ISO8601",
  "completed_at": "ISO8601"
}
```

### If the query fails:
```json
{
  "id": "ev-YYYYMMDD-HHMMSS",
  "opportunity_id": "opp-...",
  "source_type": "data-query",
  "query": "the user's original question",
  "status": "failed",
  "error": "Clear description of what went wrong",
  "created_at": "ISO8601"
}
```

## Confidence Assessment

- **High**: Large sample (>1000), recent data (<3 months), directly relevant metric
- **Medium**: Moderate sample (100-1000), or indirect metric, or data >3 months old
- **Low**: Small sample (<100), proxy metric, or stale data (>6 months)

## Anti-Patterns

- Do NOT run exploratory queries fishing for interesting data — stay focused on the question
- Do NOT report raw numbers without interpretation — every finding must explain WHY it matters
- Do NOT overstate confidence — if the data is thin, say so
- Do NOT ignore counter-signals — if the data contradicts the hypothesis, report that clearly

## Available Tables

Use the BigQuery MCP tools to discover available tables:
- `mcp__bigquery__list-tables` — see what's available
- `mcp__bigquery__describe-table` — get schema for a specific table
- `mcp__bigquery__execute-query` — run the query

If you don't know which table to query, list tables first and find the most relevant one.
