---
name: execute
description: >
  Take approved Orbital solutions and produce an implementation plan. Tech Lead
  agent evaluates blast radius, repo readiness, and dependencies, then creates
  Linear tasks assigned to people or coding agents. Use when user says "execute
  these solutions", "create tasks", "plan implementation", or has approved
  solutions from an Orbital cycle that need to become Linear issues.
compatibility:
  mcp_servers:
    - linear
    - github
    - atlassian
---

# /execute — Implementation Planning & Task Creation

Take approved solutions from an Orbital cycle and turn them into an executable implementation plan with Linear tasks.

## When to Use
- After an Orbital cycle with approved solutions
- "Execute these solutions", "create tasks", "plan implementation"
- Need blast radius analysis before starting work

## Prerequisites
- Completed Orbital cycle with `synthesis.json` containing approved solutions
- Linear access for task creation
- GitHub access for repo analysis

## Flow

### 1. Input
- Path to workspace with completed synthesis (or active workspace)
- Which approved solutions to plan (all approved, or specific IDs)

### 2. Solution Evaluation (Tech Lead Agent)

For each approved solution, the Tech Lead evaluates:

**Blast Radius:**
- How many repos/services/teams are affected
- Integration point complexity (API boundaries, shared data)
- Data migration requirements
- Rollback complexity — can this be safely undone?

**Repo Readiness:**
- Test coverage in affected areas (via GitHub)
- CI/CD health — recent failures, build times
- Recent merge velocity — is the team actively working here?
- Code quality signals — complexity hotspots, tech debt markers

**Dependency Mapping:**
- What must ship first (sequential dependencies)
- What can run in parallel
- Cross-team dependencies (via Jira/Linear)
- External dependencies (APIs, vendors, infrastructure)

**Risk Assessment:**
- Integration risk — system boundary crossings
- Data risk — migration, backwards compatibility
- Rollback risk — reversibility of changes
- Timeline risk — what could cause delays

### 3. Task Breakdown

For each solution:
1. Break into Linear sub-issues with clear scope
2. Estimate effort per task: **S** (< 1 day), **M** (1-3 days), **L** (3-5 days)
3. Classify each task:
   - **Agent-ready** — clear spec, good test coverage, isolated scope → assign to coding agent
   - **Human-required** — ambiguous scope, cross-team coordination, architectural decisions → assign to engineer
4. Sequence tasks respecting dependencies
5. Identify parallel tracks

### 4. Linear Task Creation

Create issues in Linear via `mcp__claude_ai_Linear__save_issue`:
- Parent issue per solution (linked to synthesis)
- Sub-issues for each task
- Labels: effort size, agent-ready/human-required
- Dependencies between tasks
- Assignments to team members or coding agent flag

### 5. Output

**Linear issues:** Created with full breakdown, estimates, dependencies, assignments.

**`artifacts/execution-plan.md`:**
- Blast radius report per solution
- Sequenced implementation plan with dependency graph
- Repo readiness assessment
- Risk register with mitigations
- Agent-vs-human assignment rationale
- Estimated timeline with confidence ranges

## Example Usage

```
/execute

Workspace: data/workspaces/opp-20260410-100000/
Solutions: sol-001 (Pro Savings Dashboard), sol-002 (30-Day Savings Streak)
```

The skill will:
1. Tech Lead evaluates both solutions against actual repos and team state
2. Creates Linear parent issues + sub-tasks
3. Produces execution plan with blast radius, dependencies, and timeline

## Troubleshooting

**No approved solutions in synthesis:**
- Verify `synthesis.json` contains solutions with status `"approved"`
- If no solutions are approved, the user needs to run Phase 5 (DECIDE) of the Orbital cycle first

**GitHub repos not accessible:**
- Repo readiness assessment requires GitHub access — if unavailable, note the gap and base estimates on available information
- Reduce confidence in effort estimates and flag as needing engineering review

**Linear task creation fails:**
- Check Linear MCP connection and team/project permissions
- Verify the target team exists and the user has write access
- Fallback: produce the task breakdown in `artifacts/execution-plan.md` for manual creation

**Effort estimates seem off:**
- Ensure the Tech Lead is examining actual repo complexity, not estimating from descriptions
- Check that CI/CD health and recent merge velocity are factored in
- Estimates should include uncertainty ranges (e.g., "M-L" not just "M")

**Agent-vs-human assignment unclear:**
- Agent-ready tasks need: clear spec, good test coverage, isolated scope
- When in doubt, assign to human — false agent assignment wastes more time than manual work
