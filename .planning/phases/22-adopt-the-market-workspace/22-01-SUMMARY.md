---
phase: 22-adopt-the-market-workspace
plan: "01"
subsystem: ui
tags: [react, tailwind, markets, keyboard, vitest, playwright]
requires:
  - phase: 20-trade-and-value-stocks-from-search
    provides: "Stock catalog results, current quotes and stable trade targets"
provides:
  - "Single-row header with the three main destinations and account door"
  - "Stock-first Markets discovery and responsive current-price detail"
affects: [22-02, 22-03, 23]
tech-stack:
  added: []
  patterns: [existing theme tokens, ruled scrolling asset list, keyboard focus return]
key-files:
  created: []
  modified:
    - frontend/src/App.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/markets.css
    - design-system/birja/pages/markets.md
key-decisions:
  - "US stocks open by default. Empty search shows the original list from the curated endpoint."
  - "Mobile keeps the search and list in the document and returns focus to the selected row."
requirements-completed: [WS-01, WS-02, WS-03]
duration: 5min
completed: 2026-11-26
---

# Phase 22 Plan 01 — Header and market discovery

**The Markets screen opens with the original stocks and places their current-price detail beside the list on desktop and below it on phones.**

- Kept the Birja brand, destinations and account door in one header row. The original route and account handlers still apply.
- Reused the curated, catalog and crypto queries with their current result and quote handling. The stock search retains bounded results, explicit catalog selection, failures and curated fallback.
- Preserved mobile search context and added Back to results with focus return. The desktop panel uses the existing project tokens.

## Local commits

| Task | Commit |
|---|---|
| Header row and account action | `4a2d9ce` |
| Stock-first workspace, component checks and design notes | `7334d2f` |
| Browser journey locators and asset-tab selection | `442d46a` |

## Verification

- Header task lint and typecheck passed. The App suite passed 65 tests.
- Typecheck and all 137 focused tests across App, MarketsPage and useStocks passed after the workspace change.
- Prettier passed on the eight changed browser specs. Playwright discovered all 68 tests across those specs. Browser execution and measured reflow belong to Plan 22-03.
- The 14 changed files remain in the feature worktree. All three task commits exist and the task diff contains no file deletions.

## Deviations

Two additional existing browser specs used the previous mobile return label. Updated only that locator in `frontend/e2e/stocks.spec.ts` and `frontend/e2e/stock-actions.spec.ts`, preserving their assertions. Both passed browser test discovery.

## Handoff

Plan 22-02 owns the in-place portfolio chooser and calendar-bound countdown. Plan 22-03 owns browser acceptance of all Phase 22 requirements. Historical chart work is scoped to Phase 23.

## Self-Check: PASSED
