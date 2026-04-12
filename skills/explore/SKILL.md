---
name: explore
description: >
  Generates parallel solution branches from an opportunity for deeper
  investigation. Creates scoped agent teams per branch and produces a
  comparative synthesis with ICE scores. Like a lopsided Opportunity-Solution
  Tree — explore multiple directions simultaneously. Use when user says
  "explore more options", "branch this out", "what else could we do", or
  wants to investigate multiple viable solution paths in parallel.
compatibility:
  mcp_servers:
    - google-workspace
    - figma
    - github
    - linear
    - slack
---

# /explore — Parallel Solution Branches

Branch an opportunity into multiple parallel solution tracks for deeper investigation. Each branch gets a scoped agent team and produces its own mini-synthesis for comparative evaluation.

## When to Use
- After an Orbital cycle when you want to explore more directions
- When an opportunity has multiple viable solution paths worth investigating in parallel
- "Explore more options", "branch this out", "what else could we do?"
- Alternative to a single linear investigation when the solution space is wide

## Modes

### Post-Cycle Expansion
Takes findings from a completed Orbital cycle and branches into 3-5 parallel solution tracks. Uses existing evidence as the foundation — each branch goes deeper on a specific direction.

### From-Start Alternative
Skip the single-synthesis path. Go straight to multi-branch investigation from a confirmed opportunity. Useful when you already know the solution space is wide.

## Flow

### 1. Input
- **Post-cycle:** Path to workspace with completed synthesis
- **From-start:** Confirmed opportunity (after Phase 0 AGREE)

### 2. Branch Generation (Product Agent)

Product Agent identifies distinct solution directions:

**Post-cycle:**
- Analyzes existing synthesis for branching opportunities
- Each branch must represent a meaningfully different approach
- Branches can build on existing solutions or explore new ones

**From-start:**
- Analyzes opportunity and context layers
- Generates 3-5 distinct solution hypotheses
- Each must attack the opportunity from a different angle

**Per branch, define:**
- Branch title and hypothesis
- How it differs from other branches
- Which agents are needed (can be a subset of full roster)
- Key questions to answer
- Success criteria for this branch

### 3. Per-Branch Mini-Investigation

Each branch gets:
- A scoped agent team (often smaller than full roster — 2-3 agents)
- Specific investigation questions
- Shared context from the parent opportunity + any prior cycle evidence

Each branch produces:
- Agent contributions (JSON + markdown)
- Branch-level mini-synthesis with ICE score
- Key evidence for/against this direction

### 4. Comparative Synthesis (Product Agent)

Product Agent compares all branches:
- ICE score comparison
- Evidence strength per branch
- Risk profile comparison
- Resource requirements
- Overlap and synergies between branches
- Recommended starting point

### 5. Output

**Branch structure:**
```
data/workspaces/{opp-id}/
├── opportunity.json
├── branches/
│   ├── branch-001-savings-dashboard/
│   │   ├── contributions/
│   │   ├── artifacts/
│   │   └── branch-synthesis.json
│   ├── branch-002-gamified-streaks/
│   │   └── ...
│   └── branch-003-social-savings/
│       └── ...
├── explore-synthesis.md   ← comparative analysis
└── synthesis.json         ← original (if post-cycle)
```

**`explore-synthesis.md`:**
- Branch comparison matrix
- ICE scores side by side
- Evidence strength assessment
- Risk comparison
- Recommended path with rationale
- Dependencies between branches (if any)

### 6. Decision (interactive)

Present the comparison to the user:
- Which branches to pursue (approve → `/execute`)
- Which to defer or kill
- Whether to sequence branches or run in parallel
- Whether any branches should merge

## Connection to Product OS

Each approved branch becomes a Solution node in the Opportunity-Solution Tree, feeding into the existing pipeline:
```
Outcome → Opportunity → [Branch = Solution] → Experiment → Result
```

## Example Usage

```
/explore

Mode: post-cycle
Workspace: data/workspaces/opp-20260410-100000/

The completed synthesis identified 3 solutions. Let's explore 2 additional
directions: a referral-based approach and a subscription tier restructure.
```

The skill will:
1. Product Agent defines 5 branches (3 existing + 2 new directions)
2. Each branch gets a scoped 2-3 agent team
3. Comparative synthesis ranks all branches
4. User decides which to pursue

## Troubleshooting

**Branches are too similar:**
- Each branch must represent a meaningfully different approach to the opportunity
- If branches overlap, merge them and generate a genuinely distinct alternative

**Branch agent team too large:**
- Branches should use 2-3 agents, not the full roster — keep investigation focused
- If more agents are needed, the branch may be too broad and should be split

**Prior cycle evidence not loading:**
- Verify the workspace path is correct and `synthesis.json` exists
- Check that the synthesis has status `"accepted"` and contains approved solutions

**Comparative synthesis lacks differentiation:**
- Ensure each branch-level mini-synthesis has its own ICE score and evidence summary
- The Product Agent should explicitly compare risk profiles and resource requirements, not just scores

**Too many branches (>5):**
- Limit to 3-5 branches to keep the investigation tractable
- Prioritize branches with the highest expected information value
