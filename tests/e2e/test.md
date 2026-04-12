# Orbital — End-to-End Test Specification

> For use with Playwright visual regression + functional testing.
> Server: `python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000`
> Base URL: `http://localhost:8000`

---

## Prerequisites

- Server running at `http://localhost:8000`
- No existing workspaces (clean state) OR known workspace IDs for mid-flow tests
- Viewport: `1440x900` (desktop default)
- Screenshots captured at each `📸` marker

---

## Test 1: Dashboard — Empty State

**Route:** `#` (root)

### Steps

1. Navigate to `http://localhost:8000`
2. Wait for `#main` to render

### Assertions

- Page title contains "Orbital"
- `.empty-state` is visible
- `.empty-icon` contains "◎" (`&#9678;`)
- `.empty-text` reads "No investigations yet"
- `.btn-primary` with text "Start your first investigation" is visible and clickable

### 📸 `dashboard-empty.png`

---

## Test 2: Dashboard — With Workspaces

**Precondition:** At least one workspace exists (create via API: `POST /api/workspaces`)

### Steps

1. Create workspace via API:
   ```json
   POST /api/workspaces
   {
     "type": "hypothesis",
     "title": "Test: tmart NPS declining in UAE",
     "description": "NPS dropped 12 points in Q1 for tmart users in UAE"
   }
   ```
2. Navigate to `http://localhost:8000`
3. Wait for `.workspace-grid` to appear

### Assertions

- `.section-wide .heading` contains "1 Investigation"
- `.btn-primary` with text "+ New Orb" is visible
- `.workspace-card` count equals 1
- First `.workspace-card` contains:
  - `.ws-type` text equals "hypothesis"
  - `.ws-title` text equals "Test: tmart NPS declining in UAE"
  - `.status-pill` with class `.status-drafting`
  - `.ws-delete-btn` is visible
- Clicking the `.workspace-card` navigates to `#orb/{opp_id}`

### 📸 `dashboard-with-workspace.png`

---

## Test 3: New Investigation — Agree Phase (Initial)

**Route:** `#orb/new`

### Steps

1. Click "+ New Orb" button OR navigate to `#orb/new`
2. Wait for `.investigation-split` to appear

### Assertions — Layout

- `.investigation-split` has `data-phase="agree"`
- `.investigation-left` (`#inv-left`) is visible
- `.investigation-right` (`#inv-right`) is visible
- Grid layout: left panel takes remaining space, right panel is `460px` wide

### Assertions — Left Panel (Chat)

- `.back-link` with text "← Dashboard" is visible
- `.setup-chat-feed` (`#setup-feed`) is visible
- `.setup-chat-empty` is visible with:
  - `.setup-chat-empty-title` = "New Investigation"
  - `.setup-chat-empty-hint` contains "Describe what you want to investigate"
- `.chat-input-bar` (`#setup-input-bar`) is visible
- `textarea#setup-input` with placeholder "Tell me what to investigate..." is visible and focusable
- `.chat-send-btn` is visible

### Assertions — Right Panel (Agree Cards)

- 4 `.setup-card` elements visible (Progress, Opportunity, Context, Connectors)
- Progress card: `.setup-phase.active` text = "Refining"
- Opportunity card body: `.muted-hint` = "Describe your investigation to begin..."
- Context card body: `.muted-hint` = "Agent will load relevant context..."
- Connectors card body: either loading or showing connector toggles
- **No** Roster card present

### 📸 `agree-phase-empty.png`

---

## Test 4: Agree Phase — Send First Message

### Steps

1. From Test 3 state
2. Type into `#setup-input`: "NPS is declining for tmart users in UAE. We dropped 12 points in Q1. I think it's related to delivery times but not sure."
3. Press Enter (or click `.chat-send-btn`)
4. Wait for `.ai-chat-msg.ai-user` to appear
5. Wait for `.ai-thinking` to appear (briefly)
6. Wait for agent response: `.ai-chat-msg` without `.ai-user` class (timeout: 120s)

### Assertions — Chat Feed

