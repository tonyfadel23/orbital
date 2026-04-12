# Orbital

A decision operating system that runs synthetic Design Sprints using AI agent teams. Instead of one AI giving one answer, Orbital assembles a cross-functional team of AI agents that investigate an opportunity in parallel, produce a portfolio of distinct solutions, score them from every functional perspective, and package the result as a decision brief for leadership.

## How It Works

```
/agree     →  Frame the opportunity with the PM
/assemble  →  Pick the team (data, design, engineering, etc.)
/orbit     →  Investigate → Review → Synthesize → Dot-Vote → Decision Brief → Decide
```

Each agent (data, design, engineering, analyst, financial, etc.) investigates from their function's perspective, writes structured findings, and reviews each other's work. The result isn't a single recommendation — it's a ranked portfolio of 3+ solutions spanning incremental to ambitious, scored by every agent on the team.

## Quick Start

### Prerequisites
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- Python 3.12+

### Run the Server

```bash
cd code/orbital
pip install -r requirements.txt
python3 -m server.app
```

Server starts at `http://localhost:8000`. The UI lets you create opportunities, launch investigations, and monitor agent progress in real-time.

### Run an Investigation (CLI)

```bash
# Phase 0: Frame the opportunity
claude /agree

# Phase 1: Assemble the team
claude /assemble

# Phases 2-5: Run the full cycle
claude /orbit
```

### Run Tests

```bash
# All Python tests (server, services, schemas)
python3 -m pytest tests/ -v

# Schema validation only
bash tests/schemas/test-all.sh
```

## The Orbital Cycle

| Phase | Name | What Happens |
|-------|------|--------------|
| 0 | AGREE | Refine opportunity framing with user |
| 1 | ASSEMBLE | Recommend team roster, user approves |
| 2 | INVESTIGATE | Parallel agents explore from their function |
| 3 | PEER REVIEW | Cross-functional challenge of findings |
| 4 | SYNTHESIZE | Build portfolio of 3+ distinct solutions |
| 4b | DOT-VOTE | Each agent scores all solutions |
| 4c | DECISION BRIEF | Generate shareable document for leadership |
| 5 | DECIDE | Human picks solutions, creates tasks |

## Solution Portfolios

Synthesis produces 3+ genuinely distinct solutions, each tagged with an archetype:

- **Incremental** — builds on what exists, 1-3 sprints
- **Moderate** — requires new capabilities, 3-6 sprints  
- **Ambitious** — new infrastructure or paradigm, 6+ sprints

## Dot-Voting

After synthesis, every agent on the roster scores all solutions from their function's perspective. Engineering scores on feasibility/effort/risk. Design scores on UX coherence. Data scores on measurability. The result is a heat map showing where consensus and divergence live.

## Agent Catalog

13 agent types available. The product agent is always included. Others are assembled per opportunity:

| Agent | Focus |
|-------|-------|
| Product | Orchestrator — frames, synthesizes, generates brief |
| Design | UX audit, prototyping, patterns |
| Data | Baselines, funnels, segments |
| Engineering | Feasibility, architecture, effort |
| Analyst | Market sizing, competitive landscape |
| Financial | Unit economics, ROI |
| Data-Science | Predictive models, experiment design |
| Legal | Regulatory, compliance |
| Brand-Marketing | Positioning, GTM |
| UX-Writing | Content strategy, tone |
| Commercial-Strategy | Partnerships, marketplace |
| Customer Voice | VoC synthesis, prototype evaluation |
| Tech Lead | Blast radius, task breakdown |

## Project Structure

```
schemas/          JSON Schema definitions (7 schemas)
.claude/agents/   Agent definitions (13 agents)
skills/           Skill definitions (6 skills)
server/           FastAPI server + WebSocket + frontend
data/             Config, context layers, workspaces
tests/            Schema + server tests (186 tests)
docs/             MCP setup, design system reference
```

## Documentation

- **[ORBITAL.md](ORBITAL.md)** — Full system design, data model, architecture
- **[CLAUDE.md](CLAUDE.md)** — Development conventions and project instructions
- **[docs/mcp-setup.md](docs/mcp-setup.md)** — BigQuery, Tableau, Looker integration
- **[docs/design-system.md](docs/design-system.md)** — UI design tokens and components
