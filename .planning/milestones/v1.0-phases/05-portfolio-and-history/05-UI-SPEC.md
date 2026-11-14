---
phase: 5
slug: portfolio-and-history
status: approved
reviewed_at: "2026-10-29T13:32:46Z"
shadcn_initialized: true
preset: radix-vega (existing style; no preset URL recorded)
created: 2026-10-29
---

# Phase 5 — UI Design Contract

> Portfolio and History contract for PORT-01..05 and HIST-01..02. Approved by the UI checker on all six dimensions.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn source; preserve `frontend/components.json` and `src/index.css` |
| Preset | Detected `radix-vega`, neutral base, CSS variables, light only |
| Component library | Existing Radix-backed Button, Card and Badge; semantic HTML for data views |
| Icon library | Existing Lucide; 20px controls, 16px inline, decorative icons hidden |
| Font | Existing self-hosted Inter Variable; tabular figures for all numbers |
| Authority | `design-system/birja/MASTER.md`; phase exceptions explicitly listed below |

Sources: REQUIREMENTS/ROADMAP define scope; PROJECT/MASTER define mid valuation and visual language; `05-RESEARCH.md` supplies financial/state defaults adopted here. No CONTEXT exists; the user authorized proceeding from the existing design system. No further style questionnaire or initialization is required. Existing configuration/source inspection satisfies detection; no CLI download or package change is needed.

Local UI-UX searches on 2026-10-29: `responsive table cards --domain ux` matched Table Handling/Horizontal Scroll; `live status screen reader --domain ux` matched Contextual Live Badge Updates; `list key --stack react` matched stable IDs. Apply those relevant recommendations; preserve MASTER's palette and fonts.

| Requirement | Required surface |
|-------------|------------------|
| PORT-01 | Total-value summary, cash card, every positive holding |
| PORT-02 | Total dollar/percentage P/L and starting-cash comparison |
| PORT-03 | Labelled quantity, fee-inclusive average cost, value and unrealized dollar/percentage P/L |
| PORT-04 | Cash-inclusive allocation text and bars |
| PORT-05 | Summary and per-holding price freshness/timestamps |
| HIST-01 | Persisted-fill table/cards with every required field |
| HIST-02 | Deterministic Load more, retry and end state |

## Spacing Scale

| Token / context | Value | Usage |
|-----------------|-------|-------|
| xs / sm | 4px / 8px | Inline icon gap / space between controls |
| compact | 12px | Mobile card gap and internal stacks |
| md | 16px | Mobile gutter/padding; desktop card gap |
| control | 20px | Button horizontal padding |
| lg | 24px | Desktop card padding |
| xl | 32px | Desktop gutters; page top/bottom margin |
| major | 40px / 48px | Reserved existing MASTER scale; no added large gaps |

Use MASTER's 4px scale rather than introducing 64px. Table rows are at least 52px and grow for wrapped timestamps. Buttons/hit areas are at least 44×44px, separated by 8px. Radius: card 24px, control 14px, pill 9999px, allocation bar 6px; use existing shadows. These are component dimensions, not extra spacing tokens.

## Typography

Exactly four sizes and two weights for new page content: **13, 15, 32, 40px; 400 and 500**. Existing shell/pages keep their current hierarchy.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body, row values, helper prose | 15px | 400 | 22px |
| Label, timestamp, freshness badge | 13px | 500 | 18px |
| Section heading, button, emphasized row | 15px | 500 | 22px |
| Page heading | 32px below 768px; 40px otherwise | 500 | 36px / 44px |
| Cash KPI / total-value display | 32px / 40px | 500 | 36px / 44px |

Explicit phase-only MASTER exceptions: section headings use 15/22 at 500 instead of 20/28 at 600; total-value display uses 40/44 on desktop instead of 56/60. This bounds new-page typography while keeping existing sizes, page headings and large numbers. Override new CardTitle/Badge instances as needed; do not change global tokens/components. Body line height remains MASTER's 22/15, not a new 1.5 default. Long exact values wrap without truncation or shrinking text.

## Color

| Role | Value / existing token | Usage |
|------|------------------------|-------|
| Dominant (60%) | `--background` #F2F2F2 | Calm page canvas and neutral negative space |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Cards and secondary controls |
| Accent (10%) | `--data-blue` #4A6BF0 / `--data-blue-text` #3451D1 | Allocation fill, data links; small state emphasis |
| Primary action | `--primary` #18181B | Active nav pill and one principal action per state |
| Gain / loss / warning | Existing `gain`, `loss`, `warn` fill/text/soft families | Signed outcomes / stale data / delayed data and refresh warnings |
| Destructive | `--destructive` #B83270 | No new destructive action in this phase |