- `.setup-chat-empty` is removed from DOM
- User message visible: `.ai-chat-msg.ai-user` with label "you"
- At least one agent response message: `.ai-chat-msg` with `.ai-chat-label` (color differs from user)
- `.ai-chat-text` contains rendered markdown (agent's response)

### Assertions — Right Panel Updates

- Opportunity card now shows title (not the placeholder hint)
- Progress card still shows "Refining" as active phase
- Context card may show loaded context layers

### Assertions — Activity Indicator

- `#setup-activity` shows activity status while agent runs
- After agent completes: activity indicator shows duration and cost

### 📸 `agree-phase-first-message.png`

---

## Test 5: Evidence Gathering — Chip Appears

**Precondition:** Agent response in Test 4 mentions evidence-related keywords (data, NPS, signal, research, feedback, etc.)

### Steps

1. Continue from Test 4
2. If agent asks about evidence/data, wait for `.evidence-chips` to appear in `#setup-feed`

### Assertions

- `.evidence-chips` container visible in chat feed
- Contains at least one `.evidence-chip` button
- `.evidence-chip` text = "Gather Evidence"
- `.evidence-chip` has `::before` pseudo-element with search icon

### Fallback

If the agent response doesn't contain trigger keywords, send a follow-up message:
"Do you have any data or customer research to support this?"
Then wait for the agent response containing evidence keywords.

### 📸 `evidence-chip-visible.png`

---

## Test 6: Evidence Gathering — Modal

### Steps

1. Click `.evidence-chip` button
2. Wait for `.evidence-modal-overlay` to appear

### Assertions — Modal Structure

- `.evidence-modal-overlay` covers full viewport (backdrop blur)
- `.evidence-modal` is centered, max-width `460px`
- `.evidence-modal-header h3` text = "Gather Evidence"
- `.evidence-modal-header p` contains "Launch a focused agent"

### Assertions — Source Grid

- `.evidence-source-grid` contains 6 `.evidence-source-option` buttons in a 2x3 grid
- Each option has `.source-label` and `.source-desc`:
  | source-label | source-desc |
  |---|---|
  | 📊 Data Query | SQL / BigQuery / analytics |
  | 📄 Doc Search | Internal documents & wikis |
  | ⭐ App Reviews | App store ratings & feedback |
  | 💬 Slack Signal | Slack threads & discussions |
  | 🌐 Market Intel | Competitor & market research |
  | 📈 Metrics Pull | Dashboards & KPIs |
- No option is `.selected` initially

### Assertions — Query Input

- `#evidence-query-input` is visible with placeholder "What are you looking for?"
- Input is auto-focused

### Assertions — Footer

- `.evidence-btn-cancel` with text "Cancel" is enabled
- `.evidence-btn-gather` with text "Gather" is **disabled** (no source selected, no query)

### Interactions

1. Click "📊 Data Query" option → it gets `.selected` class, others don't
2. Type "NPS scores for tmart users in UAE" into `#evidence-query-input`
3. `.evidence-btn-gather` is now **enabled**
4. Click a different source option → selection switches (only one `.selected` at a time)

### 📸 `evidence-modal-open.png`
### 📸 `evidence-modal-filled.png` (after selecting source + typing query)

---

## Test 7: Evidence Gathering — Launch & Card

### Steps

1. From Test 6 with source selected + query filled
2. Click `.evidence-btn-gather`
3. Wait for modal to close (`.evidence-modal-overlay` removed)
4. Wait for `.evidence-card` to appear in `#setup-feed`

### Assertions — API Call

- Network request: `POST /api/evidence/{opp_id}/gather` with body:
  ```json
  { "source_type": "data-query", "query": "NPS scores for tmart users in UAE" }
  ```
- Response: `{ "status": "launched", "opp_id": "...", "source_type": "data-query" }`

### Assertions — Evidence Card

- `.evidence-card` visible in chat feed
- `#evidence-card-data-query` exists
- `.evidence-card-header` contains:
  - `.evidence-card-icon` = "📊"
  - `.evidence-card-title` = "Data Query"
  - `.evidence-card-status.gathering` = "Gathering..." (pulsing animation)
- `.evidence-card-query` text = "NPS scores for tmart users in UAE"
- `.evidence-card-output` exists (may be empty initially)

### Assertions — Polling

- Periodic network requests to `GET /api/evidence/{opp_id}/status` every 3 seconds
- `.evidence-card-output` updates with streaming text as evidence agent works

### 📸 `evidence-card-gathering.png`

---

## Test 8: Evidence Gathering — Completion

**Note:** This test requires the evidence subprocess to complete. In CI, mock the evidence API responses.

### Steps

1. Wait for evidence polling to detect `{ "running": false }` (timeout: 300s, or mock)
2. Wait for `.evidence-card-status` to update

### Assertions

- `.evidence-card-status` changes from `.gathering` to `.completed`
- `.evidence-card-status.completed` text = "Done"
- Pulsing animation stops
- `.evidence-card-output` or `.evidence-card-findings` shows evidence summary

### 📸 `evidence-card-completed.png`

---

## Test 9: Evidence Gathering — Multiple Sources (Parallel)

### Steps

1. Click another `.evidence-chip` (or call `openEvidenceModal()` again)
2. Select "💬 Slack Signal" source
3. Enter query "fresh food quality complaints tmart"
4. Click Gather
5. Verify second evidence card appears

### Assertions

- `#evidence-card-slack-signal` appears alongside `#evidence-card-data-query`
- Both cards can show independent statuses
- Polling handles multiple source types

### 📸 `evidence-multiple-cards.png`

---

## Test 10: Evidence Modal — Cancel

### Steps

1. Open evidence modal (click `.evidence-chip`)
2. Click `.evidence-btn-cancel`

### Assertions

- `.evidence-modal-overlay` is removed from DOM
- No API call made
- No evidence card added

### Alternative: Click overlay backdrop

1. Open evidence modal
2. Click on `.evidence-modal-overlay` (outside `.evidence-modal`)
3. Modal closes

---

## Test 11: Agree → Assemble Phase Transition

**Precondition:** Agent recommends `/assemble` in its response

### Steps

1. Continue conversation until agent output contains `/assemble`
2. Wait for `.cmd-action-btn[data-cmd="/assemble"]` to appear
3. Click the "/assemble" action button
4. Wait for agent to process `/assemble` command
5. Wait for phase transition (WebSocket/poll detects `opp.roster` populated)

### Assertions — Action Button

- `.cmd-action-btn` text = "→ Move to /assemble"
- Clicking sends `/assemble` as chat message

### Assertions — Phase Transition Animation

- `.investigation-right` gets `.phase-exit` class (250ms exit animation)
- After exit: `data-phase` attribute changes to `"assemble"`
- `.investigation-right` gets `.phase-enter` class (250ms enter animation)
- `.investigation-left` stays (chat persists — no animation for agree→assemble)

### Assertions — Right Panel (Assemble Cards)

- Progress card: "Refined" phase shows `.complete`, "Assembling" shows `.active`
- Condensed Opportunity card with title and description
- `.agent-card-grid` with agent cards (typically 3-5 agents)
- Each `.agent-card` has:
  - `.agent-card__accent` colored bar (top)
  - `.agent-card__icon` with SVG icon
  - `.agent-card__title` (e.g., "Product", "Data", "Design", "Engineering")
  - `.agent-card__track-count` (e.g., "3 tracks")
  - `.agent-toggle.on` (included by default)
- `.roster-summary` showing agent count and total tracks

### 📸 `assemble-phase.png`

---

## Test 12: Assemble Phase — Agent Card Interactions

### Steps

1. From Test 11 state
2. Click an `.agent-card` (not on the toggle)
3. Slide-over opens with agent details

### Assertions — Agent Detail Slide-Over

- Slide-over (`.drawer-overlay` / `.drawer`) opens
- Shows agent icon, name, and track count
- Lists investigation tracks with:
  - `.agent-card__track-name` for each track
  - `.agent-card__track-question` (if structured tracks)
  - `.agent-card__artifact-tag` tags (expected artifacts)
- Agent toggle in slide-over matches card toggle state

### Agent Toggle

1. Click `.agent-toggle` on a card
2. Toggle switches to off (`.agent-toggle` loses `.on` class)
3. Card gets `.excluded` class (visual dimming)
4. `.roster-summary` updates (count decreases)
5. Click toggle again → agent re-included

### 📸 `assemble-agent-detail.png`
### 📸 `assemble-agent-excluded.png`

---

## Test 13: Assemble Phase — Plan Mode & Launch

### Steps

1. Wait for agent to enter plan mode (`.setup-approve-btn` appears)
2. Optionally: `.plan-preview` div shows plan content
3. Click "Launch Investigation" button

### Assertions — Plan Approval

- `.setup-approve-btn` text = "Launch Investigation"
- Clicking changes text to "Launching..." and `disabled = true`
- API call: `POST /api/launch/{opp_id}/approve`
- On success: text changes to "Launched", border turns green

### Assertions — Status Transition

- Opportunity `status` changes to `"orbiting"`
- Phase transition triggers: assemble → investigate

### 📸 `assemble-plan-approve.png`

---

## Test 14: Investigate Phase — Graph + Sidebar

### Steps

1. Wait for phase transition to "investigate"
2. Wait for `#orbital-canvas` to appear
3. Wait for sidebar content to load

### Assertions — Layout

- `.investigation-split[data-phase="investigate"]`
- Left panel: graph canvas
- Right panel: investigation sidebar

### Assertions — Left Panel (Graph)

- `#orbital-canvas` is a `<canvas>` element filling the left panel
- `.graph-stats` (`#graph-stats`) shows node/edge counts
- `.agent-legend` (`#agent-legend`) shows colored agent labels
- `.graph-controls` with 3 buttons: zoom-in (`+`), recenter (`⌂`), zoom-out (`−`)

### Assertions — Right Panel (Sidebar)

- `#sidebar-header` shows:
  - `.status-pill` with status (e.g., "orbiting" or "assembled")
  - Opportunity ID in monospace
  - `.edit-opp-btn` edit button
  - Opportunity title as `.subheading`
- `#sidebar-content` shows tab interface:
  - Tab buttons for "Overview", "Evidence", "Agents"
  - Active tab content rendered

### 📸 `investigate-phase.png`

---

## Test 15: Investigate Phase — Graph Interactions

### Steps

1. From Test 14 state
2. Hover over a graph node
3. Click a graph node

### Assertions — Hover

- Node highlights (glow effect visible on canvas)
- Tooltip or label appears near node

### Assertions — Click

- Node drawer opens (`.drawer-overlay` + `.drawer`)
- Drawer shows node details (type, content, agent, confidence, source)
- Close drawer via close button or clicking overlay

### Graph Controls

1. Click zoom-in (`#zoom-in-btn`) → canvas zoom increases
2. Click zoom-out (`#zoom-out-btn`) → canvas zoom decreases
3. Click recenter (`#recenter-btn`) → graph recenters

### 📸 `investigate-node-hover.png`
### 📸 `investigate-node-drawer.png`

---

## Test 16: Dashboard — Resume Existing Investigation

### Steps

1. Navigate to `#` (dashboard)
2. Click on an existing workspace card
3. Wait for `#orb/{opp_id}` to load

### Assertions

- Phase detected correctly from workspace state:
  - `status !== 'investigating'` + no roster → `agree`
  - `status !== 'investigating'` + roster present → `assemble`
  - `status === 'investigating'` → `investigate`
- Correct panels rendered for detected phase
- Chat history is **not** preserved (fresh render) — but workspace data is

### 📸 `resume-investigation.png`

---

## Test 17: Responsive Layout (Mobile)

**Viewport:** `375x812` (iPhone)

### Steps

1. Resize viewport to `375x812`
2. Navigate to `#orb/new`

### Assertions

- `.investigation-split` switches to single column (`grid-template-columns: 1fr`)
- `.investigation-right` gets `border-top` instead of `border-left`
- `.investigation-right` max-height is `50vh`
- Chat and cards stack vertically
- All interactive elements remain accessible

### 📸 `mobile-agree-phase.png`

---

## Test 18: Navigation — Back to Dashboard

### Steps

1. From any investigation phase
2. Click `.back-link` ("← Dashboard")

### Assertions

- Navigation goes to `#` (dashboard)
- Graph cleanup: `state.graph` nulled, `cancelAnimationFrame` called
- WebSocket cleanup: `state.ws` and `state._setupWs` closed
- Polling cleanup: `state._setupPoll` and `state._agentPoll` cleared
- Evidence polling cleanup: `state._evidencePolling` cleared

---

## Test 19: Hash Routing

### Steps

1. Navigate directly to `http://localhost:8000/#orb/new` → New orb
2. Navigate directly to `http://localhost:8000/#orb/{opp_id}` → Loads at correct phase
3. Navigate directly to `http://localhost:8000/#detail/{opp_id}` → Detail view
4. Navigate directly to `http://localhost:8000/#` → Dashboard
5. Navigate to `http://localhost:8000/#workspace/{opp_id}` → Redirects to `#orb/{opp_id}`

### Assertions

- Each route renders the correct view
- Browser back/forward buttons work
- Hash updates when navigating via UI clicks

---

## Test 20: Workspace Deletion

### Steps

1. From dashboard with at least one workspace
2. Click `.ws-delete-btn` on a workspace card
3. Browser `confirm()` dialog appears

### Assertions — Cancel

- Click Cancel → nothing happens, workspace remains

### Assertions — Confirm

- Click OK → API call: `DELETE /api/workspaces/{opp_id}`
- Workspace card removed from grid
- If last workspace: empty state appears

### 📸 `dashboard-delete-confirm.png`

---

## API Mocking Strategy (for CI)

For tests that require agent subprocesses (Tests 4, 8, 11, 13, 14), mock these endpoints:

| Endpoint | Mock Behavior |
|----------|------|
| `POST /api/launch/{id}/start` | Return `200 {}` |
| `POST /api/launch/{id}/send` | Return `200 {}` |
| `GET /api/launch/{id}/status` | Return stream-json lines simulating agent output, then `done: true` |
| `POST /api/launch/{id}/approve` | Return `200 {}`, update opportunity status |
| `POST /api/evidence/{id}/gather` | Return `200 { "status": "launched" }` |
| `GET /api/evidence/{id}/status` | Return progressive output, then `{ "running": false }` |
| `GET /api/workspaces/{id}` | Return workspace with updated state per phase |

### Mock Data Files

Place mock responses in `tests/e2e/fixtures/`:

```
fixtures/
├── workspace-drafting.json      # Agree phase workspace
├── workspace-with-roster.json   # Assemble phase workspace
├── workspace-investigating.json # Investigate phase workspace
├── agent-output-agree.jsonl     # Stream-json lines for agree agent
├── agent-output-assemble.jsonl  # Stream-json lines for assemble agent
├── evidence-status-running.json # Evidence polling (in-progress)
├── evidence-status-done.json    # Evidence polling (completed)
└── evidence-completed.json      # Full evidence file
```

---

## Visual Regression Baselines

All `📸` screenshots should be stored in `tests/e2e/screenshots/` and compared against baselines on each run. Tolerance: `0.1%` pixel diff for anti-aliasing variance.

| Screenshot | Description |
|---|---|
| `dashboard-empty.png` | Empty state with CTA |
| `dashboard-with-workspace.png` | Card grid with workspace |
| `agree-phase-empty.png` | Split layout, chat + agree cards |
| `agree-phase-first-message.png` | User message + agent response |
| `evidence-chip-visible.png` | Gather Evidence button in chat |
| `evidence-modal-open.png` | Modal with 6 source options |
| `evidence-modal-filled.png` | Source selected + query entered |
| `evidence-card-gathering.png` | Inline card with pulsing status |
| `evidence-card-completed.png` | Card with findings |
| `evidence-multiple-cards.png` | Multiple evidence cards |
| `assemble-phase.png` | Agent cards grid + progress |
| `assemble-agent-detail.png` | Slide-over with tracks |
| `assemble-agent-excluded.png` | Dimmed excluded agent |
| `assemble-plan-approve.png` | Plan preview + launch button |
| `investigate-phase.png` | Graph canvas + sidebar |
| `investigate-node-hover.png` | Highlighted node |
| `investigate-node-drawer.png` | Node detail drawer |
| `resume-investigation.png` | Correct phase on resume |
| `mobile-agree-phase.png` | Mobile responsive layout |
| `dashboard-delete-confirm.png` | Delete confirmation |
