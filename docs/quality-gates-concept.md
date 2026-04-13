# Quality Gates — Design Philosophy

> How Orbital knows the difference between a thorough investigation and a checkbox exercise.

---

## The Problem

AI agents are fast. They produce structured JSON, cite sources, and follow instructions. But speed and structure don't guarantee quality. An agent can file six findings in thirty seconds — all technically valid, all schema-compliant — and still miss the point entirely.

Schema validation catches malformed data. It doesn't catch shallow thinking.

Orbital needed a system that could answer a harder question: **did the investigation actually earn the right to move forward?**

---

## The Design

Quality gates are checkpoints between investigation phases. They enforce a simple principle: *the work must be good enough before the process advances.*

Three layers, each asking a different kind of question:

### Layer 1 — Did the team do the work?

Deterministic checks. No AI, no judgment calls. Pure arithmetic.

- Did every assumption get at least one finding? (assumption coverage)
- Is any agent's confidence suspiciously low? (confidence floor)
- Are the proposed solutions actually different from each other? (solution distinctiveness)
- Is the evidence recent enough to act on? (evidence freshness)
- Did enough agents vote? (vote quorum)
- Did each agent contribute enough findings? (finding density)

These gates are binary and instant. They catch the obvious gaps — the kind a team lead would spot in the first thirty seconds of a review.

### Layer 2 — Is each finding worth something?

An LLM evaluates every individual finding against five rubrics:

- **Grounded** — Does it cite a real, verifiable source?
- **Relevant** — Does it actually relate to the opportunity?
- **Actionable** — Does it lead somewhere concrete?
- **Non-obvious** — Does it tell us something we didn't already know?
- **Self-aware** — Did the agent's own review catch any weaknesses?

This is the equivalent of a senior reviewer reading each insight and asking: "So what? Why does this matter?" A finding that scores 2/5 might technically pass schema validation, but it's not contributing real signal.

### Layer 3 — Does the whole hold together?

A dedicated judge agent — separate from the investigation team — reads everything and evaluates the synthesis as a whole:

- Were contradictions between agents surfaced, or papered over?
- Did minority viewpoints survive into the final synthesis?
- Can the recommendation be traced back to specific evidence?
- Are risks weighted proportionally, or buried?
- Do the proposed solutions represent genuinely different bets?

This is the hardest layer. It catches the failure mode where every individual piece looks fine but the assembled picture is misleading — consensus without substance, recommendation without grounding.

---

## Why Three Layers

Each layer costs more and catches different problems:

| Layer | Catches | Misses | Cost |
|-------|---------|--------|------|
| 1 | Missing work, structural gaps | Quality of individual findings | Free |
| 2 | Weak findings, ungrounded claims | Cross-agent synthesis issues | ~$0.01/finding |
| 3 | Groupthink, buried dissent, hollow consensus | Nothing (most thorough) | ~$0.10/run |

The progression is deliberate. Layer 1 is a filter — if agents haven't even covered all the assumptions, there's no point evaluating finding quality. Layer 2 refines — now we know the work exists, is it actually good? Layer 3 synthesizes — the parts are strong, but does the whole tell an honest story?

Running all three layers in sequence costs roughly $0.15 and takes about 65 seconds. Running Layer 3 on an investigation that fails Layer 1 would waste both money and time. The layers are a funnel: cheap and fast at the top, expensive and thorough at the bottom.

---

## Blocking vs. Warning

Not every quality signal should stop the process. The system distinguishes between:

- **Blocking gates** halt phase transitions. If assumption coverage fails, you cannot launch dot-voting. The investigation isn't ready.
- **Warning gates** flag concerns without stopping progress. If evidence freshness fails, the team should know — but stale evidence might still be the best available.

Teams can configure three enforcement modes:

- **Block** — failing blocking gates return HTTP 422. Full stop.
- **Warn** — gates run, failures are surfaced, but the process continues.
- **Off** — skip checks entirely. For rapid prototyping or time-boxed sprints.

The default is `warn`. This gives teams quality visibility without creating a bottleneck during early experimentation. As investigations mature, switching to `block` prevents premature decisions from reaching leadership.

---

## The Judge Is Not on the Team

Layer 3's judge agent is architecturally separate from the investigation team. This is intentional.

Investigation agents have a built-in incentive to produce findings that support their function's perspective. The data agent favors data-backed arguments. The engineering agent gravitates toward technical risk. This is correct behavior — it's why Orbital uses multiple agents in the first place.

But the synthesis must rise above individual perspectives. A judge who participated in the investigation would carry the same biases into their evaluation. By bringing in a separate agent with a different prompt, different rubrics, and no stake in the findings, the system gets an independent assessment of whether the synthesis is trustworthy.

The judge doesn't suggest new solutions or add findings. It only evaluates what exists. This constraint keeps the quality system from becoming another opinion in the room.

---

## Configurable by Design

Every aspect of quality gates is tunable:

- Master toggle to disable all gates
- Per-gate enable/disable
- Per-gate thresholds (confidence floor at 0.4 vs 0.6, quorum at 80% vs 100%)
- Per-gate blocking status (make evidence freshness blocking, or make confidence floor advisory)
- Layer 2 and 3 independently togglable
- Blocking mode switchable at any time

This matters because different investigations have different quality needs. A quick competitive scan doesn't need Layer 3 synthesis evaluation. A high-stakes market entry decision should run all three layers with blocking mode on.

The settings are accessible in the UI and via API, so teams can adjust quality thresholds as they learn what level of rigor their decisions actually require.

---

## What Quality Gates Are Not

Quality gates don't replace human judgment. They don't guarantee correct decisions. They don't catch every possible failure mode.

What they do: make the quality of an AI-driven investigation visible and enforceable. Before quality gates, the only signal was "the agents finished." Now the signal is "the agents finished, and here's evidence that their work meets a measurable standard."

That shift — from "done" to "done well enough to act on" — is the entire point.
