# Orbital Design System

> Reference for `server/static/design-system.css`

---

## Design Tokens

All tokens live in `:root`. Use `var(--token-name)` everywhere — never hardcode values.

### Colors

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0a0c12` | Page background |
| `--surface` | `rgba(22,25,35,0.88)` | Glass panels, cards |
| `--surface-solid` | `#161923` | Opaque surface (toast, etc.) |
| `--border` | `rgba(255,255,255,0.06)` | Default borders |
| `--border-hover` | `rgba(255,255,255,0.12)` | Hover state borders |
| `--text-primary` | `#e2e8f0` | Headings, emphasis |
| `--text-secondary` | `#6b7a90` | Body text |
| `--text-muted` | `#4a5568` | Labels, hints |
| `--color-accent` | alias for `--color-product` | Primary accent (green) |
| `--color-accent-dim` | `rgba(16,185,129,0.15)` | Accent backgrounds |
| `--color-counter` | `#EF4444` | Contradictions, delete, kill signals |
| `--color-brief` | `#F59E0B` | Warnings, gaps, amber signals |
| `--color-neutral` | `#64748B` | Neutral badges |
| `--color-neutral-light` | `#94a3b8` | Light neutral |

**Agent colors** (used for roster dots, legends, borders):

| Token | Value | Agent |
|-------|-------|-------|
| `--color-product` | `#10B981` | Product |
| `--color-design` | `#8B5CF6` | Design |
| `--color-data` | `#3B82F6` | Data |
| `--color-engineering` | `#F97316` | Engineering |

### Typography

| Token | Value | Use |
|-------|-------|-----|
| `--text-2xs` | `9px` | Micro labels, badges |
| `--text-xs` | `10px` | Status pills, section titles |
| `--text-sm` | `11px` | Secondary text, form labels |
| `--text-base` | `12px` | Default body text |
| `--text-md` | `13px` | Buttons, form inputs |
| `--text-lg` | `14px` | Subheadings, card titles |
| `--text-xl` | `16px` | Nav icons, close buttons |
| `--text-2xl` | `18px` | Page headings |
| `--font-sans` | Inter stack | Body text |
| `--font-mono` | JetBrains Mono stack | Code, labels, IDs |

### Spacing

| Token | Value |
|-------|-------|
| `--space-1` through `--space-12` | 2, 4, 6, 8, 10, 12, 14, 16, 20, 24, 32, 48 px |

### Border Radius

| Token | Value | Use |
|-------|-------|-----|
| `--radius-xs` | `6px` | Small elements (delete btn, connectors) |
| `--radius-sm` | `8px` | Inputs, badges, tooltips |
| `--radius` | `12px` | Cards, panels |
| `--radius-tag` | `14px` | Tags, select dropdowns |
| `--radius-lg` | `16px` | Glass panels |
| `--radius-pill` | `20px` | Status pills, graph stats |

---

## Base Components

### Cards

| Class | Use |
|-------|-----|
| `.glass` | Frosted glass panel (surface + blur + shadow) |
| `.card` | Standard card (border, padding 14px, hover effect) |
| `.card--section` | Section card within a form/panel (padding 14px 16px, margin-bottom 10px) |
| `.card-clickable` | Add `cursor: pointer` to a card |

Aliases: `.edit-card` and `.setup-card` both map to `.card--section`.

### Labels

| Class | Use |
|-------|-----|
| `.label` | Small uppercase mono label (9px, 0.14em spacing) |
| `.section-label` | Section header in cards (10px, 0.08em spacing, muted) |
| `.section-label--accent` | Green-colored section label |

Aliases: `.edit-card-title` = `.section-label--accent`, `.setup-card-title` = `.section-label`.

### Chips

| Class | Use |
|-------|-----|
| `.chip` | Base chip (inline-flex, gap 5px, mono) |
| `.chip--status` | Status pill variant (pill radius, uppercase, bold) |
| `.chip--tag` | Tag variant (tag radius, border, background) |
| `.chip--source` | Small source badge (2px 8px padding) |
| `.chip--roster` | Roster member chip |

Aliases: `.status-pill` = `.chip--status`, `.edit-tag` = `.chip--tag`, `.source-field-chip` = `.chip--source`, `.setup-roster-chip` = `.chip--roster`.

### Buttons

| Class | Use |
|-------|-----|
| `.btn-primary` | Primary gradient button (green-to-blue) |
| `.btn-secondary` | Ghost button with border |
| `.btn--sm` | Small button modifier (3px 10px) |
| `.btn--block` | Full-width modifier |
| `.btn-icon` | 24x24 icon button with border |

Aliases: `.edit-add-btn` = `.btn-secondary.btn--sm`, `.edit-opp-btn` = `.btn-icon`.

### Inputs

| Class | Use |
|-------|-----|
| `.form-input` | Standard bordered input |
| `.form-textarea` | Standard bordered textarea |
| `.form-select` | Standard bordered select |
| `.input--inline` | Transparent borderless input (for edit panels) |
| `.textarea--inline` | Transparent borderless textarea |

