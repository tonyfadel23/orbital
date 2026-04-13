---
name: orbit
description: >
  Run an Orbital investigation with parallel AI agents. Takes a framed opportunity
  with a locked roster and runs Phases 2-5: investigate, prototype, peer review,
  synthesize, decide. Use when PM says "orbit this", "investigate this", or
  "run an orbital" — after /agree and /assemble have completed.
compatibility:
  mcp_servers:
    - google-workspace
    - figma
    - github
    - linear
    - slack
    - atlassian
    - miro
---

# /orbit — Orbital Investigation Cycle

Run a parallel AI agent investigation of a product opportunity (Phases 2-5).

## When to Use
- Opportunity is framed (`/agree` done) and team is assembled (`/assemble` done)
- `opportunity.json` has status `"orbiting"` and a populated roster
- "Orbit this", "investigate this opportunity", "run an orbital"

## Prerequisites

Run these skills first (or provide a workspace with equivalent state):

1. **`/agree`** — Frame the opportunity: title, type, description, assumptions, success/kill signals, context refs. Status → `"framed"`.
2. **`/assemble`** — Assemble the team: roster with per-agent investigation tracks, tool access, rationale. Status → `"assembled"`. Server sets `"orbiting"` on launch.

**Input contract** — `opportunity.json` must have:
- `status: "orbiting"`
- `roster: [...]` (non-null, non-empty array)
- Populated: title, description, assumptions, success_signals, kill_signals, context_refs

## Phase Flow

### Phase 2: INVESTIGATE (parallel)
**Goal:** Agents work in parallel with scoped mandates.

1. Spawn each agent using the Agent tool
2. Each agent receives:
   - `opportunity.json` — the confirmed opportunity
   - Context layers — relevant L1/L2a/L2b documents
   - Investigation brief — their specific tracks and questions from the roster
   - Tool permissions — which MCP tools they're authorized to use
3. Each agent produces:
   - `contributions/{function}-round-1.json` — structured findings
   - `artifacts/{function-artifact}.md` — human-readable analysis
   - Other artifacts (prototypes, spreadsheets) as applicable
4. Each agent runs self-review before submission

**Artifact inventory per agent** (see `.claude/agents/*.md` for details):

| Agent | JSON | Markdown | Other |
|-------|------|----------|-------|
| Product | contribution.json | product.md | — |
| Design | contribution.json | design.md | Figma/HTML prototypes |
| Data | contribution.json | data.md | Google Sheets |
| Engineering | contribution.json | spec.md | System diagrams |
| Analyst | contribution.json | market.md | — |
| Financial | contribution.json | financial.md | Spreadsheet models |
| Legal | contribution.json | legal.md | — |
| Brand-Marketing | contribution.json | brand.md | — |
| UX-Writing | contribution.json | copy.md | — |
| Commercial-Strategy | contribution.json | commercial.md | — |
| Data-Science | contribution.json | models.md | Notebooks/scripts |

### Phase 2b: PROTOTYPE (if Design on roster)
**Goal:** Create and evaluate prototype variations.

1. Design Agent creates 2-3 prototype variations using Figma MCP (company design system)
2. Can also generate HTML prototypes for interactive exploration
3. Customer Voice Reviewer agent:
   - Synthesizes VoC data (interviews, reviews, support tickets, NPS)
   - Evaluates each variation against customer needs
   - Produces ranked evaluation with reasoning per variation
4. Best variation highlighted in `artifacts/design.md`
5. Customer voice synthesis saved to `artifacts/customer-voice.md`

### Phase 3: PEER REVIEW (dynamic)
**Goal:** Cross-functional review based on actual team roster.

1. Assign 1-2 reviewers per contribution from the actual roster (cross-functional)
2. Reviewers produce `reviews/{reviewer}-reviews-{reviewee}.json`
3. If revisions required: agent revises → round-2 contribution
4. Maximum rounds: `config.json` → `review_rounds_max`

Review assignments are dynamic — any rostered agent can review any other agent's contribution. The Product Agent assigns reviewers based on cross-functional relevance.

### Phase 4: SYNTHESIZE
**Goal:** Product Agent builds a multi-solution decision package with 3+ genuinely distinct solutions.

1. Product Agent reads all contributions, reviews, and markdown artifacts
2. Identifies:
   - **Convergence** — where multiple agents align
   - **Conflicts** — where agents disagree (both sides stated with evidence)
   - **Counter-signals** — evidence that challenges the hypothesis
3. Extracts **at least 3 distinct solution tracks** spanning three archetypes:
   - **Incremental** — low risk, builds on existing capabilities (1-3 sprints)
   - **Moderate** — medium risk, requires new capabilities (3-6 sprints)
   - **Ambitious** — high reward/risk, may need new infrastructure (6+ sprints)
4. ICE-scores each solution (Impact × Confidence × Ease, each 1-10)
5. For conditional solutions: sets `proceed_conditions` with measurable thresholds
6. Maps `depends_on` when solutions build on each other
7. Produces `synthesis.json` with:
   - `solutions[]` — 3+ ranked solution tracks with archetypes
   - `recommended_sequence` — implementation order
   - Quality score on 5 dimensions
8. Writes `artifacts/product.md` with full synthesis narrative

**Distinctiveness test:** If removing any solution doesn't change the overall recommendation, the portfolio isn't divergent enough. Rethink.

### Phase 4b: DOT-VOTE (feedback round)
**Goal:** Each agent scores all solutions from their functional perspective, creating a heat map.

**Skip condition:** If the roster has only the Product Agent (no investigating agents), skip directly to Phase 4c.

