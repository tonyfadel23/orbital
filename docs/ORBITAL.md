# Orbital

**Version:** 0.3.0
**Status:** Building
**Last updated:** 2026-04-12

## What Is Orbital

Orbital is a decision operating system for product teams that implements the [Mental Model Shift](../../frameworks/AI%20Mental%20Model/mental-model-shift.md). It replaces sequential handoffs (PM -> Design -> Data -> Engineering) with an **orbital model** — AI agents representing different product functions investigate an opportunity in parallel, self-review, peer-review, score a portfolio of solutions via dot-voting, and present a ranked decision brief to the human PM.

The opportunity sits at the center. Not the PM. Not the AI. The problem being solved.

## Design Sprint Mapping

Orbital's phases map to a compressed, synthetic GV Design Sprint:

| Day | GV Sprint | Orbital Phase | What Happens |
|-----|-----------|---------------|--------------|
| Mon | Understand | Phase 0: AGREE | Frame the opportunity, load context, confirm scope |
| Tue | Sketch | Phase 1-2: ASSEMBLE + INVESTIGATE | Parallel agents explore from every angle |
| Wed | Decide | Phase 3-4: PEER REVIEW + SYNTHESIZE | Challenge findings, build solution portfolio |
| Thu | Prototype | Phase 4b-4c: DOT-VOTE + DECISION BRIEF | Score solutions, package for leadership |
| Fri | Test | Phase 5: DECIDE | Human picks solutions, creates execution tasks |

## Core Principles

1. **The opportunity is the center of gravity.** Every agent orbits the same problem. No function owns it.
2. **Parallel beats sequential.** Multiple functions investigating simultaneously collapse the latency between insight and action.
3. **Evidence, not opinions.** Each agent contributes findings grounded in data, prototypes, measurements, or constraints — not takes.
4. **Three-layer quality.** Self-review (function critiques itself) -> Peer review (cross-functional challenge) -> Product gate (quality checks before synthesis).
5. **Portfolio, not prescription.** Synthesis produces 3+ genuinely distinct solutions spanning incremental to ambitious. The human decides which to pursue.
6. **Cross-functional scoring.** Every agent scores every solution from their functional perspective. No single function dominates the recommendation.
7. **The human governs, the system works.** AI does the investigation. The PM frames the question, approves the roster, and makes the final call.
8. **Artifacts are evidence.** Prototypes, specs, and experiments are investigation tools produced during the orbit, not deliverables produced after.
9. **Show your reasoning.** Every finding explains WHY it was included and HOW it was validated.

## The Orbital Cycle (8 Phases)

```
Phase 0:  AGREE          — Refine opportunity with user, load context, confirm framing
Phase 1:  ASSEMBLE       — PM recommends team + investigation plans, user approves
Phase 2:  INVESTIGATE    — Agents work in parallel with scoped mandates
  └─ Sub: PROTOTYPE      — Design creates variations, Customer Voice Reviewer evaluates
Phase 3:  PEER REVIEW    — Dynamic cross-functional review
Phase 4:  SYNTHESIZE     — Multi-solution portfolio (3+ solutions with archetypes)
Phase 4b: DOT-VOTE       — Each agent scores all solutions from their function's lens
Phase 4c: DECISION BRIEF — Shareable markdown artifact for leadership
Phase 5:  DECIDE         — Human picks solutions, creates Linear tasks
```

### Phase 0: AGREE — `/agree` skill (interactive, multi-turn)
Human states an opportunity. Product Agent loads context layers (L1 global, L2a business line, L2b market), surfaces gaps, presents framing (title, description, type, assumptions, success/kill signals). User refines. Changes tracked in `refinement_history`. User confirms → status = `"assembled"`.

**Implementation:** Multi-turn conversation via `CliBridge`. Each turn is a `claude -p` invocation with `--output-format stream-json`. Agent reads context, shares insights, asks ONE probing question, then exits. User reply triggers `claude -p "reply" --resume`. After 3-5 turns, agent recommends `/assemble`.

### Phase 1: ASSEMBLE — `/assemble` skill (interactive, multi-turn)
Product Agent recommends a team roster using templates from `config.json`. For each agent: function, rationale, investigation tracks (with specific questions), expected artifacts (JSON + markdown), and tool access. User can add/remove agents, modify tracks, adjust tools. User confirms → roster locked into `opportunity.json`, status → `"orbiting"`.

**Implementation:** `POST /api/launch/{id}/assemble`. Same multi-turn pattern as Phase 0.

