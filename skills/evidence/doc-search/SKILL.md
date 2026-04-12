---
name: evidence-doc-search
description: >
  Searches Google Drive for internal research documents, decks, reports,
  and analysis relevant to the opportunity. Returns key findings from
  matching documents with source attribution.
compatibility:
  mcp_servers:
    - google-workspace
---

# Evidence: Document Search

Search internal documents (Google Drive) for qualitative evidence — research reports, strategy decks, customer studies, competitive analyses.

## When to Use

- Looking for existing research that addresses the opportunity hypothesis
- Need to find prior work, decisions, or analysis on a topic
- Want to surface internal knowledge that's already been documented

## Input

- `query`: What to search for (e.g. "Customer research on fresh food trust")
- `opportunity_id`: The workspace this evidence belongs to

## Process

1. **Search Google Drive** — use `mcp__google-workspace__search_drive_files` with the query
2. **Read top results** — use `mcp__google-workspace__get_drive_file_content` for the most relevant docs
3. **Extract findings** — pull out key data points, conclusions, and recommendations
4. **Assess relevance** — how directly does this address the opportunity's assumptions?
5. **Write evidence file** — to `data/workspaces/{opportunity_id}/evidence/{id}.json`

## Output

Same schema as data-query, with `source_type: "doc-search"`.

Source detail should reference the document name and folder path. Each finding should cite which document it came from.

## Confidence Assessment

- **High**: Recent research (<6 months) with rigorous methodology, directly on topic
- **Medium**: Older research, tangentially related, or small sample size
- **Low**: Anecdotal references, draft documents, or unvalidated analysis

## Anti-Patterns

- Do NOT summarize entire documents — extract only findings relevant to the query
- Do NOT read more than 5 documents — focus on the most relevant matches
- Do NOT include confidential document contents verbatim — paraphrase and cite
