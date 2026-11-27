---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "04"
subsystem: frontend
tags: [history, react, portfolio, pagination, accessibility]
requires:
  - phase: "25-02"
    provides: Owned mixed History filters and filter-bound continuations
provides:
  - Compact History toolbar and disclosure list for the selected portfolio
  - Server-filtered activity and assets with distinct private query scopes
  - Continued access to exact correction originals and catalog trade links
affects: [25-05]
tech-stack:
  added: []
  patterns: [query-bound-cursor, owned-infinite-query, native-event-disclosure]
key-files:
  created:
    - frontend/src/pages/historyWorkspace.css
  modified:
    - frontend/src/api/history.ts
    - frontend/src/api/history.test.ts
    - frontend/src/api/eventHistory.ts
    - frontend/src/api/eventHistory.test.ts
    - frontend/src/hooks/useEventHistory.ts
    - frontend/src/hooks/useEventHistory.test.tsx
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/pages/HistoryPage.test.tsx
key-decisions:
  - Discard the previous scope's pages so returning to a filter begins with a fresh first page.
  - Use the browser's local date and short time in the list while retaining the exact recorded timestamp and event detail.
requirements-completed: [FLOW-02]
completed: 2026-11-26
---

# Phase 25 Plan 04 — Filtered portfolio History

The compact History workspace shows events from the selected portfolio.
Activity and asset filters request the full matching server result before
pagination. The client validates that the continuation belongs to the same
portfolio and filter pair. Mixed all/all retains v3 and trade-only callers
retain v2. The native disclosures preserve exact event details and the
original dividend when it falls outside the loaded page or selected filters.

| Task | Result | Commit |
|---|---|---|
| 25-04-01 | Typed filters and scope-checked requests and continuations | `3bcd4dc` |
| 25-04-02 | Compact toolbar, date groups, scoped requests and focus recovery | `49e00bc` |

## Verification

- The two API suites passed 95 tests. The complete six-file Plan 25-04 suite
  passed 184 tests, including existing private-target, catalog identity,
  correction, retry and append focus coverage.
- Focused tests verified v4 continuation with an active filter, focus transfer
  at the final append, aborting an obsolete append, ignoring its late result,
  discarding a late session refusal from an obsolete scope and returning to the
  first page when filters are cleared.
- TypeScript, scoped ESLint, Prettier and commit diff checks passed.
- Plan 25-05 covers integrated Chromium sessions, captures and geometry checks.

## Deviations

The plan's two source commits cover the declared files. The standalone checks
used the existing installed frontend dependencies.

## Self-Check: PASSED

Both commits are present in the phase branch. They touch the nine declared
files and include no file deletions. The verified History route requests the
actual selected portfolio, and its empty/loading/recovery views reflect the
current server query.