### Phase 2: INVESTIGATE (parallel)
Agents work in parallel. Each receives the opportunity, context layers, investigation brief, and tool permissions. Each produces structured JSON contributions + markdown artifacts. Self-review before submission.

**Sub-phase: PROTOTYPE** (if Design on roster)
Design Agent creates 2-3 prototype variations using Figma MCP. Customer Voice Reviewer synthesizes VoC data and evaluates each variation against customer needs. Ranked evaluation feeds into Design's contribution.

**Implementation:** `POST /api/launch/{id}/start` → `CliBridge.generate_function_commands()` → `AgentLauncher.launch_staggered()`.

### Phase 3: PEER REVIEW (dynamic)
Cross-functional review based on actual team roster. Product Agent assigns 1-2 reviewers per contribution. Reviewers produce structured reviews. If revisions required: round-2 (up to `review_rounds_max`).

### Phase 4: SYNTHESIZE — Solution Portfolio
Product Agent reads all contributions, reviews, and markdown artifacts. Identifies convergence, conflicts, counter-signals. Produces `synthesis.json` with 3+ genuinely distinct solutions:

- **Incremental** — builds on existing capabilities, 1-3 sprints
- **Moderate** — requires new capabilities, 3-6 sprints
- **Ambitious** — may need new infrastructure, 6+ sprints

Each solution includes: archetype, ICE scores (Impact x Confidence x Ease, 1-10), evidence_refs, proceed_conditions, depends_on, solution_quality scores.

Distinctiveness test: if removing a solution doesn't change the recommendation, the portfolio isn't divergent enough.

### Phase 4b: DOT-VOTE (parallel)
Each rostered agent scores every solution from their function's perspective. Scoring dimensions are function-specific:

| Agent | Scoring Dimensions |
|-------|-------------------|
| product | strategic_fit, market_timing, competitive_advantage |
| data | measurability, data_availability, signal_clarity |
| engineering | feasibility, effort, technical_risk |
| design | ux_coherence, research_alignment, accessibility_risk |
| analyst | market_fit, competitive_differentiation, sizing_confidence |
| financial | roi_clarity, unit_economics, payback_confidence |
| data-science | model_feasibility, experiment_validity, prediction_confidence |
| Others | relevance, confidence |

Agents can flag blockers, risks, opportunities, or data gaps. Results aggregated into a heat map (`synthesis.json` → `dot_vote_summary`) with `consensus_ranking`.

**Skip condition:** If only the product agent is on the roster, skip dot-vote and proceed to decision brief.

**Implementation:** `POST /api/launch/{id}/dot-vote` → `CliBridge.generate_dot_vote_commands()` → `AgentLauncher.launch_staggered()`.

### Phase 4c: DECISION BRIEF
Product Agent generates `artifacts/decision-brief.md` — a shareable artifact readable by non-technical leadership:

1. Executive Summary
2. Context
3. Key Findings (convergence + counter-signals)
4. Solutions (ranked by dot-vote consensus, with archetype badges and heat map rows)
5. Evidence Trail
6. Risks
7. Recommendation + Sequence
8. Quality Assessment

**Implementation:** `POST /api/launch/{id}/decision-brief` → `CliBridge.generate_decision_brief_command()` → `AgentLauncher.launch()`.

### Phase 5: DECIDE (interactive)
Present synthesis + decision brief to user. Per solution: approve (→ Linear issue), defer, or kill. Update opportunity status → `"decided"`. Suggest: `/execute` for implementation planning, `/explore` for parallel branches.

## Agent Catalog

### Always Included
| Agent | Role | Default Tools |
|-------|------|---------------|
| Product | Orchestrator — frames, assembles team, synthesizes, generates brief | Drive, Gmail, Linear, Slack |

### Core Functional Agents
| Agent | Role | Default Tools | Artifacts |
|-------|------|---------------|-----------|
| Design | Experience audit, prototyping, UX patterns | Figma, Drive, Miro | design.md, prototypes |
| Data | Baselines, funnel analysis, segment sizing | Sheets, Drive, BigQuery, Looker | data.md, spreadsheets |
| Engineering | Feasibility, architecture, effort estimation | GitHub, Drive, Jira | spec.md |
| Analyst | Market sizing, competitive landscape | Drive, Sheets, Slack, Looker | market.md |
| Financial | Unit economics, ROI modeling | Sheets, Drive | financial.md |

