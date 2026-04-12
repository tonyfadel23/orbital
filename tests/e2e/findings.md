# Orbital E2E Test Findings

**Date:** 2026-04-12
**Viewport:** 1440x900 (desktop), 375x812 (mobile)
**Server:** http://localhost:8000
**State:** 8 existing workspaces (mixed statuses)

---

## Summary

| Category | Pass | Fail | Skip | Notes |
|----------|------|------|------|-------|
| Dashboard (Tests 1-2) | 1 | 0 | 1 | Empty state skipped (requires clean DB) |
| Agree Phase (Tests 3-4) | 1 | 0 | 1 | First message skipped (requires live agent) |
| Evidence (Tests 5-10) | 0 | 0 | 6 | All require live agent subprocess |
| Assemble (Tests 11-13) | 0 | 0 | 3 | Require live agent + phase transition |
| Investigate (Tests 14-15) | 1 | 0 | 1 | Graph interactions skipped (canvas-based) |
| Navigation (Tests 16-19) | 4 | 0 | 0 | All pass |
| Deletion (Test 20) | 1 | 0 | 0 | Both cancel + confirm paths verified |
| Responsive (Test 17) | 1 | 0 | 0 | Mobile stacking works |
| **Running Processes** | 0 | 1 | 0 | **New feature — 404 on running server** |

**Overall: 9 pass, 1 fail, 12 skipped**

---

## Test Results

### Test 2: Dashboard — With Workspaces (PASS)

- Heading shows "8 Investigations"
- "+ New Investigation" button visible and clickable
- 8 `.workspace-card` elements rendered in 3-column grid
- Each card shows: type pill, status pill, title, opp-id
- Status pills: `investigating` (green), `open` (cyan), `agreed` (muted)
- Type pills: `hypothesis`, `question`, `market_expansion`
- Delete buttons (trash icon) visible on each card
- Clicking card navigates to `#orb/{opp_id}`

**Screenshot:** `dashboard-with-workspace.png`

---

### Test 3: New Investigation — Agree Phase (PASS)

- Route: `#orb/new`
- Split layout renders: left panel (chat) + right panel (agree cards)
- Left panel:
  - "← Dashboard" back link visible (but overlapped by nav — see bug)
  - Empty state: "New Investigation" title + hint text
  - Chat input bar with placeholder "Tell me what to investigate..."
  - Send button visible
- Right panel — 4 setup cards:
  - **Progress:** "Refining" active, "Assembling" and "Ready" inactive
  - **Opportunity:** placeholder hint "Describe your investigation to begin..."
  - **Context:** placeholder hint "Agent will load relevant context..."
  - **Connectors:** 12 connector toggles (figma, github, google-drive, google-sheets, gmail, linear, slack, jira, bigquery, looker, tableau, miro) — all enabled
- No Roster card present (correct for agree phase)

**Screenshot:** `agree-phase-empty.png`

---

### Test 14: Investigate Phase — Graph + Sidebar (PASS)

- Route: `#orb/opp-20260405-120000`
- Left panel: `<canvas>` graph rendering with 70 nodes, 69 links, 9 agents
- Agent legend with colored labels: data, design, engineering, data.md, design.md, grocery, measurement, product.md, substitution
- Graph controls: zoom-in (+), recenter, zoom-out (-)
- Right panel sidebar:
  - Status pill: "INVESTIGATING"
  - Opp ID in monospace
  - Edit button
  - Title as heading
  - Tab interface: OVERVIEW | EVIDENCE | AGENTS
  - Overview tab shows:
    - Synthesis card: "Complete" status with summary
    - Assumptions (5) with importance levels (CRITICAL, HIGH, MEDIUM) and status (untested)

**Screenshot:** `investigate-phase.png`

---

### Test 16: Resume Existing Investigation (PASS)

- Navigating to `#orb/opp-20260412-122621` (status: agreed) loads agree phase
- Opportunity card fully populated: title, description, 3 assumptions, 3 success signals, 3 kill signals
- Progress card shows "Refining" as active (correct — agreed means still in refine cycle)
- Chat shows "Edit Investigation" empty state with "What would you like to refine?" placeholder

**Screenshot:** `resume-investigation-agreed.png`

---

### Test 17: Responsive Layout — Mobile (PASS)

