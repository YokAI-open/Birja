---
phase: 23-show-historical-market-prices
plan: "03"
subsystem: markets-ui
tags: [react, tanstack-query, canvas, accessibility]
requires:
  - phase: 23-02
    provides: "Authenticated history API with exact selectors and normalized prices"
provides:
  - "Selectable price history with an equivalent accessible table"
  - "Markets layout with ticker tiles, aligned prices, and an independent trade action"
affects: [23-04]
tech-stack:
  added: []
  patterns: [session-scoped-query, responsive-canvas, progressive-disclosure]
key-files:
  created:
    - frontend/src/api/marketHistory.ts
    - frontend/src/api/marketHistory.test.ts
    - frontend/src/hooks/useMarketHistory.ts
    - frontend/src/components/MarketHistoryChart.tsx
    - frontend/src/components/MarketHistoryChart.test.tsx
  modified:
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
    - frontend/src/pages/markets.css
    - design-system/birja/pages/markets.md
key-decisions:
  - "Only the selected exact instrument and range request history."
  - "The chart uses the established neutral data-fill token, with gain and loss colors reserved for changes."
  - "The selected catalog row displays its already-fetched eligible midpoint."
requirements-addressed: [CHART-01, CHART-02, CHART-03]
requirements-completed: []
duration: 12min
completed: 2026-11-26
---

# Phase 23 Plan 03 Summary

Markets shows the selected instrument's history below its current quote, with
1D, 1W and 1M controls and a Price data disclosure for exact bar closes.

## Implementation

- The decoder checks response identity, listing version, range, source,
  time basis, decimal closes, interval order, gaps and timeliness. The
  authenticated query uses the active session epoch and exact selection.
  Changing context cancels the old request. Pending replies receive at most
  three followups within a twelve-second request window.
- The Canvas plot uses the normalized bars and stops each line at a missing
  interval or closed market. The table retains the decimal closes and local
  timestamps, including the reason for each break. Chart status and data
  are independent of current quote, reopening and trade behavior.
- The Markets workspace follows the ZIP's desktop split and mobile stacking.
  It uses 38px ticker tiles, aligned Price and Day columns, a compact quote
  header and a right-aligned action. Only comparable Day values returned for
  the selected instrument appear in the list. The catalog's selected row
  shares the currently permitted quote already displayed in the detail panel.
- Real provider attribution, time-basis labels and price data disclosure
  add content beyond the ZIP. The demo selector and mock holding and price
  values are absent from the runtime.

## Tasks and verification

| Task | Commit | Result |
|---|---|---|
| Connect cancellable history queries and render the series | `eb25cba` | Twenty-eight chart and decoder tests passed. |
| Restore the Markets composition from the approved ZIP | `6a9839c` | Fifty-three decoder, chart and Markets tests passed together. TypeScript, ESLint and scoped Prettier checks passed. |

Tests exercise malformed decimals and mismatched listing versions, keyboard
range changes, precise price data, delayed and partial series, bounded
pending polling and cancellation on selection or session change. A Markets
case confirms that a failed chart range clears its Day figure and preserves
the current quote and portfolio-scoped BTC trade action. Existing Phase 22
catalog and market-status assertions remain covered.

## Deviations from the plan

No scope changes. The catalog price assertions are scoped to the detail region
or selected row now that the approved layout shows the same permitted
midpoint in both places.

## Remaining evidence

The isolated browser comparison and current-order regression checks are
Plan 23-04 work. Provider scope remains disabled pending separate live
qualification. [Source qualification](23-SOURCE-QUALIFICATION.md)

## Self-Check: PASSED
