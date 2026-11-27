---
phase: 24
slug: compare-portfolio-performance
status: verified
shadcn_initialized: true
preset: radix-vega
created: 2026-11-26
---

# Phase 24 — UI design contract

Use the approved `portfolios.html` and `portfolio.html` from the v1.5 ZIP for
the two portfolio surfaces. D-01 and D-02 define the cards. D-04 defines the
selected workspace. D-03 supplies recorded daily values and D-05 defines
visual acceptance. [Phase decisions](24-CONTEXT.md) · [Research](24-RESEARCH.md) · [Approved prototype](../../ui-reviews/v1.5/README.md)

## Design system

| Property | Value |
|---|---|
| Tool | Existing checked-in shadcn components and Tailwind CSS utilities |
| Preset | `radix-vega` with neutral CSS variables from `frontend/components.json` |
| Component library | Radix and existing React portfolio components |
| Icon library | Existing Lucide icons with text labels for actions and decorative icons hidden from assistive technology |
| Font | Self-hosted Inter Variable with tabular figures for money, age and percentages |

Reuse the existing Birja shell, focus treatment, formatter and panel primitives.
Use `PortfolioRoute` and `PortfolioSwitcher` for the selected book, the
existing create, metadata and removal forms for mutations, and
`PortfolioAllocation` and `PortfolioHoldings` for detail rendering. Use the
existing responsive Canvas approach for the compact sparkline. The local UI
reference search supports a line with an equivalent readable summary and
unobscured keyboard focus. [Birja design system](../../../design-system/birja/MASTER.md) · [Component configuration](../../../frontend/components.json) · [Theme variables](../../../frontend/src/index.css)

## Spacing scale

| Size | Use |
|---|---|
| 4px | Name to optional description and tightly related inline values |
| 8px | Related controls, chips and allocation legend pairs |
| 16px | Phone gutter, card gaps and phone card padding |
| 24px | Mid-width gutter, desktop card padding and toolbar to summary |
| 32px | Wide summary padding and summary to Holdings |
| 48px | Wide space above the first content section and between value and allocation |

Use existing `--radius-card` and `--radius-control` and a single-pixel border.
Keep regular controls at least 44px tall with 8px separation and primary form
actions at least 48px tall. At 1440px use a centered 1360px content area with
40px side gutters. At 390px use the prototype's 358px content area with 16px
side gutters. Keep the navigation and content usable at 320px with the same
16px content gutter. Use a three-column overview and holdings grid at desktop
width above 1050px, two columns from 521px to 1050px, and one column at
520px and below. Use the prototype's roughly 244px desktop and 200px phone
minimum portfolio card heights. Allow wrapped content to grow without overlap
or clipping. [Approved prototype styles](../../ui-reviews/v1.5/README.md)

## Typography

| Role | Size | Weight | Line height |
|---|---|---|---|
| Supporting | 14px | 400 | 1.4 |
| Body and controls | 16px | 400 | 1.5 |
| Card name and section heading | 24px | 600 | 1.2 |
| Financial display | 32px | 600 | 1.15 |

Retain semantic page headings. On the overview and ready selected workspace
the heading is visually hidden because the navigation or selected portfolio
identifies the view. Show the selected portfolio name in the chooser and the
visible heading for an unavailable destination. Give complete totals and
holding values the strongest financial hierarchy. Wrap long names and currency
values at narrow widths.

## Color

| Role | Existing token | Use |
|---|---|---|
| Dominant surface, about 60% | `--background` | Warm page canvas and toolbar field backgrounds |
| Secondary, about 30% | `--card`, `--muted` | Cards, summary and empty bar tracks |
| Accent, at most about 10% | `--brand`, `--ring` | Focus treatment and subtle emphasis on the New portfolio card |
| Primary and supporting ink | `--foreground`, `--primary`, `--muted-foreground` | Values, actions and labels |
| Destructive and warning | `--destructive`, `--loss-text`, `--warn-text` | Confirmed removal, refusal and incomplete values |
| Financial outcomes and data | `--gain-text`, `--loss-text`, `--data-fill`, `--muted-foreground`, `--border` | Signed gain or loss, neutral sparkline, labelled allocation segments |

Use existing token fills and signed text to distinguish gains, losses and
unavailable values. Reserve the fox-red accent for the focus treatment and
creation-card emphasis. Give the sparkline a neutral 2px stroke. Label each
allocation segment with its asset class, percentage and supplied USD value.

## Layout and interaction

### Portfolios overview

- Put the portfolio name and its nonempty description first, reserve a 44px
  sparkline slot, and place the current total and signed return together above
  cash. Use the same current valuation messages and server-supplied amounts as
  the existing overview. Keep dated stock price context and rewrite no values
  from a chart observation. One link covers the full card surface and is named
  by its portfolio heading. The arrow is decorative.
- Put `New portfolio` last as a same-size button card. When there are zero
  portfolios it is the primary visible next action. When ten active portfolios
  are confirmed, keep the last card disabled and associate it with the visible
  capacity reason. Retain the existing original-request recovery actions and
  use the existing form when the user opens the creation card.
- Draw observations over the latest 30 UTC calendar days for the exact active
  portfolio ID. Position by UTC day and break the line at absent or null days.
  Draw a segment only between two available adjacent daily observations. When
  enough complete points exist, isolated recorded points may use a marker.
  With zero or one complete observation keep the current total and return and
  show the collecting state in the chart slot. Match the slot height for
  loading and unavailable history to prevent a card jump. Keep the separate
  current valuation response authoritative throughout.
