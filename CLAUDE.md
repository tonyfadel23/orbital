# Orbital — Project Instructions

## What This Is
Orbital is a decision operating system that runs synthetic GV Design Sprints using Claude Code agent teams. Parallel AI agents investigate product opportunities from different functional perspectives, produce a portfolio of distinct solutions, score them via dot-voting, and package everything into a decision brief for leadership.

## Investigation Workflow
- **Framing first**: every opportunity must have a target segment, geo scope, investigation type (discovery/optimization), and specific metric before drafting. See `/agree` skill Step 0.
- **Read before acting**: read `data/config.json` for agent metadata, then read only the selected agents' `.md` files — never read all 14 agent definitions.
- **Skills are in `skills/*/SKILL.md`** — check there before attempting to run any skill command.
- **File writes are mandatory**: `/agree` and `/assemble` must update `opportunity.json` on every turn, including the first. Verify the write landed.

## Development Rules

### TDD — No Exceptions
1. **Red** — Write a failing test first.
2. **Green** — Write the minimum code to pass.
3. **Refactor** — Clean up while tests stay green.

### Conventions
- Schemas are JSON Schema Draft 2020-12
- Data files are JSON
- Agent definitions are markdown (`.claude/agents/*.md`)
- Skills are markdown (`skills/*/SKILL.md`)
- Tests use Python (jsonschema library) + bash runners
- IDs use format: `{type}-{YYYYMMDD}-{HHMMSS}` (e.g., `opp-20260405-120000`)
- Vote IDs: `vote-{function}-YYYYMMDD-HHMMSS`
- Solution IDs: `sol-001`, `sol-002`, etc.

### File Structure Rules
- Each opportunity gets its own workspace: `data/workspaces/{opp-id}/`
- Contributions go in `contributions/{function}-round-{n}.json`
- Markdown artifacts go in `artifacts/{function-artifact}.md`
- Reviews go in `reviews/{reviewer}-reviews-{reviewee}.json`
- Votes go in `votes/{function}-vote.json`
- Decision brief goes in `artifacts/decision-brief.md`
- Context layers go in `data/context/{layer-type}/`
- Never modify schemas without updating tests first

### Agent Development
- **Two-pass selection**: select agents from `config.json` metadata (`role`, `domains`, `always_included`), then read full `.claude/agents/{function}.md` only for shortlisted agents. Never read all agent files — use the registry.
- Each agent definition specifies: Role, Tool Access, Investigation Tracks, Artifacts Produced, Output Format, Self-Review Protocol, Peer Review Behavior, Dot-Vote Behavior, Anti-Patterns
- Agents write structured JSON contributions AND markdown artifacts
- JSON contributions follow `schemas/contribution.schema.json`
- Dot-vote files follow `schemas/dot-vote.schema.json`
- Markdown artifacts are for human-readable analysis and agent-to-agent communication
- Every finding must include a `type`, `confidence`, and `source`
- Agents must explain WHY each finding matters to the opportunity
- Agent function names use pattern `^[a-z][a-z0-9-]*$` — not limited to a fixed list

### Solution Portfolios
- Synthesis must produce 3+ genuinely distinct solutions (configurable via `config.json` → `min_solutions`)
- Each solution has an archetype: `incremental` (1-3 sprints), `moderate` (3-6 sprints), `ambitious` (6+ sprints)
- Distinctiveness test: if removing a solution doesn't change the recommendation, the portfolio isn't divergent enough
- Each solution includes: archetype, ICE scores, evidence_refs, proceed_conditions, depends_on, solution_quality

### Tool Access
- 3-layer model: config defaults → roster overrides → agent capabilities
- Effective access = roster authorization ∩ agent capability
- When MCP tools are unavailable, agents degrade gracefully (note gaps, reduce confidence)
- See `docs/mcp-setup.md` for BigQuery, Tableau, Looker setup

### Skills
- `/agree` — Phase 0: refine opportunity framing with user
- `/assemble` — Phase 1: assemble investigation team, roster, tools, tracks
- `/orbit` — Phases 2-5: investigate → peer review → synthesize (portfolio) → dot-vote → decision brief → decide
- `/prototype` — standalone prototype variation + customer voice review
- `/execute` — Tech Lead: blast radius, task breakdown, Linear tasks
- `/explore` — parallel solution branches, lopsided OST

### Server & UI Architecture
- FastAPI app (`server/app.py`) serves a single-file HTML frontend (`server/static/index.html`)
- Design system CSS lives in `server/static/design-system.css` — reference doc at `docs/design-system.md`
- Real-time updates via WebSocket (`/ws/workspace/{opp_id}`) with reconnect/disconnect dropdown
- `CliBridge` generates `claude -p` commands; `AgentLauncher` manages subprocesses
- Phase 0 uses multi-turn conversation: each turn is a `claude -p` invocation that exits, user reply triggers `claude -p "message" --resume`
- Phase 2 is single-shot: spawns parallel agent subagents
- Dot-vote is parallel: spawns each rostered agent to score solutions simultaneously

### UI Conventions
- Use design tokens (`var(--token)`) for all colors, font sizes, radii — never hardcode
- Use existing CSS classes from `design-system.css` before creating new ones
- BEM-lite naming: `.component`, `.component--modifier`, `.component__element`
- Dynamic values (runtime agent colors, computed widths) stay as inline `style=`
- Data normalization helpers: `normalizeAssumption()` (JS) and `WorkspaceService._normalize_assumption()` (Python) handle string/object/corrupted assumption formats

### Server Endpoints (for reference)
- `POST /api/workspaces` — create workspace
- `PATCH /api/workspaces/{id}/opportunity` — update opportunity
- `GET /api/workspaces/{id}` — get workspace state (opportunity + contributions + reviews + artifacts + synthesis)
- `GET /api/workspaces/{id}/votes` — get all dot-vote files
- `GET /api/workspaces/{id}/decision-brief` — get decision brief markdown
- `POST /api/launch/{id}/start` — launch agent subprocess (staggered for parallel agents)
- `POST /api/launch/{id}/assemble` — launch /assemble skill (Phase 1)
- `POST /api/launch/{id}/dot-vote` — launch parallel dot-vote scoring
- `POST /api/launch/{id}/decision-brief` — launch decision brief generation
- `POST /api/launch/{id}/send` — send message (or resume via --resume)
- `POST /api/launch/{id}/approve` — send "yes" to approve plan mode
- `POST /api/launch/{id}/stop` — stop running subprocess
- `GET /api/launch/{id}/status` — poll subprocess output
- `GET /api/catalog/tools` — tool registry from config.json
- `GET /api/context` — list context layers
- `WS /ws/workspace/{id}` — real-time file change notifications

### Quality Standards
- Every schema has positive AND negative test fixtures
- Contributions must pass schema validation before being accepted
- Synthesis must reference specific contribution IDs, not summarize vaguely
- Solutions must include ICE scores grounded in evidence
- Solution portfolios must have 3+ distinct archetypes
- Counter-signals must be surfaced, not buried
- Dot-vote rationales must be at least 20 characters