The 60/30/10 split is the page emphasis target. Accent is reserved for allocation bars, inline data links and selected/hover tint; focus uses `--ring`, brand orange remains logo-only. Neutral chrome stays neutral. Use MASTER's highlight gradient once on Portfolio's summary, with white text confined to its navy area; no gradient on History or tables. This existing highlight is the deliberate large data-emphasis surface. Never apply gain/loss/warning text tokens over the gradient; put outcome text on its matching light badge surface. Components reference tokens, never raw hex.

## Navigation and Layout

- Add signed-in `/portfolio` and `/history`. Preserve `/` Markets, `/trade/:symbol`, `/account`, account sign-out and existing account health content. Direct links, refresh and browser Back remain functional through the existing auth switch.
- Desktop top navigation: Markets · Portfolio · History; active item is the primary pill with `aria-current="page"`. Keep a separate visible **Account** link in the shell, routing to existing account/sign-out content; this phase does not require a new account menu.
- Below 768px, use MASTER's three-item bottom tab bar with Lucide icon plus text, 56px height plus safe-area inset. Account stays in the top shell. Reserve bottom content padding of `80px + env(safe-area-inset-bottom)` so tabs never obscure content/focus.
- New pages use the existing centered 1440px maximum, 16px mobile/32px desktop gutters. Header has one h1 and secondary **Refresh portfolio** / **Refresh history** control; wrap controls below title when necessary.
- Portfolio: desktop ≥1024px 12-column grid, summary spans 8 and cash/allocation spans 4; holdings spans 12 beneath. At 768–1023px summary/cash each occupy one of two equal columns; holdings spans both. Below 768px all sections stack.
- Summary order: **Total portfolio value**, amount, **Total profit/loss**, signed dollars and percent, **Compared with your {formatted starting_cash} start**, then valuation/freshness detail. Cash card: **Cash**, amount, **Allocation**, then labelled cash/holding bars.
- Holdings heading **Holdings**; helper **Average cost includes buy fees. Values use market mid prices.** Desktop columns in order: Coin, Quantity, Average cost, Mid price, Current value, Unrealized P/L ($ and % together), Allocation, Price updated, Trade.
- At ≥768px use a semantic table in a labelled, keyboard-focusable `overflow-x-auto` region when needed. Headers use `scope="col"`; coin cells are row headers. Only the card may scroll horizontally. Number columns align right; wrap names/timestamps.
- Below 768px replace rows with stacked cards in an ordered semantic list: coin/name and current value first, then a labelled definition list containing every remaining field. Hide the inactive representation with CSS `display:none` so screen readers and keyboard users encounter each record once.
- Active holdings have secondary **Trade {symbol}** links to the existing trade route. Inactive holdings display **Inactive · trading unavailable** with no Trade link. All positive quantities remain visible, including inactive coins; zero quantities are omitted.
- History: one full-width card headed **Executed trades**, helper **Newest first. Times are shown in your local timezone.** Columns: Date/time, Coin, Side, Quantity, Execution price, Fee, Total cash change. Use the same table-to-card behavior and retain every field on mobile.

## Data and Formatting Contract

Adopt the research response fields below in plans, schemas, guards and tests. Monetary/percentage values and history IDs remain exact strings; null means unavailable. Pages perform presentation only, with no monetary arithmetic, Number/parseFloat conversions, or client reconstruction of totals.

| Response | Required fields |
|----------|-----------------|
| Portfolio | `cash`, `starting_cash`, `total_value`, `total_pl`, `total_pl_percent`, `cash_allocation_percent`, `valuation_complete`, `valued_at`, `prices_as_of`, `fresh_seconds`, `stale_seconds`, `holdings` |
| Holding | `symbol`, `name`, `is_active`, `quantity`, `cost_basis`, `average_cost`, `mid`, `current_value`, `unrealized_pl`, `unrealized_pl_percent`, `allocation_percent`, `as_of`, `age_seconds`, `status` |
| History page | `items`, `next_cursor` |
| History item | `id`, `created_at`, `symbol`, `name`, `side`, `quantity`, `exec_price`, `fee`, `total` |