- Viewport: 375x812
- Layout switches to single column (stacked vertically)
- Chat section on top, cards stack below
- Chat input and send button remain accessible
- Connector toggles wrap correctly
- All cards visible via scroll

**Screenshot:** `mobile-agree-phase.png`

---

### Test 18: Navigation — Back to Dashboard (PASS)

- Clicking ORBITAL logo navigates from investigation to dashboard
- Dashboard re-renders with correct workspace count
- Note: "← Dashboard" back link is visually present but **intercepted by the nav bar** (see Bug #1)

---

### Test 19: Hash Routing (PASS)

| Route | Result |
|-------|--------|
| `#` | Dashboard renders with workspace grid |
| `#orb/new` | Agree phase with empty state |
| `#orb/opp-20260405-120000` | Investigate phase with graph |
| `#orb/opp-20260412-122621` | Agree phase (agreed status) |
| `#detail/opp-20260405-120000` | Detail view with phase stepper, opportunity, roster |
| `#workspace/opp-20260405-120000` | **Redirects** to `#orb/opp-20260405-120000` |

All routes render correctly. `#workspace/` redirect works as specified.

---

### Test 20: Workspace Deletion (PASS)

- **Cancel path:** Clicking delete → confirm dialog fires → clicking Cancel → workspace remains (8 cards)
- **Confirm path:** Clicking delete → confirm dialog fires → clicking OK → API call succeeds → workspace removed (7 cards)
- Dialog message: `Delete "Lets just build something to test quickly"? This cannot be undone.`
- Card count updates from "8 Investigations" to "7 Investigations"

**Screenshot:** `dashboard-after-delete.png`

---

## Bugs Found

### Bug #1 (Medium): Back link intercepted by nav bar

- **Location:** Agree phase, `← Dashboard` link
- **Behavior:** Clicking the back link fails — the ORBITAL logo in the nav bar intercepts pointer events
- **Root cause:** The nav bar's logo element overlaps the back link position
- **Workaround:** Users can click the ORBITAL logo instead (same navigation target)
- **Fix:** Adjust z-index or position of `.back-link` to sit below the nav, or add `pointer-events: none` to the nav overlay area

### Bug #2 (Critical): `/api/launch/processes` returns 404

- **Location:** Dashboard, every 3 seconds via polling
- **Behavior:** The new "Running Processes" feature polls `GET /api/launch/processes` every 3s. The running server returns 404 for this endpoint.
- **Root cause:** The server was started before the new `launch.py` routes were added. The frontend code references the endpoint but the running server doesn't have it.
- **Impact:** 69 console errors accumulated during the test session. No visible UI impact (the processes section gracefully hides when no data).
- **Fix:** Restart the server to pick up the new route code.

### Bug #3 (Low): No favicon

- **Location:** All pages
- **Behavior:** `GET /favicon.ico` returns 404
- **Impact:** Browser tab shows default icon
- **Fix:** Add a favicon to `server/static/`

---

## Console Errors

| Error | Count | Severity |
|-------|-------|----------|
| `404 /api/launch/processes` | 68 | Critical (see Bug #2) |
| `404 /favicon.ico` | 1 | Low |

No JavaScript runtime errors. No uncaught exceptions.

---

## Skipped Tests

Tests 1, 4-13, 15 were skipped because they require:
- **Test 1:** Clean database (empty state) — all workspaces would need deletion
- **Tests 4-10:** Live agent subprocess (Claude CLI) to generate responses, evidence gathering
- **Tests 11-13:** Live agent + phase transitions (agree → assemble → investigate)
- **Test 15:** Canvas-based graph interactions (hover/click on canvas nodes — not accessible via DOM)

These tests should be automated with API mocks per the mock strategy in `tests/e2e/test.md`.

---

## Screenshots Captured

| File | Description |
|------|-------------|
| `dashboard-with-workspace.png` | 8 workspace cards, 1440x900 |
| `agree-phase-empty.png` | New investigation, split layout |
| `investigate-phase.png` | Graph canvas + sidebar + 70 nodes |
| `resume-investigation-agreed.png` | Agreed workspace in agree phase |
| `mobile-agree-phase.png` | 375x812 mobile layout |
| `detail-view.png` | Detail view with stepper + roster |
| `dashboard-after-delete.png` | 7 cards after deletion |