### Specialist Agents
| Agent | Role | Default Tools | Artifacts |
|-------|------|---------------|-----------|
| Legal | Regulatory constraints, compliance | Drive | legal.md |
| Brand-Marketing | Positioning, go-to-market | Figma, Drive, Slack | brand.md |
| UX-Writing | Content strategy, tone, key copy | Figma, Drive | copy.md |
| Commercial-Strategy | Partnerships, marketplace dynamics | Drive, Sheets, Slack | commercial.md |
| Data-Science | Predictive models, experiment design | GitHub, Sheets, BigQuery | models.md |

### Special-Purpose Agents
| Agent | Role | Used In |
|-------|------|---------|
| Customer Voice | VoC synthesis, prototype evaluation | /prototype, Phase 2b |
| Tech Lead | Blast radius, task breakdown, assignments | /execute |
| Quality Judge | Cross-agent synthesis evaluation (5 rubrics) | Phase 4b–5, quality endpoints |

## Tool Access Model

3-layer access control:
1. **Config defaults** — `config.json` → `available_agents.{fn}.default_tool_access`
2. **Roster overrides** — `opportunity.json` → `roster[].tool_access`
3. **Agent capabilities** — `.claude/agents/*.md` → what the agent knows how to use

Effective access = roster authorization ∩ agent capability.

When an MCP tool is not connected, agents degrade gracefully — note data gaps and reduce confidence scores rather than failing. See `docs/mcp-setup.md` for BigQuery, Tableau, and Looker setup.

## Skills

| Skill | Description |
|-------|-------------|
| `/agree` | Phase 0: refine opportunity framing with user (multi-turn) |
| `/assemble` | Phase 1: assemble investigation team, roster, tools, tracks (multi-turn) |
| `/orbit` | Phases 2-5: investigate → peer review → portfolio synthesis → dot-vote → decision brief → decide |
| `/prototype` | Standalone prototype variation + customer voice review |
| `/execute` | Tech Lead: blast radius, Linear tasks, assignments |
| `/explore` | Parallel solution branches (lopsided OST) |

## Server Architecture

Orbital includes a development server for the investigation UI:

- **FastAPI** (`server/app.py`) — REST API + WebSocket + static file serving
- **CliBridge** (`server/services/cli_bridge.py`) — generates `claude -p` commands with turn-aware prompts
- **AgentLauncher** (`server/services/launcher.py`) — manages `claude` subprocesses (stdin/stdout/lifecycle)
- **WorkspaceWatcher** (`server/services/watcher.py`) — monitors file changes, pushes updates via WebSocket
- **WorkspaceService** (`server/services/workspace.py`) — filesystem operations (CRUD, votes, decision briefs, quality results)
- **SchemaValidator** (`server/services/validator.py`) — validates JSON against schemas
- **QualityGateService** (`server/services/quality_gates.py`) — Layer 1 deterministic gates (assumption coverage, confidence floor, solution distinctiveness, evidence freshness, vote quorum, finding density)
- **LLMJudgeService** (`server/services/llm_judge.py`) — Layer 2 LLM-as-Judge evaluation (5 binary rubrics per finding via Claude Haiku)
- **JudgeAgentService** (`server/services/judge_agent.py`) — Layer 3 Agent-as-a-Judge (cross-agent synthesis evaluation via judge subprocess)
- **Frontend** (`server/static/index.html`) — HTML + JS app with Phase 0 chat, workspace preview, agent monitoring, quality dashboard
- **Design System** (`server/static/design-system.css`) — tokens, components, utilities; reference at `docs/design-system.md`
- **Config** (`data/config.json`) — agent catalog, tool registry, roster templates, dot-vote settings

### Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/workspaces` | Create workspace |
| PATCH | `/api/workspaces/{id}/opportunity` | Update opportunity |
| GET | `/api/workspaces/{id}` | Full workspace state |
| GET | `/api/workspaces/{id}/votes` | Dot-vote files |
| GET | `/api/workspaces/{id}/decision-brief` | Decision brief markdown |
| POST | `/api/launch/{id}/start` | Launch investigation (parallel) |
| POST | `/api/launch/{id}/assemble` | Launch /assemble skill |
| POST | `/api/launch/{id}/dot-vote` | Launch parallel dot-vote |
| POST | `/api/launch/{id}/decision-brief` | Launch decision brief generation |
| POST | `/api/launch/{id}/send` | Send message / resume |
| POST | `/api/launch/{id}/approve` | Approve plan mode |
| POST | `/api/launch/{id}/stop` | Stop subprocess |
| GET | `/api/launch/{id}/status` | Poll subprocess output |
| GET | `/api/workspaces/{id}/quality` | Full quality report (Layer 1 live, Layer 2+3 from files) |
| GET | `/api/workspaces/{id}/quality/gates` | Layer 1 gates only |
| POST | `/api/workspaces/{id}/quality/evaluate` | Trigger Layer 2 LLM evaluation |
| POST | `/api/workspaces/{id}/quality/judge` | Launch Layer 3 judge agent |
| GET | `/api/workspaces/{id}/quality/judge` | Poll judge agent status + results |
| GET | `/api/quality/config` | Read quality gate configuration |
| PATCH | `/api/quality/config` | Update quality gate configuration |
| GET | `/api/catalog/tools` | Tool registry |
| GET | `/api/context` | Context layers |
| WS | `/ws/workspace/{id}` | Real-time file changes |

## Data Model

### Opportunity (center object)
Framed as hypothesis, problem, or strategic question. Holds assumptions, success/kill signals, context references, refinement history, team roster, and the final decision.

**Status flow:** `aligning` → `assembled` → `orbiting` → `converging` → `scoring` → `landed`

### Contribution (per agent, per round)
Typed findings (evidence_candidate, constraint, opportunity, risk, prototype_insight, measurement, counter_signal) plus artifacts produced, cross-references, and self-review. Agent function is pattern-based (`^[a-z][a-z0-9-]*$`) — not limited to a fixed list.

### Review (peer or self)
Independent review of a contribution. Reviewer function is pattern-based. Includes review_type (self or peer), issues, strengths, and revisions required.

### Synthesis (decision package)
Multi-solution portfolio with:
- Convergence, conflicts, counter-signals
- `solutions[]` — 3+ distinct solutions, each with archetype (incremental/moderate/ambitious), ICE scores, evidence_refs, proceed_conditions, depends_on, solution_quality
- `recommended_sequence` — implementation order
- `dot_vote_summary` — heat_map (function → solution → avg score) + consensus_ranking
- Optional Linear integration (`linear_issue_id`, `linear_issue_url`)
- Quality score on 5 dimensions

### Dot-Vote (per agent)
Per-agent scoring of all solutions. Each vote includes:
- `voter_function` — the agent's function name
- `votes[]` — per-solution scores on function-specific dimensions (1-10), rationale, flags
- `abstentions[]` — solutions the agent can't score, with reason

### Decision Brief (markdown artifact)
Shareable document for leadership. Nine sections: Executive Summary, Context, Key Findings, Solutions (ranked), Evidence Trail, Risks, Recommendation, Quality Assessment. Lives at `artifacts/decision-brief.md`.

### Context Layers
Organizational context (global, business line, market) that grounds all agents in the same reality.

### Context Ref Convention
A `context_ref` ID uses the format `{layer_type}-{filename_without_extension}`. To resolve: split on the first hyphen — prefix is the directory, suffix is the filename. Path: `data/context/{prefix}/{suffix}.json`. Examples:
- `L1-global` -> `data/context/L1/global.json`
- `L2a-groceries` -> `data/context/L2a/groceries.json`
- `L2b-ae` -> `data/context/L2b/ae.json`

## Benchmarks (calibrating — targets based on design intent)

These benchmarks will be calibrated after 10+ cycles. Until then, they represent design-intent targets.