Aliases: `.edit-input` = `.input--inline`, `.edit-textarea` = `.textarea--inline`.

---

## Utility Classes

### Layout
| Class | Property |
|-------|----------|
| `.flex` | `display: flex` |
| `.flex-col` | `flex-direction: column` |
| `.flex-wrap` | `flex-wrap: wrap` |
| `.flex-1` | `flex: 1; min-width: 0` |
| `.items-center` | `align-items: center` |
| `.justify-between` | `justify-content: space-between` |
| `.justify-end` | `justify-content: flex-end` |
| `.inline-block` | `display: inline-block` |
| `.d-none` | `display: none` |
| `.w-full` | `width: 100%` |
| `.truncate` | ellipsis overflow |
| `.nowrap` | `white-space: nowrap` |

### Spacing
| Class | Property |
|-------|----------|
| `.gap-{4,6,8,10,12,20}` | `gap: Npx` |
| `.mb-{4,6,8,10,12,14,16,24}` | `margin-bottom: Npx` |
| `.mt-{6,8,12,16}` | `margin-top: Npx` |
| `.ml-{4,8}`, `.ml-auto` | `margin-left` |
| `.pt-80` | `padding-top: 80px` |

### Typography
| Class | Property |
|-------|----------|
| `.text-2xs` | `font-size: var(--text-2xs)` |
| `.text-xs` | `font-size: var(--text-xs)` |
| `.text-sm` | `font-size: var(--text-sm)` |
| `.text-base` | `font-size: var(--text-base)` |
| `.text-md` | `font-size: var(--text-md)` |
| `.text-lg` | `font-size: var(--text-lg)` |
| `.font-mono` | `font-family: var(--font-mono)` |
| `.font-semibold` | `font-weight: 600` |
| `.font-weight-500` | `font-weight: 500` |
| `.uppercase` | `text-transform: uppercase` |
| `.lh-14` | `line-height: 1.4` |
| `.lh-16` | `line-height: 1.6` |
| `.word-break` | `word-break: break-word` |

### Color
| Class | Property |
|-------|----------|
| `.text-muted` | `color: var(--text-muted)` |
| `.text-secondary` | `color: var(--text-secondary)` |
| `.text-primary` | `color: var(--text-primary)` |
| `.text-accent` | `color: var(--color-accent)` |
| `.text-counter` | `color: var(--color-counter)` |
| `.text-brief` | `color: var(--color-brief)` |
| `.text-design` | `color: var(--color-design)` |
| `.bg-accent` | `background: var(--color-accent)` |
| `.bg-counter` | `background: var(--color-counter)` |
| `.bg-brief` | `background: var(--color-brief)` |
| `.bg-data` | `background: var(--color-data)` |
| `.bg-design` | `background: var(--color-design)` |

### Dots / Shapes
| Class | Size |
|-------|------|
| `.status-dot` | 6x6 circle |
| `.drawer-dot` | 7x7 circle |
| `.dot-lg` | 10x10 |
| `.dot-xl` | 12x12 |

---

## Sidebar Components

| Class | Use |
|-------|-----|
| `.sidebar-section` | Section wrapper (margin-bottom 14px) |
| `.sidebar-section-title` | Collapsible section header (9px, uppercase, clickable) |
| `.sidebar-tab` / `.sidebar-tabs` | Tab switcher |
| `.contrib-item` | Contribution list item (dot + name + badge) |
| `.finding-card` | Finding card with colored left border |

### Drawer Components
| Class | Use |
|-------|-----|
| `.drawer-row` | Flex row with gap 10px |
| `.drawer-dot` | 7px colored dot |
| `.drawer-badge` | Small mono badge |
| `.drawer-meta` | Secondary text block |
| `.confidence-bar` / `.confidence-fill` | Progress bar |

### Live Status & WebSocket Dropdown

| Class | Use |
|-------|-----|
| `.live-badge` | Connection status pill (green tint, pill radius, mono) |
| `.live-badge--clickable` | Adds cursor pointer + hover effect to badge |
| `.live-pulse` | 6px animated green dot (pulse keyframe) |
| `.ws-dropdown` | Wrapper for badge + dropdown menu (position: relative) |
| `.ws-chevron` | Small dropdown arrow (8px, muted) |
| `.ws-dropdown-menu` | Absolute-positioned menu (surface-solid, border, shadow) |
| `.ws-dropdown-item` | Menu row (flex, gap 8px, mono, hover highlight) |
| `.ws-dropdown-item--danger` | Red variant for destructive actions (disconnect) |

### Chat & Loading

| Class | Use |
|-------|-----|
| `.ai-thinking` | Thinking indicator wrapper (fade-in, muted) |
| `.ai-thinking .ai-chat-label` | "thinking" label (mono, accent, uppercase) |
| `.ai-thinking-dots` | Animated dot container |
| `.ai-thinking-dots span` | Individual dot with staggered `dotPulse` animation |

