# Quality Gates — 3-Layer Evaluation System

> Orbital v0.3.0 — ensures investigation quality through deterministic checks, LLM rubrics, and cross-agent synthesis evaluation.

---

## Overview

Orbital's agents produce structured contributions validated by JSON Schema. Schema validation checks structure — not whether findings are grounded, assumptions are covered, or solutions are genuinely distinct. The quality gate system adds semantic enforcement through three progressive layers:

| Layer | What | How | Cost | Speed |
|-------|------|-----|------|-------|
| **Layer 1** | Deterministic Gates | Pure Python checks at phase transitions | Free | Instant |
| **Layer 2** | LLM-as-Judge | Binary rubrics per finding via Claude Haiku | ~$0.01/finding | ~2s/finding |
| **Layer 3** | Agent-as-a-Judge | Cross-agent synthesis evaluation via judge subprocess | ~$0.10/run | ~60s |

All three layers are configurable, independently togglable, and surfaced in the UI.

---

## Layer 1 — Deterministic Gates

Pure Python checks that run at phase transitions. Fast, cheap, reproducible.

### Gates

| Gate | What It Checks | Default Threshold | Blocking |
|------|---------------|-------------------|----------|
| `assumption_coverage` | Every assumption in `opportunity.json` has ≥1 finding referencing it | `min_coverage: 1.0` (100%) | Yes |
| `confidence_floor` | No contribution has mean finding confidence below threshold | `threshold: 0.4` | Yes |
| `solution_distinctiveness` | Pairwise Jaccard similarity on `evidence_refs` below threshold | `max_jaccard: 0.7` | No |
| `evidence_freshness` | Evidence sources not older than N days | `max_age_days: 180` | No |
| `vote_quorum` | Minimum percentage of rostered agents have voted | `min_pct: 0.8` (80%) | Yes |
| `finding_density` | Each contribution has at least N findings | `min_findings: 3` | Yes |

### Algorithms

**assumption_coverage** — For each `opp.assumptions[].id`, scans all `contributions[].findings[].assumptions_addressed` arrays. Score = addressed_count / total_count. Passes if score >= `min_coverage`.

**confidence_floor** — Computes mean of `findings[].confidence` per contribution. Takes the minimum mean across all contributions. Passes if min mean >= `threshold`.

**solution_distinctiveness** — Computes pairwise Jaccard index on `solutions[].evidence_refs` sets from `synthesis.json`. Jaccard = |intersection| / |union|. Flags if any pair exceeds `max_jaccard`. Lower Jaccard = more distinct.

**evidence_freshness** — Parses `created_at` timestamps from evidence files. Compares against `now - max_age_days`. Non-blocking warning by default.

**vote_quorum** — Counts unique `voter_function` values in vote files, divides by roster length. Passes if ratio >= `min_pct`.

**finding_density** — Counts `findings[]` per contribution. Passes if every contribution has >= `min_findings`.

### GateResult Shape

Each gate returns:

```python
@dataclass
class GateResult:
    gate: str        # Gate name
    passed: bool     # Pass/fail
    score: float     # 0.0–1.0
    threshold: float # Configured threshold
    blocking: bool   # Blocks phase transition?
    details: str     # Human-readable explanation
```

### QualityReport

`evaluate_all(opp_id)` runs all enabled gates and returns:

```python
@dataclass
class QualityReport:
    opp_id: str
    gates: list[GateResult]
    # overall_passed: True if all blocking gates pass
    # overall_score: mean of all gate scores
```

### Phase Transition Integration

Gate checks run before two phase transitions in `server/routers/launch.py`:

| Endpoint | Phase Transition | Gates Checked |
|----------|-----------------|---------------|
| `POST /api/launch/{id}/dot-vote` | investigate → scoring | All enabled Layer 1 gates |
| `POST /api/launch/{id}/decision-brief` | scoring → decision_brief | All enabled Layer 1 gates |

Behavior depends on `blocking_mode` in config:

| Mode | Behavior |
|------|----------|
| `"block"` | HTTP 422 if any blocking gate fails |
| `"warn"` | Proceed, include warnings in response |
| `"off"` | Skip gate checks entirely |

---

## Layer 2 — LLM-as-Judge

Each finding is evaluated with 5 binary yes/no rubrics via a lightweight Claude API call.

### Rubrics

| Rubric | Question |
|--------|----------|
| `evidence_grounding` | Does this finding cite a specific, verifiable source? |
| `relevance` | Is this finding directly relevant to the opportunity? |
| `actionability` | Does this finding lead to a concrete next step or decision? |
| `non_obviousness` | Does this finding surface something non-obvious? |
| `self_review_quality` | Did the self-review demonstrate critical thinking? |

### How It Works