- Use existing string-safe `formatUsd`, `formatUnitPrice`, `formatQuantity`; retain current quantity behavior (up to 8 decimals, trailing zeros removed, no forced 2-place minimum). This explicitly follows shipped Phase 4 behavior where MASTER's quantity example differs.
- USD cash/value/fee/P&L displays two decimals. Unit prices/average cost follow existing ≥$1 two-decimal / below-$1 four-significant-digit formatting. Server percentages already represent percentage points: append `%` to the validated two-decimal string; never use a formatter that multiplies by 100.
- Signed results use `+` for positive, U+2212 `−` for negative, and neutral `0.00` for zero. P/L adds arrow and accessible **Gain**, **Loss**, or **No change** outcome text; color follows each displayed value independently. A rounded 0.00% remains neutral even beside a negative dollar amount.
- History Side uses neutral **Buy** / **Sell** text badges. Total cash change is the stored signed `total`, fee included: buys negative, sells positive/net, zero-proceeds sales `$0.00`. Fee remains separately visible. Do not use P/L colors or gain/loss labels for trade sides/cash transfers.
- Allocation denominator includes cash. Show **Cash** and each actual held symbol/name with its server percentage beside an 8px solid blue bar on a muted track. Text is the accessible equivalent; decorative bars have `aria-hidden="true"`. Use validated 0..100 percentage strings directly as CSS widths, without financial conversion. No invented segments, hatch, donut or chart.
- Independently rounded allocations need not sum to 100.00%; do not adjust a row. Null allocation shows **Unavailable** with no filled bar. Zero-total allocation is unavailable, not 0%. Known 0% allocation has a real empty track and `0.00%` text.
- Display local full date/time including timezone in `<time dateTime={UTC}>` for each price and fill; permit wrapping. Include exact UTC timestamp in `title` and an accessible full timestamp label; no hover-only detail. `valued_at` means **Calculated at**, never price time.

## Freshness and Availability

- Reuse server thresholds and existing age/status helpers. Defaults: **Live** age <120s; **Delayed** age ≥120s and ≤300s; **Stale** age >300s. This explicitly corrects MASTER's illustrative ≤120 wording; shared configured rules are authoritative.
- Age uses server `age_seconds` plus elapsed time since query `dataUpdatedAt`, ticking silently every second. Do not compare browser wall time with provider time. Each priced holding has a text freshness badge plus exact `as_of` timestamp.
- Summary uses the oldest available held price (`prices_as_of`) and worst priced-row state. All fresh: **Oldest price {age}**. Delayed/stale: **Last-known valuation · oldest price {age}** plus the warning copy below. One missing position takes precedence with **Valuation incomplete**; label any remaining timestamp **Oldest available price**.
- Missing price: show quantity/average cost, **Price unavailable** badge, and **Unavailable** for mid/value/dollar and percentage P/L. Preserve known values for other positions. Total value, total P/L and every allocation are unavailable; never show partial totals as complete or substitute zero.
- Zero basis with a known price: show average cost `$0.00`, valid dollar P/L and **Not applicable** for return percent, with **Percentage return is unavailable because cost basis is zero.** Missing-price null percentages use **Unavailable**, not this zero-basis explanation.
- Cash-only accounts show actual cash as total, actual total P/L against starting cash, and 100.00% cash allocation when total is positive. Show **No market prices needed** instead of a freshness badge. A fully liquidated account retains its real P/L; do not restore the starting balance.
- Stale/delayed valuation remains visible at its real last-known mid. Existing trade page still enforces freshness; do not imply the portfolio's Trade link guarantees execution availability.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA, empty portfolio/history | **Browse markets** → `/` |
| Normal page controls | **Refresh portfolio** / **Refresh history**; secondary style |
| Holdings empty heading/body | **No holdings yet** / **Your cash is available to trade. Browse markets to choose a coin.** |
| History empty heading/body | **No trades yet** / **Your executed buys and sells will appear here. Browse markets to make your first trade.** |
| Initial portfolio error | **Can't load your portfolio right now. Try again.**; **Try again** button |
| Initial history error | **Can't load your trade history right now. Try again.**; **Try again** button |
| Background portfolio failure | **Couldn't refresh your portfolio. Showing the last successful update.**; **Retry refresh** |
| Background history failure | **Couldn't refresh your trade history. Showing the last successful update.**; **Retry refresh** |
| Missing-price summary | **Value unavailable** / **Some holdings have no price. Total value, profit/loss and allocation are unavailable until prices return.** |
| Delayed / stale warning | **Some prices are delayed. Values use the last known prices.** / **Some prices are out of date. Values use the last known prices.** |
| Allocation helper | **Share of total portfolio value, including cash.** |
| Zero-total allocation | **Allocation is unavailable while total portfolio value is zero.** |
| Next-page failure | **Couldn't load more trades. Your loaded trades are still here.**; **Try loading more** |
| Pagination pending / idle / end | **Loading more trades…** / **Load more** / **All trades loaded.** |
| Loading / refreshing | **Loading your portfolio** / **Loading trade history** / **Refreshing portfolio…** / **Refreshing history…** |
| Successful append status | **{count} more trades loaded. {total} trades shown.** |
| Destructive confirmation | None added; existing account **Sign out** behavior remains |