- Make the neutral Canvas decorative and associate a text summary with the
  card link via `aria-describedby`. Give the first and last available UTC
  dates and recorded USD values, plus an incomplete history phrase when a day
  between observations is absent or incomplete. A single value can be described
  with its UTC date. Use ordinary text for the chart availability state. Avoid
  a focus stop, hover dependency, chart controls or a second interactive element
  inside the card. A delayed reply for a previous session or a closed portfolio
  must never appear on the active card.

### Selected portfolio

- Keep one labelled chooser, `Edit`, `Update` with age and `Remove` in one
  toolbar group in that order. Align them in one row when they fit. On phones
  place the chooser first, then wrap actions in the same tab order. The chosen
  ID governs the detail, current figures, refresh and actions. Use the current
  refresh age and permitted price state, with an exact timestamp available.
  Announce refresh success or failure once per operation. Maintain the
  existing confirmation, disabled and interrupted-mutation states.
- Follow the toolbar with one panel. Put visible `Total value` and the largest
  figure with its signed all-time dollar and percentage return on the left.
  Use cash, stock and crypto allocations in that order on the right, with a
  labelled distribution strip and class values beneath. At phone width stack
  the value group above allocation. Use `class_values` and
  `class_allocation_percent` directly. When valuation is incomplete, show
  qualified known value and cash, count unvalued holdings and explain the
  unavailable return and allocation. At zero total, keep its actual value
  visible and explain unavailable allocation percentages.
- Place `Holdings` before `Filter holdings` and `Sort holdings`, then holding
  cards. Use filters `All assets`, `Stocks` and `Crypto`; sort by `Highest
  value` by default, with `Ticker A–Z` and `Highest return`. Compare exact
  supplied market values and percentage returns, put unavailable amounts
  last, and use stable ticker and exact ID ties. Place ticker and asset
  identity, position value, signed return and quantity on each card. Preserve
  `Cost and price` detail, dated or unavailable price context and the scoped
  `Trade` or `View details` action. Keep a distinct trade link on a card that
  includes a disclosure so both controls remain reachable.
- Preserve focus to the originating New portfolio, Edit or Remove control on
  cancellation. Give successful navigation a clear heading target. For an
  invalidated destination or a completed removal, take focus to the stable
  fallback heading or overview. Each form keeps its visible field labels,
  associated errors and current signed-in/ownership checks. Keep keyboard focus
  rings visible outside row and chart clipping.

## Copywriting contract

| Element | Copy and behavior |
|---|---|
| Overview action | `New portfolio` opens the existing form. `Create portfolio` confirms after validation. |
| Overview empty or at limit | Give the zero state an accessible `No portfolios yet` heading and a visible `New portfolio` card. At limit show `You have 10 active portfolios. You can’t create another right now.` |
| Overview or selected startup | `Loading portfolios…` or `Loading your portfolio`. Reserve the existing loading surface. |
| Overview or selected load failure | `Can’t load your portfolios right now.` or `Can’t load your portfolio right now.` with `Try again`. Use `Retry refresh` when permitted prior figures remain visible. |
| Trend loading or collecting | `Loading value history…` while pending. `Collecting daily values` for zero or one complete value. |
| Trend partial or failed | `Some days have no recorded value` in the summary when applicable. On failed history show `Value history unavailable` and one `Retry value history` control for the overview outside the card links. Keep the current figures and card links usable while retrying. |
| Trend text equivalent | `Daily value over 30 days. From {UTC date}, {USD value}, to {UTC date}, {USD value}.` Use the UTC dates of the actual observations. |
| Selected toolbar | `Edit`, `Update` with the current age such as `12s ago`, and `Remove`. Provide `Edit portfolio`, `Update portfolio` and `Remove portfolio` accessible names. |
| Current value incomplete | `Known value: {amount} — incomplete` followed by the unvalued count and a reason. If none can be provided, state `Value unavailable` and offer refresh where available. |
| Empty or filtered holdings | `No holdings yet` with `Explore Markets`; `No holdings match this filter.` when a filter returns no results. |
| Removal confirmation | `Delete “{name}”?` with `Keep portfolio` and `Delete portfolio`. Keep the existing irreversible closure and original-request recovery copy. |

## Integrated visuals and accessibility

Capture the authorized app overview and selected workspace at 1440px and
390px beside the two approved ZIP pages using the same viewport. Check card
grid and inset, names and cash/value placement, compact trend slot, creation
card, toolbar order, two-column value and allocation, stacked mobile summary,
and holding card and filter placement. Use realistic seeded daily values for
the paired view and a separate sparse fixture for chart gaps. The neutral
stroke, current age and error copy, exact figures, separate Trade and
disclosure controls, and existing management surfaces reflect live app
behavior. Exercise keyboard activation, order, focus after closure, long
names, narrow mobile and enlarged-text reflow without horizontal page scroll.
Use current source-authorized fixture data and keep demo controls and simulated
browser state outside the app implementation. [Approved prototype](../../ui-reviews/v1.5/README.md) · [Phase decisions](24-CONTEXT.md)

## Registry safety

| Registry | Blocks used | Safety gate |
|---|---|---|
| shadcn official | Existing checked-in Button, Card and other portfolio primitives | Local reuse. No registry import needed. |
| Third-party | None | Not applicable |

## Checker sign-off

- [x] Dimension 1 Copywriting
- [x] Dimension 2 Visuals
- [x] Dimension 3 Color
- [x] Dimension 4 Typography
- [x] Dimension 5 Spacing
- [x] Dimension 6 Registry Safety

The independent UI contract check passed all six dimensions on 2026-11-26.