1. Product Agent confirms `synthesis.json` has 3+ solutions with archetypes
2. Set `opportunity.json` status → `"scoring"`
3. Spawn each rostered agent with:
   - `synthesis.json` — the full solution portfolio
   - Their function-specific scoring dimensions (defined in agent `.md` files)
4. Each agent scores every solution (1-10 per dimension) and writes:
   - `votes/{function}-vote.json` — follows `schemas/dot-vote.schema.json`
   - Rationale for each score (min 20 chars)
   - Flags: `blocker`, `risk`, `opportunity`, `needs_more_data`
   - Abstentions with reason if unable to score a solution
5. Timeout: `config.json` → `dot_vote_timeout_minutes` (default 15). Proceed without missing votes; note gaps.
6. Product Agent aggregates results into `synthesis.json`:
   - `dot_vote_summary.heat_map` — per-function average scores for each solution
   - `dot_vote_summary.consensus_ranking` — solutions ranked by aggregate score
7. If consensus ranking diverges significantly from `recommended_sequence`, revise the sequence

**Scoring dimensions per function:**

| Agent | Dimensions |
|-------|-----------|
| Product | strategic_fit, market_timing, competitive_advantage |
| Data | measurability, data_availability, signal_clarity |
| Engineering | feasibility, effort, technical_risk |
| Design | ux_coherence, research_alignment, accessibility_risk |
| Analyst | market_fit, competitive_differentiation, sizing_confidence |
| Financial | roi_clarity, unit_economics, payback_confidence |
| Data-Science | model_feasibility, experiment_validity, prediction_confidence |
| Legal | regulatory_risk, compliance_complexity, legal_precedent |
| Brand-Marketing | brand_fit, messaging_clarity, channel_readiness |
| Commercial-Strategy | revenue_impact, partnership_viability, market_timing |
| UX-Writing | content_clarity, tone_consistency, localization_readiness |
| Customer-Voice | customer_need_alignment, sentiment_confidence, segment_coverage |
| Others (fallback) | relevance, confidence |

### Phase 4c: DECISION BRIEF
**Goal:** Generate a shareable markdown artifact summarizing the investigation for leadership.

1. Product Agent generates `artifacts/decision-brief.md` with:
   - **Header** — title, date, investigation ID, verdict
   - **Executive Summary** — 2-3 sentence expansion of `verdict_summary`
   - **Context** — opportunity description + key context from layers
   - **Key Findings** — convergence points and counter-signals with severity
   - **Solutions (ranked by consensus)** — for each: archetype badge, ICE score, heat map row, evidence refs, proceed conditions
   - **Evidence Trail** — table of all findings (finding, agent, type, confidence, direction)
   - **Risks** — counter-signals, unresolved conflicts, blocker flags from dot-votes
   - **Recommendation** — rationale + recommended sequence
   - **Quality Assessment** — quality_score dimensions
2. This document must be readable by non-technical leadership

### Phase 5: DECIDE (interactive)
**Goal:** Human PM makes decisions on each solution.

1. Present the synthesis to the user:
   - Overall verdict and rationale
   - Ranked solutions with ICE scores
   - Key evidence, conflicts, and counter-signals
   - Quality score
2. Per solution, user can:
   - **Approve** → create Linear issue via `mcp__claude_ai_Linear__save_issue`
   - **Defer** → mark as deferred with rationale
   - **Kill** → mark as killed with rationale
3. Update `opportunity.json` status → `"decided"`
4. Update `synthesis.json` status → `"accepted"`, solution statuses updated
5. Suggest next steps:
   - "Run `/execute` for implementation planning" (approved solutions → tasks)
   - "Run `/explore` to branch into parallel solution tracks"

## Tool Access Model

3-layer access control:
1. **Config defaults** — `config.json` → `available_agents.{fn}.default_tool_access`
2. **Roster overrides** — `opportunity.json` → `roster[].tool_access`
3. **Agent capabilities** — `.claude/agents/*.md` → what the agent knows how to use

Effective access = roster authorization ∩ agent capability.

When an MCP tool is not connected, agents degrade gracefully — note data gaps and reduce confidence scores rather than failing.

## Workspace Structure

```
data/workspaces/{opp-id}/
├── opportunity.json
├── contributions/
│   ├── product-round-1.json
│   ├── design-round-1.json
│   ├── data-round-1.json
│   └── ...
├── reviews/
│   ├── data-reviewer-reviews-design.json
│   └── ...
├── votes/
│   ├── data-vote.json
│   ├── engineering-vote.json
│   ├── design-vote.json
│   ├── product-vote.json
│   └── ...
├── synthesis.json
└── artifacts/
    ├── product.md
    ├── design.md
    ├── data.md
    ├── spec.md
    ├── market.md
    ├── customer-voice.md
    ├── decision-brief.md
    └── ...
```

## Troubleshooting

**Agent fails to produce contribution:**
- Check that the agent has the required MCP tools connected (see Tool Access Model)
- Verify the agent's investigation brief has specific questions, not vague mandates
- If an MCP tool is unavailable, the agent should degrade gracefully — note the data gap and reduce confidence scores

**Contribution fails schema validation:**
- Validate against `schemas/contribution.schema.json` before accepting
- Common issues: missing `type`, `confidence`, or `source` fields on findings
- Ensure every finding explains WHY it matters to the opportunity

**Context layers not loading:**
- Verify `data/context/L1/`, `L2a/`, and `L2b/` directories exist and contain the expected files
- Check that the business line and market match available context directories

**Peer review loops indefinitely:**
- Maximum review rounds are capped by `config.json` → `review_rounds_max`
- If an agent keeps failing review, check whether the reviewer's criteria are achievable given available data

**Synthesis quality is low:**
- Verify the Product Agent is citing specific contribution IDs, not summarizing vaguely
- Check that counter-signals are surfaced — a clean narrative usually means evidence was buried