1. For each finding in each contribution, the service makes one API call per rubric
2. Each call sends the finding + opportunity context + self-review to Claude Haiku
3. Model responds with `{"pass": true/false, "reasoning": "..."}`
4. Finding score = fraction of rubrics passed (0.0–1.0)
5. Overall score = mean of all finding scores
6. Results persisted to `data/workspaces/{opp_id}/quality/llm-judge.json`

### Configuration

```json
"layer_2": {
  "enabled": true,
  "model": "claude-haiku-4-5-20251001",
  "pass_threshold": 0.6
}
```

### Prerequisites

- `ANTHROPIC_API_KEY` environment variable must be set
- If missing, Layer 2 degrades gracefully — returns `degraded: true` with reason

### Graceful Degradation

Layer 2 handles failures without crashing:

| Condition | Behavior |
|-----------|----------|
| No API key | Returns degraded report, reason: "No API key configured" |
| Layer 2 disabled in config | Returns degraded report, reason: "Layer 2 disabled in config" |
| API error mid-evaluation | Partial results returned, individual rubrics marked as failed |
| No contributions | Empty report (not degraded, just no data) |

### FindingJudgment Shape

```python
@dataclass
class FindingJudgment:
    finding_id: str
    rubrics: list[RubricResult]  # 5 rubric results
    # score: fraction passed (0.0–1.0)

@dataclass
class RubricResult:
    rubric: str      # Rubric name
    passed: bool     # Yes/No
    reasoning: str   # One-sentence explanation
```

---

## Layer 3 — Agent-as-a-Judge

A dedicated judge agent (separate from the investigation team) evaluates cross-agent synthesis quality.

### Rubrics

| Rubric | What It Evaluates |
|--------|-------------------|
| `contradictions_surfaced` | Are contradictions between agents explicitly named with evidence? |
| `minority_viewpoints` | Are dissenting views preserved in synthesis? |
| `evidence_based_recommendation` | Does the recommendation trace back to specific findings? |
| `risk_weighting` | Are risk/kill signals proportionally weighted? |
| `solution_diversity` | Does the portfolio cover genuinely different approaches? |

### How It Works

1. `POST /api/workspaces/{id}/quality/judge` spawns the judge agent subprocess
2. Agent reads `opportunity.json`, all contributions, `synthesis.json`, all votes, and artifacts
3. Agent evaluates each rubric with a 0.0–1.0 score and rationale
4. Results written to `data/workspaces/{opp_id}/quality/judge-evaluation.json`
5. Status polled via `GET /api/workspaces/{id}/quality/judge`

### Agent Definition

Located at `.claude/agents/quality-judge.md`. The judge agent:
- Is **not** part of the investigation team
- Is invoked after dot-voting, before or during the decide phase
- Does not suggest new solutions or findings — only evaluates what exists
- Scores each rubric independently with evidence references

### Output Format

```json
{
  "opp_id": "opp-...",
  "rubrics": {
    "contradictions_surfaced": {
      "score": 0.8,
      "rationale": "Two contradictions surfaced between data and engineering...",
      "evidence_refs": ["find-001", "find-003"]
    }
  },
  "overall_score": 0.72,
  "overall_passed": true,
  "timestamp": "2026-04-12T16:00:00Z"
}
```

---

## API Endpoints

### Per-Workspace Quality

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/workspaces/{id}/quality` | Full quality report (Layer 1 live, Layer 2+3 from files) |
| GET | `/api/workspaces/{id}/quality/gates` | Layer 1 gates only |
| POST | `/api/workspaces/{id}/quality/evaluate` | Trigger Layer 2 LLM evaluation |
| POST | `/api/workspaces/{id}/quality/judge` | Launch Layer 3 judge agent |
| GET | `/api/workspaces/{id}/quality/judge` | Poll judge agent status + results |

### Quality Config

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/quality/config` | Read quality gate configuration |
| PATCH | `/api/quality/config` | Update quality gate configuration |

### Response Shapes

**GET /quality** returns:
```json
{
  "opp_id": "opp-20260405-120000",
  "timestamp": "2026-04-12T16:00:00Z",
  "layer_1": {
    "overall_passed": false,
    "overall_score": 0.67,
    "gates": [
      {
        "gate": "assumption_coverage",
        "passed": true,
        "score": 1.0,
        "threshold": 1.0,
        "blocking": true,
        "details": "3/3 assumptions addressed"
      }
    ]
  },
  "layer_2": null,
  "layer_3": null
}
```

**PATCH /quality/config** accepts:
```json
{
  "enabled": true,
  "blocking_mode": "warn",
  "layer_1": {
    "confidence_floor": { "threshold": 0.5 }
  }
}
```

Merges into existing config — only supplied fields are updated.

---

## Configuration

Quality gates are configured in `data/config.json` under the `quality_gates` key:

```json
"quality_gates": {
  "enabled": true,
  "blocking_mode": "warn",
  "layer_1": {
    "assumption_coverage": { "enabled": true, "min_coverage": 1.0, "blocking": true },
    "confidence_floor": { "enabled": true, "threshold": 0.4, "blocking": true },
    "solution_distinctiveness": { "enabled": true, "max_jaccard": 0.7, "blocking": false },
    "evidence_freshness": { "enabled": true, "max_age_days": 180, "blocking": false },
    "vote_quorum": { "enabled": true, "min_pct": 0.8, "blocking": true },
    "finding_density": { "enabled": true, "min_findings": 3, "blocking": true }
  },
  "layer_2": {
    "enabled": true,
    "model": "claude-haiku-4-5-20251001",
    "pass_threshold": 0.6
  },
  "layer_3": {
    "enabled": true,
    "rubrics": ["strategic_alignment", "decision_readiness", "counter_signal_coverage"]
  }
}
```

### Key Settings

| Setting | Values | Effect |
|---------|--------|--------|
| `enabled` | `true`/`false` | Master toggle — disables all gates |
| `blocking_mode` | `"block"`, `"warn"`, `"off"` | Controls phase transition enforcement |
| Per-gate `enabled` | `true`/`false` | Toggle individual gates |
| Per-gate `blocking` | `true`/`false` | Whether this gate blocks phase transitions |

Settings are editable via the `#settings` route in the UI or the `PATCH /api/quality/config` endpoint.

---

## Services Architecture

### QualityGateService (Layer 1)

**File:** `server/services/quality_gates.py`
**Registered on:** `app.state.quality_gate_svc`
**Dependencies:** `WorkspaceService`, config dict

Methods:
- `evaluate_all(opp_id) → QualityReport` — runs all enabled gates
- `can_transition(opp_id, phase) → (bool, blockers, warnings)` — used by launch router
- `check_{gate_name}(opp_id) → GateResult` — individual gate checks

### LLMJudgeService (Layer 2)

**File:** `server/services/llm_judge.py`
**Registered on:** `app.state.llm_judge_svc`
**Dependencies:** `WorkspaceService`, config dict, `ANTHROPIC_API_KEY`

Methods:
- `evaluate_all(opp_id) → LayerTwoReport` — evaluates all findings
- `evaluate_finding(finding, self_review, opp_context) → FindingJudgment` — single finding

Results persisted to `quality/llm-judge.json`.

### JudgeAgentService (Layer 3)

**File:** `server/services/judge_agent.py`
**Registered on:** `app.state.judge_agent_svc`
**Dependencies:** `CliBridge`, `AgentLauncher`

Methods:
- `launch_judge(opp_id) → bool` — spawns judge subprocess
- `get_judge_status(opp_id) → {running, results}` — poll status

Results written by agent to `quality/judge-evaluation.json`.

---

## UI Components

### Quality Tab (Investigate Phase Sidebar)

Fourth tab in the investigation sidebar. Shows:
- **Overall score** — color-coded (green > 0.7, amber 0.5–0.7, red < 0.5)
- **Gate cards** — stack of `.quality-gate` cards, each with name, pass/fail pill, score, expandable detail
- **Layer 2 results** — finding-level rubric badges (if evaluated)
- **Layer 3 results** — synthesis quality card (if judged)
- **Trigger buttons** — "Run LLM Judge" and "Run Agent Judge"

### Quality Strip (Sidebar Header)

Compact quality summary below the opportunity title. Shows pass/fail counts as `.gate-pill` badges. Clicking navigates to the Quality tab.

### Contribution Quality Badges (Evidence Tab)

In the Evidence tab's contribution list, Layer 2 scores appear as `4/5` badges on each contribution item.

### Evidence Freshness Warning

Evidence cards in the chat feed show a `.gate-pill--fail` badge with age (e.g., "Stale (183d)") when evidence exceeds the freshness threshold.

### Settings Page (`#settings`)

Dedicated route with form cards for:
- Quality Gates — master toggle, blocking mode selector
- Layer 1 — per-gate toggles and threshold inputs
- Layer 2 — enable toggle, model selector
- Layer 3 — enable toggle
- Save button → `PATCH /api/quality/config`

### CSS Classes

See `docs/design-system.md` — Quality Gates section for the full class reference.

---

## Workspace Structure

Quality results are stored in a `quality/` subdirectory within each workspace:

```
data/workspaces/{opp-id}/
├── opportunity.json
├── contributions/
├── reviews/
├── synthesis.json
├── votes/
├── artifacts/
├── evidence/
└── quality/
    ├── evaluation.json         # Layer 1 results (saved by QualityGateService)
    ├── llm-judge.json          # Layer 2 results (saved by LLMJudgeService)
    └── judge-evaluation.json   # Layer 3 results (written by judge agent)
```

---

## Schema

Quality evaluation results follow `schemas/quality-evaluation.schema.json`. This schema validates the persisted evaluation files in the `quality/` directory.
