---
name: agree
description: >
  Refine an opportunity with the user before investigation begins. Loads context
  layers, surfaces gaps, helps frame the hypothesis/problem/question with assumptions
  and signals. Multi-turn conversation. Use when user says "let's frame this",
  "agree on this", or starts with a vague product idea.
compatibility:
  mcp_servers: []
---

# /agree — Opportunity Framing

Refine a vague product idea into a framed investigation opportunity through a multi-turn conversation.

## When to Use
- User has a hypothesis, problem, or strategic question but it's not yet framed
- "Let's frame this", "agree on this", "I have an idea about..."
- Starting from a gut feeling, signal, or vague observation
- Before assembling a team — framing must be solid first

## Prerequisites
- A workspace created via `POST /api/workspaces` with at least a title
- Opportunity status must be `"aligning"` or `"assembled"`

## Flow

### Step 0 — Scope Check
Before drafting, confirm these four dimensions with the user. Do not assume broad framing.
1. **Target segment** — new users, current users, or a specific cohort
2. **Geographic scope** — UAE only, multi-market, or specific country
3. **Investigation type** — discovery (what's the opportunity?) vs optimization (how do we improve X?)
4. **Key metric** — the specific conversion point (e.g., add-to-cart rate, not "engagement")

If any are missing or vague, ask before proceeding. One question per gap.

5. **Frame as HMW** — Rewrite the title as a **How Might We** question. HMW questions open solution space — specific enough to constrain the investigation but broad enough to invite multiple approaches. Examples:
   - "HMW make fresh groceries a habitual purchase on tMart?"
   - "HMW reduce first-order drop-off for new users in KSA?"
   - "HMW shift Q-commerce from promo-dependent to organically retained?"

### Turn 1 — Context & Framing
1. Read `{workspace}/opportunity.json`
2. Load context layers from `data/context/`:
   - `L1/global.json` — always loaded
   - `L2a/{business_line}.json` — matched from opportunity domain
   - `L2b/{market}.json` — matched from opportunity scope
3. Surface context sufficiency — what's missing that would change the investigation
4. Present the framing:
   - **What I see in the context** — 2-3 bullets connecting the idea to real data/strategy from context files
   - **My initial read** — 1-2 sentences on how to frame this as an investigation
   - **To sharpen the framing** — ONE specific question: challenge an assumption, surface a gap, or test scope

### Turn 2+ — Refine
1. Process user's answer
2. **MUST update `{workspace}/opportunity.json` BEFORE producing response** — use the Write tool to update:
   - `title` — sharpened as a HMW question
   - `type` — hypothesis / problem / question
   - `description` — refined
   - `assumptions` — each with id, content, status, importance
   - `success_signals` — what evidence means proceed
   - `kill_signals` — what evidence means stop
   - `context_refs` — which context layers are relevant
3. Append to `refinement_history`: `{"action": "reframed|assumption_added|context_added", "details": "...", "timestamp": "..."}`
4. Share what was updated and why
5. Ask the next refining question — one per turn

### Exit — Framing Complete (3-5 turns)
When the framing is solid:
- `opportunity.json` has: clear HMW title, typed opportunity, populated assumptions (3-5), success signals, kill signals, context refs
- Status remains `"assembled"` (set during workspace creation or first confirm)
- Recommend: "Framing is solid. Run `/assemble` to set up the investigation team."

## What This Skill Does NOT Do
- Does NOT assemble a roster — that's `/assemble`
- Does NOT launch agents — that's `/orbit`
- Does NOT create the workspace — that's the UI / API
- Does NOT use interactive tools (AskUserQuestion, EnterPlanMode) — runs via `claude -p` + `--resume`

## Output
- Updated `opportunity.json` with framing fields populated
- `refinement_history` tracking all changes across turns

## Next Step
Run `/assemble` to recommend and lock in the investigation team.