- **Cycle duration:** 30-120 min depending on complexity
- **Findings per agent:** 3-7 (fewer = shallow, more = unfocused)
- **Counter-signals:** at least 1 per cycle (0 = confirmation bias)
- **Kill rate:** 30-40% of opportunities should be killed (lower = not challenging enough)
- **Quality score thresholds:** <0.5 = redo, 0.5-0.7 = proceed with caution, >0.7 = strong
- **Conflicts:** 1-3 per cycle (0 = agents aren't challenging each other)
- **Solution portfolio:** minimum 3 solutions spanning at least 2 archetypes

### Quality Gate Defaults

Enforced by the 3-layer quality evaluation system (see `docs/quality-gates.md`):

| Gate | Default | Blocking |
|------|---------|----------|
| Assumption coverage | 100% of assumptions addressed | Yes |
| Confidence floor | Mean finding confidence ≥ 0.4 | Yes |
| Solution distinctiveness | Pairwise Jaccard < 0.7 | No |
| Evidence freshness | Sources ≤ 180 days old | No |
| Vote quorum | ≥ 80% of roster voted | Yes |
| Finding density | ≥ 3 findings per contribution | Yes |
| LLM-as-Judge pass rate | ≥ 60% of rubrics passed per finding | Configurable |

## Architecture

```
code/orbital/
├── ORBITAL.md              # This file — system design + data model
├── CLAUDE.md               # Project instructions for Claude Code
├── README.md               # Quick-start guide
├── .claude/
│   └── agents/             # Agent definitions (13 agents)
│       ├── product.md      # Orchestrator (always included)
│       ├── design.md       # UX audit, prototyping
│       ├── data.md         # Baselines, funnels, segments
│       ├── engineering.md  # Feasibility, architecture
│       ├── analyst.md      # Market sizing, competitive
│       ├── financial.md    # Unit economics, ROI
│       ├── data-science.md # Predictive models, experiments
│       ├── legal.md        # Regulatory, compliance
│       ├── brand-marketing.md  # Positioning, GTM
│       ├── commercial-strategy.md  # Partnerships
│       ├── ux-writing.md   # Content strategy, copy
│       ├── customer-voice.md   # VoC synthesis
│       ├── tech-lead.md    # Blast radius, Linear tasks
│       └── quality-judge.md # Cross-agent synthesis evaluation
├── skills/
│   ├── agree/SKILL.md      # Phase 0: refine opportunity framing
│   ├── assemble/SKILL.md   # Phase 1: assemble investigation team
│   ├── orbit/SKILL.md      # Phases 2-5: investigate → decide
│   ├── prototype/SKILL.md  # Prototype variations + customer voice
│   ├── execute/SKILL.md    # Tech Lead + Linear tasks
│   └── explore/SKILL.md    # Parallel solution branches
├── schemas/                # JSON Schema Draft 2020-12
│   ├── opportunity.schema.json
│   ├── contribution.schema.json
│   ├── review.schema.json
│   ├── synthesis.schema.json
│   ├── dot-vote.schema.json
│   ├── context.schema.json
│   ├── evidence.schema.json
│   └── quality-evaluation.schema.json
├── data/
│   ├── config.json         # Roster templates, agent catalog, tool registry, dot-vote settings
│   ├── context/            # Org context layers (L1, L2a, L2b)
│   └── workspaces/         # One per opportunity
├── server/
│   ├── app.py              # FastAPI — REST + WebSocket + static
│   ├── routers/            # workspaces, launch, catalog, context, evidence, quality
│   ├── services/           # workspace, cli_bridge, launcher, watcher, validator, quality_gates, llm_judge, judge_agent
│   ├── ws/                 # WebSocket handler
│   └── static/
│       ├── index.html      # Frontend app (HTML + JS)
│       └── design-system.css # Tokens, components, utilities
├── docs/
│   ├── mcp-setup.md        # BigQuery, Tableau, Looker setup
│   ├── design-system.md    # Design system reference
│   └── quality-gates.md    # 3-layer quality evaluation system
├── tests/
│   ├── schemas/            # Schema validation tests (bash)
│   ├── fixtures/           # Valid + invalid test data
│   │   ├── contributions/
│   │   ├── reviews/
│   │   ├── syntheses/
│   │   ├── votes/          # Dot-vote fixtures
│   │   └── opportunities/
│   ├── server/             # API, WebSocket, service tests (pytest)
│   └── validate.py         # Schema validation script
└── playground-*.html       # Interactive visualizations
```

## Workspace Structure

```
data/workspaces/{opp-id}/
├── opportunity.json            # Framing, roster, status, decision
├── contributions/
│   ├── {function}-round-{n}.json
│   └── ...
├── reviews/
│   ├── {reviewer}-reviews-{reviewee}.json
│   └── ...
├── synthesis.json              # Solution portfolio + dot_vote_summary
├── votes/
│   ├── {function}-vote.json    # Per-agent dot-vote scoring
│   └── ...
├── evidence/
│   └── {evidence-id}.json      # Evidence collected during investigation
├── quality/
│   ├── evaluation.json         # Layer 1 deterministic gate results
│   ├── llm-judge.json          # Layer 2 LLM-as-Judge results
│   └── judge-evaluation.json   # Layer 3 Agent-as-a-Judge results
└── artifacts/
    ├── decision-brief.md       # Shareable leadership document
    ├── product.md
    ├── design.md
    ├── data.md
    ├── spec.md
    ├── market.md
    ├── customer-voice.md
    └── {prototypes, spreadsheets, etc.}
```