Keyframes: `dotPulse` (opacity 0.3 → 1 → 0.3, 1.4s), `aiFadeIn` (opacity 0 → 1, 0.3s).

### Workspace Cards

| Class | Use |
|-------|-----|
| `.workspace-card` | Card in the workspace list (hover reveals delete) |
| `.ws-delete-btn` | Hidden delete button, appears on card hover |

### Opportunity Signal Lists

| Class | Use |
|-------|-----|
| `.opp-signals` | Signal section wrapper (margin-top 8px) |
| `.opp-signals-title` | Section header (mono, 9px, uppercase, muted, letter-spacing 0.08em) |
| `.opp-signal-item` | Signal row (flex, gap 6px, 11px secondary text, line-height 1.5) |
| `.opp-signal-dot` | 5px colored circle indicator (flex-shrink 0, margin-top 5px) |

Used in setup preview Opportunity card and detail page for assumptions, success signals, and kill signals. Dot color is set via inline `style="background:var(--token)"`:
- Assumptions: `--color-neutral-light`
- Success signals: `--color-accent`
- Kill signals: `--color-counter`

### Command Action Buttons

| Class | Use |
|-------|-----|
| `.cmd-action-btn` | Inline action button in chat feed (mono, 11px, accent text, accent-dim bg, sm radius) |

Appears when agent output mentions a slash command (e.g., `/assemble`). Clicking auto-sends the command. Deduplicated via `data-cmd` attribute.

### Detail Page Phase Bar

| Class | Use |
|-------|-----|
| `.detail-phases` | Phase bar container (flex, center, gap 0, margin-bottom 20px) |
| `.detail-phase` | Individual phase step (flex column, center, gap 4px, 10px mono muted) |
| `.detail-phase.active` | Active phase (accent text + accent dot) |
| `.detail-phase.complete` | Completed phase (accent text + accent dot, reduced opacity) |
| `.detail-phase-dot` | 8px circle indicator (border default, filled when active/complete) |
| `.detail-phase-line` | Connector line between phases (40px wide, 1px border-top) |

Maps `opp.status` to phases: aligning → Agree, assembled → Assemble, orbiting/converging → Investigate, landed → Decide.

### Quality Gates

Components for the 3-layer quality evaluation system. Used in the Quality tab, sidebar header, contribution badges, and evidence cards.

#### Gate Cards

| Class | Use |
|-------|-----|
| `.quality-gate` | Gate result card (12px padding, 3px left border, 6px radius, surface bg, 8px bottom margin) |
| `.quality-gate--pass` | Pass state — green left border (`--color-accent`) |
| `.quality-gate--fail` | Fail state — red left border (`--color-counter`) |
| `.quality-gate--warn` | Warning state — amber left border (`--color-brief`) |
| `.quality-gate__name` | Gate name label (13px, medium weight, primary text) |
| `.quality-gate__value` | Gate score value (13px mono, tabular-nums, secondary text) |

#### Gate Pills

| Class | Use |
|-------|-----|
| `.gate-pill` | Compact pass/fail badge (11px, 2px/8px padding, 10px radius, medium weight) |
| `.gate-pill--pass` | Pass pill — green tint bg (`--color-accent-dim`), green text (`--color-accent`) |
| `.gate-pill--fail` | Fail pill — red tint bg, red text (`--color-counter`) |
| `.gate-pill--warn` | Warning pill — amber tint bg, amber text (`--color-brief`) |

Used inline on contribution items, evidence cards (e.g., "Stale (183d)"), and the quality strip.

#### Quality Strip

| Class | Use |
|-------|-----|
| `.quality-strip` | Compact summary bar in sidebar header (flex, 6px gap, center alignment, 8px vertical margin) |

Contains `.gate-pill` elements showing pass/fail counts. Clicking navigates to the Quality tab.

#### Quality Score

| Class | Use |
|-------|-----|
| `.quality-score` | Large overall score display (32px, bold, tabular-nums) |
| `.quality-score--pass` | Green text — score > 0.7 |
| `.quality-score--fail` | Red text — score < 0.5 |
| `.quality-score--warn` | Amber text — score 0.5–0.7 |

#### Rubric Results (Layer 2)

| Class | Use |
|-------|-----|
| `.quality-rubric-list` | Container for rubric results (flex column, 4px gap) |
| `.quality-rubric` | Single rubric row (flex, space-between, 10px padding, 4px radius, surface bg) |
| `.quality-rubric__name` | Rubric name (12px, secondary text) |
| `.quality-rubric__score` | Rubric score or pass/fail (12px mono, tabular-nums) |

---

## When Adding New Components

1. Check if an existing class or utility covers it
2. Use tokens for ALL colors, font sizes, radii — never hardcode
3. Follow BEM-lite naming: `.component`, `.component--modifier`, `.component__element`
4. If a pattern appears 3+ times, extract to a class
5. Dynamic values (runtime colors, computed widths) stay as inline `style=`
6. Static values belong in CSS classes
