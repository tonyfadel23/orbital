---
name: prototype
description: >
  Create and evaluate prototype variations for a solution concept. Uses the
  company design system via Figma MCP and evaluates variations through a
  Customer Voice Reviewer. Can run standalone or as part of an Orbital cycle.
  Use when user says "prototype this", "explore design options", "create
  variations", "show me UX options", or needs customer voice validation on
  design directions.
compatibility:
  mcp_servers:
    - figma
    - google-workspace
    - miro
---

# /prototype — Prototype Variation & Customer Voice Review

Create multiple prototype variations for a solution concept and evaluate them through the lens of real customer voices.

## When to Use
- Have a solution concept that needs UX exploration
- Want to compare 2-4 different approaches before committing
- Need customer voice validation on design directions
- "Prototype this", "explore design options", "create variations"

## Modes
- **Standalone** — run independently with a solution description
- **In-cycle** — runs as Phase 2b during an Orbital investigation (triggered automatically when Design is on the roster)

## Flow

### 1. Input
- Solution description — what are we building and for whom
- Target persona — who is this for (if known)
- Design constraints — platform, existing patterns, brand rules
- Context — prior research, data findings, competitive examples (if available)

### 2. Variation Generation (Design Agent)

Design Agent creates 2-4 prototype variations:

**Using Figma MCP:**
- Pull components from company design system
- Create variations that explore meaningfully different UX approaches
- Each variation must differ in structure or interaction model, not just styling

**Using HTML prototypes:**
- Generate interactive HTML prototypes for quick exploration
- Useful for flow-based variations or when Figma access is limited

**Variation requirements:**
- Each explores a distinct approach (not cosmetic tweaks)
- All use company design system components
- Each includes a brief rationale for the approach taken
- Accessibility considerations noted

### 3. Customer Voice Review (Customer Voice Reviewer)

The Customer Voice Reviewer agent:

1. **Synthesizes VoC data** from available sources:
   - User interviews (from Google Drive)
   - App store reviews
   - NPS verbatims
   - Support ticket themes
   - Survey responses

2. **Builds a customer need map:**
   - What customers want (explicit needs)
   - What they struggle with (pain points)
   - What they don't say but demonstrate (behavioral needs)
   - Mental models and expectations

3. **Evaluates each variation:**
   - Alignment with customer needs
   - Friction points customers would encounter
   - Emotional resonance
   - Learnability and familiarity

4. **Produces ranked evaluation:**
   - Per-variation scorecard with reasoning
   - Overall ranking with recommendation
   - Gaps — what no variation addresses

### 4. Output

**`artifacts/prototype-review.md`:**
- Customer voice synthesis with sources
- Per-variation evaluation
- Ranked recommendation with reasoning
- Identified gaps for iteration

**Prototype files:**
- Figma prototypes (linked)
- HTML prototypes (in artifacts/)

## Example Usage

```
/prototype

Solution: Pro Savings Dashboard — show users how much they've saved with Pro
Persona: Deal Hunter segment (price-sensitive, high order frequency)
Constraints: Must fit existing Pro subscription screen, RTL support for Arabic
```

The skill will:
1. Design Agent creates 3 variations (e.g., summary card, timeline view, gamified tracker)
2. Customer Voice Reviewer evaluates each against Deal Hunter needs
3. Output: ranked recommendation with customer voice backing

## Troubleshooting

**Figma MCP not connected:**
- Variations can still be created as HTML prototypes when Figma access is unavailable
- Note the limitation in the output — Figma prototypes using the actual design system are preferred

**No VoC data available:**
- Customer Voice Reviewer should state the data gap explicitly rather than inventing needs
- Reduce confidence in the evaluation and recommend gathering customer data before proceeding

**Variations are too similar:**
- Each variation must differ in structure or interaction model, not just styling
- If the Design Agent produces cosmetic-only differences, reject and re-prompt with specific divergence criteria

**Design system components missing:**
- Document missing components in `artifacts/design.md` under design system gap analysis
- Use closest available components and note the gap for the design system team
