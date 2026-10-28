---
phase: 03-prices
plan: 04
subsystem: frontend
tags: [react-router, tanstack-query, markets, prices]
requires: [03-01]
provides:
  - fetchPrices/isPrices (validated /api/v1/prices client)
  - usePrices (30 s polling, 401 invalidates ["me"])
  - formatUnitPrice (D-06)
  - MarketsPage at / and Account (+ System status) at /account
affects: [03-06]
tech-stack:
  added: []
  patterns: [string-based decimal formatting, router-aware test render]
key-files:
  created:
    - frontend/src/api/prices.ts
    - frontend/src/api/prices.test.ts
    - frontend/src/hooks/usePrices.ts
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
  modified:
    - frontend/src/lib/money.ts
    - frontend/src/lib/money.test.ts
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/main.tsx
    - frontend/src/test/render.tsx
    - frontend/src/pages/SignInPage.test.tsx
    - frontend/e2e/auth.spec.ts
    - frontend/e2e/health.spec.ts
decisions:
  - "Signed-out visitors get the sign-in card on every URL with no redirect, so a user stays on the URL they opened after signing in"
  - "Intl 4-significant-digit output matched every expected string; no implementation workaround needed"
metrics:
  completed: 2026-10-28
  tasks: 2
---

# Phase 3 Plan 04: Markets page and routing Summary

Signed-in users land on a Markets table (symbol, name, USD price) polled every 30 s through TanStack Query, with Account and System status moved to `/account` behind react-router.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 | Prices API + validator, `usePrices`, `formatUnitPrice`, `MarketsPage` with loading/empty/error states | e0ae6e6 |
| 2 | `BrowserRouter`, nav, `/` and `/account` routes, router-aware test render, updated e2e specs | ab3fa7f |

## Verification

- Vitest: 93 tests pass; coverage 98% statements, 95% branches (threshold 80%).
- lint, typecheck, prettier and `npm run build` pass.
- `npx playwright test --list` lists auth, csp, health and markets specs. Playwright was not run (per instructions; CI runs it).
- Built against the contract with stubbed fetch; the real 03-02 endpoint was not exercised.

## Deviations from Plan

**1. [Rule 3 - Blocking] SignInPage.test.tsx updated**
- Issue: the "puts the user in the me cache" test expected the account view at `/`; signed-in users now land on Markets.
- Fix: render that test at route `/account`.
- File: `frontend/src/pages/SignInPage.test.tsx`

**2. [Rule 3 - Blocking] e2e imports use `./helpers.js`**
- Issue: the node tsconfig requires explicit extensions (same as 03-01).

**3. [Rule 2 - Coverage] Added a test for the T-03-15 mitigation**
- A mid-session 401 from prices invalidates `["me"]` and the app falls back to the sign-in card (`App.test.tsx`).

## Known Stubs

None. A comment in `MarketsPage.tsx` marks where 03-06 adds the freshness column (no placeholder column).

## Self-Check: PASSED
