---
phase: 22-adopt-the-market-workspace
plan: "02"
subsystem: ui
tags: [markets, portfolios, stocks, session-hours, accessibility]
requires:
  - phase: 22-01
    provides: Stock-first Markets layout, result focus and retained discovery
provides:
  - An in-place Markets portfolio chooser and authority-gated trade links
  - A verified reopening countdown with local-time metadata
affects: [22-03 browser proof, 23 historical prices]
tech-stack:
  added: []
  patterns: [Existing signed-in portfolio authority, server session timestamps]
key-files:
  created: []
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/components/MarketOpening.tsx
    - frontend/src/components/PortfolioSwitcher.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
key-decisions:
  - Keep portfolio selection in the current signed-in session.
  - Keep an unavailable explicit portfolio from falling through to the legacy route.
  - Keep the visible countdown concise and expose the opening time in the user's time zone.
requirements-completed: [WS-01, WS-03, WS-04]
duration: 5 min
completed: 2026-11-26
---

# Phase 22 Plan 02 Summary

The selected instrument and quote stay in view when the user switches
portfolios. The trade link uses the chosen portfolio once its access is
verified. When access is pending or unavailable, Markets keeps the quote
visible and prompts for an available portfolio.

Curated and catalog results use their own verified opening timestamps. The
closed state keeps the last permitted price and shows the reopening
countdown, with the local opening time available to screen readers and as a
tooltip. Trade readiness still depends on the existing quote response.

## Task commits

| Task | Commit | Verification |
|---|---|---|
| Select the trading portfolio without losing the instrument | `75239c8` | 158 tests across App, Markets, PortfolioSwitcher and usePortfolioTarget |
| Render the verified last price and reopening countdown | `3a3dc22` | 116 tests across Markets, useStocks and both stock trade pages |

Type checking and lint passed after the countdown change. Focused tests cover
a portfolio change without navigation, preserved catalog identity, pending
and revoked access, the last mark over a weekend, early close and holiday,
and reopening with an outstanding quote refresh.

## Execution notes

The three curated mark fixtures include the attribution metadata required by
the existing API contract. The catalog identity test changes the portfolio
within the mounted test app so it retains the query provider and selection.
The orchestrator will update shared state when the browser and verification
waves finish.

## Self-Check: PASSED

Both task commits are present. The working tree matched the plan changes
before this summary was added.