## Loading, Refresh and Pagination

- Initial loads reserve summary/card/table shapes with muted skeletons; one labelled status and `aria-busy` on the data region. Skeletons are decorative; never show zero-value placeholders or a full-card spinner.
- Initial errors replace only the affected page's data region with the relevant alert and Retry. Retry refetches the failed read. An empty state is shown only after a successful response with zero rows, never during an error.
- Portfolio refetches every 30s and on focus using existing TanStack patterns. Manual refresh disables itself while pending and shows its refreshing label. Keep previous values and continue aging badges during refresh or failure; never reset age to the request completion time.
- History uses keyset Load more, default 25 rows, opaque `next_cursor`. Preserve response order `(created_at DESC, id DESC)` and use string `id` as React key. Append once, disable Load more during any history fetch, retain rows/cursor on failure, and retry that same next page.
- History has no polling, page numbers, total-count promise or automatic infinite scroll. Refresh/focus/successful-trade invalidation refetch the existing infinite-query chain; newer fills appear through that refresh. Keep loaded rows visible while refreshing, including on failure. Load more is the page's primary action when available; refresh remains secondary.
- At the end, replace Load more with **All trades loaded.** If its focused button disappears, transfer focus to this nearby `tabIndex=-1` end marker; otherwise keep focus on the triggering control. Appending rows never jumps scroll or focuses a row.
- Successful trades (including replay) invalidate portfolio/history alongside existing queries. Do not optimistically calculate balances or append speculative fills. Clear/cancel private queries before a new identity is published; final unauthorized state returns through existing sign-in handling without flashing another account's data.

## Component Inventory and Accessibility

| Component | Contract |
|-----------|----------|
| Signed-in shell | Existing App/nav extended with routes, Account access, responsive tabs and active state |
| Portfolio summary / cash-allocation / holdings | Existing Card/Button/Badge; semantic headings, definition lists, table/list; local helpers only as needed |
| History list and pagination | Existing Card/Button; semantic table/list, stored fill values, retained-data retry |
| Result / freshness / status | Existing Badge/FreshnessBadge, age/money helpers, Lucide arrows; null-aware display and one page status region |

Keyboard order follows visuals; route changes focus the page heading without stealing focus on refetch. Keep 2px ring/2px offset, ≥44px targets and ≥8px control gaps. New nav/row actions override smaller existing variants locally. All data fields remain readable at 200% zoom. Do not make whole rows clickable. Preserve ≥4.5:1 text contrast and labelled non-color outcomes. One atomic polite page status announces refresh results, append counts and meaningful freshness transitions; never announce every second or make every badge a live region. Errors use alerts once per failure. Respect reduced motion: disable crossfades/press transforms and skeleton animation; no animated bar width, count-up numbers or price flashing is needed.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official / existing local source | Button, Card, Badge; no downloaded block | Not required; local source/config inspected 2026-10-29 |
| Third-party | None; `registries: {}` confirmed | Not applicable — no external registry/block introduced, 2026-10-29 |

## Verification Targets

At **375, 768, 1024 and 1440px**, check nav/safe area, summary grid, readable wrapped timestamps/large values, all mobile fields, keyboard table scrolling, no horizontal page overflow and one accessible representation per record. Check keyboard/focus/200% zoom and reduced motion. Behavioral fixtures must cover cash-only/full liquidation, positive/negative/rounded-zero P/L, zero basis, inactive holdings, missing one price, 119/120/300/301s transitions, last-known/failed refresh, initial failure/retry, empty history, multiple pages/tied timestamps, append failure/retry/end focus, exact stored fee-inclusive totals and identity changes. Preserve markets/account/auth/trade regressions. These are implementation verification targets; no UI or runtime tests were executed for this documentation task.

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-10-29; six PASS verdicts, no recommendations. UI checker was read-only; the orchestrator recorded its verdict.
