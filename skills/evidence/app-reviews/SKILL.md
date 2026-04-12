---
name: evidence-app-reviews
description: >
  Analyzes app store reviews (iOS App Store, Google Play) for customer
  sentiment, complaints, and praise related to the opportunity topic.
  Uses web search to find and analyze review data.
compatibility:
  mcp_servers: []
---

# Evidence: App Reviews

Analyze app store reviews for voice-of-customer signal on a specific topic.

## When to Use

- Need customer sentiment data on a specific feature or experience
- Want to understand complaint patterns or praise themes
- Looking for qualitative signal from real users at scale

## Input

- `query`: Topic to analyze in reviews (e.g. "Fresh food complaints, last 90 days")
- `opportunity_id`: The workspace this evidence belongs to

## Process

1. **Search for reviews** — use web search to find recent app store reviews mentioning the topic
2. **Categorize themes** — group by complaint type, praise type, feature request
3. **Quantify where possible** — frequency of themes, star rating distribution
4. **Extract representative quotes** — strongest examples of each theme
5. **Write evidence file** — to `data/workspaces/{opportunity_id}/evidence/{id}.json`

## Output

Same schema with `source_type: "app-reviews"`. Findings should include theme counts and representative quotes. Sample size = number of reviews analyzed.

## Confidence Assessment

- **High**: 100+ reviews analyzed, clear theme patterns, recent data
- **Medium**: 20-100 reviews, or mixed signals, or older reviews
- **Low**: <20 reviews, or reviews from a different market/context

## Anti-Patterns

- Do NOT cherry-pick only negative or positive reviews — represent the full picture
- Do NOT count the same review twice across themes
- Do NOT extrapolate from very small samples
