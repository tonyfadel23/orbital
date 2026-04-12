---
name: evidence-slack-signal
description: >
  Searches Slack channels for internal discussions, customer feedback
  threads, incident reports, and team sentiment on the opportunity topic.
compatibility:
  mcp_servers:
    - slack
---

# Evidence: Slack Signal

Search Slack for internal signal — team discussions, customer escalations, incident threads, feature requests.

## When to Use

- Looking for what internal teams are saying about a topic
- Want to find customer escalations or support patterns
- Need to understand team sentiment or operational pain points

## Input

- `query`: What to search for (e.g. "What are CX teams saying about fresh quality?")
- `opportunity_id`: The workspace this evidence belongs to

## Process

1. **Search Slack** — use `mcp__slack__slack_search_public` with relevant keywords
2. **Read key threads** — use `mcp__slack__slack_read_thread` for the most relevant discussions
3. **Synthesize themes** — what are people saying, how frequently, how recently
4. **Attribute sources** — which channels, which teams, approximate frequency
5. **Write evidence file** — to `data/workspaces/{opportunity_id}/evidence/{id}.json`

## Output

Same schema with `source_type: "slack-signal"`. Source detail should reference channels searched. Findings should capture themes with frequency.

## Confidence Assessment

- **High**: Multiple channels, consistent theme, recent discussions (<30 days)
- **Medium**: Single channel, or mixed signals, or older discussions
- **Low**: Few messages, or tangential mentions, or individual opinions vs team consensus

## Anti-Patterns

- Do NOT include names or quotes from private DMs
- Do NOT search more than 10 channels — focus on the most relevant
- Do NOT conflate individual opinions with team-wide sentiment
