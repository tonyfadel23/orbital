---
name: assemble
description: >
  Assemble the investigation team for an Orbital opportunity. Reads context,
  recommends agent roster from templates, defines investigation tracks per agent,
  sets tool access. Interactive multi-turn. Use when user says "assemble the team",
  "set up the investigation", or after /agree completes.
compatibility:
  mcp_servers: []
---

# /assemble — Investigation Team Assembly

Recommend, configure, and lock the agent roster for an Orbital investigation.

## When to Use
- After `/agree` has produced a framed opportunity (status `"framed"`)
- "Assemble the team", "set up the investigation", "who should investigate this?"
- User wants to configure which agents, tools, and investigation tracks to use

## Prerequisites
- Workspace exists with `opportunity.json`
- Status must be `"framed"` (framing confirmed via `/agree`)
- Roster must be `null` (team not yet assembled)

## Flow

### Turn 1 — Analyze & Recommend

1. Read `{workspace}/opportunity.json` — validate status = `"framed"`, roster = `null`
2. Read `data/config.json`:
   - `roster_templates` — core, market_entry, technical_deep_dive, full_spectrum
   - `available_agents` — all agents with display names, roles, domains, default tool access
   - `tool_registry` — all available tools with MCP servers and capabilities
3. **Select agents from config** (do NOT read .md files yet):
   a. Match opportunity type/domain to a `roster_template`
   b. Include any agents with `always_included: true` (product)
   c. Review `role` and `domains` in `available_agents` to add/remove agents based on opportunity specifics
   d. Result: a shortlist of 3-5 agent function names
4. **Read only selected agent definitions** — `.claude/agents/{function}.md` for ONLY the shortlisted agents. Use full definitions to design investigation tracks, determine artifact expectations, and refine tool access.
5. Read context layers from `data/context/` (per `context_refs` on the opportunity)

Present to the user:

#### Context Alignment
2-3 bullets connecting the opportunity to the loaded context data. Show you understand the domain.

#### Recommended Template
Which roster template fits and why. Example: "I recommend **core** (product, design, data, engineering) because this is a UX + data hypothesis that needs both experience audit and baseline measurement."

#### Per-Agent Breakdown
For each recommended agent:

| | |
|---|---|
| **Function** | e.g., `design` |
| **Why needed** | Specific to THIS opportunity, not generic role description |
| **Investigation tracks** | 2-3 specific questions derived from the opportunity's assumptions and signals |
| **Expected artifacts** | JSON contribution + markdown artifact + any special outputs (prototypes, spreadsheets) |
| **Tool access** | Default from config + any additions/removals suggested for this investigation |

#### Tool Dependency Summary
- Which MCP servers are needed across all agents
- Which tools have `setup_required: true` (BigQuery, Looker, Tableau) — flag if not configured

#### One Question
"Is there a function missing? Should any be dropped? Want to adjust any investigation tracks?"

### Turn 2+ — Adjust

1. Process user's feedback:
   - Add or remove agents
   - Modify investigation tracks (change questions, add/remove tracks)
   - Adjust tool access per agent
   - Switch to a different roster template
2. **MUST update `{workspace}/opportunity.json` with current roster draft BEFORE responding** — use the Write tool
3. Append to `refinement_history`: `{"action": "roster_modified", "details": "added analyst agent for market sizing", "timestamp": "..."}`
4. Present updated roster with changes highlighted
5. Ask next adjustment question or confirm readiness

### Final Turn — Lock

When user confirms the roster:

1. Write final roster to `opportunity.json`:
   ```json
   "roster": [
     {
       "function": "product",
       "rationale": "Orchestrates investigation and synthesizes findings",
       "investigation_tracks": [
         {
           "track": "Opportunity framing",
           "question": "Is the Weekly Basket Builder persona well-defined enough to measure?",
           "expected_artifacts": ["product.md"]
         }
       ],
       "tool_access": ["google-drive", "gmail", "linear", "slack"]
     }
   ]
   ```
2. Update status: `"framed"` → `"assembled"`
3. Append to `refinement_history`: `{"action": "roster_confirmed", "timestamp": "..."}`
4. Print summary: "Team assembled. N agents, M investigation tracks. Ready — run `/orbit` to start the investigation."

## Tool Access Model

3-layer access control determines what each agent can actually use:

1. **Config defaults** — `config.json` → `available_agents.{fn}.default_tool_access`
2. **Roster overrides** — `opportunity.json` → `roster[].tool_access` (set during /assemble)
3. **Agent capabilities** — `.claude/agents/*.md` → what the agent knows how to use

**Effective access = roster authorization ∩ agent capability**

When recommending tool access, explain what each tool contributes to the agent's investigation tracks. Don't just list defaults — justify each tool for THIS opportunity.

## What This Skill Does NOT Do
- Does NOT frame the opportunity — that's `/agree`
- Does NOT run the investigation — that's `/orbit`
- Does NOT use interactive tools (AskUserQuestion, EnterPlanMode) — runs via `claude -p` + `--resume`

## Output
- Updated `opportunity.json` with:
  - `roster` array populated with function, rationale, investigation_tracks, tool_access per agent
  - `status` changed from `"framed"` to `"assembled"`
  - `refinement_history` entries for roster modifications and confirmation

## Next Step
Run `/orbit` to launch the investigation with the assembled team.
