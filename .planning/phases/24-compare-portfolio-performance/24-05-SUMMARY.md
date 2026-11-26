---
phase: 24-compare-portfolio-performance
plan: "05"
subsystem: ui
tags: [portfolio, react, tanstack-query, canvas, accessibility]
requires:
  - phase: 24-04
    provides: Owner-scoped, exact-cent daily value observations and a 30-day batch endpoint
provides:
  - Independently fetched and guarded daily values for active portfolio cards
  - Responsive strategy cards with real values, signed returns and gap-aware sparklines
affects: [24-07, 24-08]
tech-stack:
  added: []
  patterns: [Independent private query, UTC-window Canvas, exact cents normalization]
key-files:
  created:
    - frontend/src/api/portfolioValueHistory.ts
    - frontend/src/api/portfolioValueHistory.test.ts
    - frontend/src/hooks/usePortfolioValueHistory.ts
    - frontend/src/hooks/usePortfolioValueHistory.test.tsx
    - frontend/src/components/PortfolioValueSparkline.tsx
    - frontend/src/components/PortfolioValueSparkline.test.tsx
    - frontend/src/pages/portfolioOverview.css
  modified:
    - frontend/src/pages/PortfoliosPage.tsx
    - frontend/src/pages/PortfoliosPage.test.tsx
key-decisions:
  - Bind each trend request to the signed-in owner, session epoch, deletion state and exact ordered active portfolio IDs.
  - Reveal first and last recorded UTC values and exact signed change through the card description. Show one overview-level retry on history failure.
requirements-completed: [TREND-01, TREND-02]
completed: 2026-11-26
---

# Phase 24 Plan 05 Portfolio overview and daily trends

Every active portfolio card links to its own workspace and shows its current
value, return and cash alongside a separate trend over 30 UTC days. The
sparkline breaks at missing observations. Current figures and portfolio
controls stay usable through history loading, gaps and errors.

## Task commits

- `f60d0c3` loads exact private history with session and active-set guards.
- `4546fdb` renders the responsive cards, keyboard-accessible summaries and
  gap-aware sparklines, with a single retry control outside the grid.

## Verification

- All 56 focused tests passed across the history decoder, history and overview
  hooks, card layout, and Canvas geometry. The tests distinguish missing and
  null observations, prove cent-precise amounts above the JS-safe limit,
  check the exact card links and guard late responses after owner or membership
  changes.
- Frontend lint and type checking passed. Prettier passed for all nine plan
  files.
- A running localhost application with synthetic responses matched the approved
  overview grid coordinates at 1440px and 390px. The desktop grid starts at
  `(40, 127)` with three approximately 443 × 245 cards and 16px gaps. The
  phone grid starts at `(16, 88)` with a 358px width, 200px strategy cards
  and a 120px creation card. The Canvas slot measures 44px as specified.
  Keyboard navigation follows the strategy cards and then New portfolio.
  Checks at 320px and 640px with simulated 200% root text showed no horizontal
  overflow. Native browser zoom remains part of Phase 24 acceptance.

## Deviations from plan

**[Rule 1 – Focus recovery]** The former creation card received focus after
closing an unresolved creation request, even at capacity. The approved cap
state disables that card, so focus now returns to Review original creation.
The regression check also confirms the existing retry still works at capacity.

**[Rule 2 – Retry feedback]** The card integration refined the history hook
to keep the retry control reachable while the request is pending. The history
hook tests exercise that state with a delayed response.

## Self-Check: PASSED

Both task commits exist and contain only the intended plan paths. The
working source uses the current statement and daily-value APIs. Neither
task deletes files or introduces runtime placeholders. The phase
orchestrator owns the shared phase and requirement records.
