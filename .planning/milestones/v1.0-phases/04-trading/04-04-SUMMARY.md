---
phase: 04-trading
plan: 04
subsystem: frontend
tags: [react, tanstack-query, api-contract, money]
requires: [04-01]
provides: [api/trades.ts, ApiError.detail, formatQuantity, useDebouncedValue, useQuote, useTrade, useHolding]
affects: [04-07]
key-files:
  created:
    - frontend/src/api/trades.ts
    - frontend/src/api/trades.test.ts
    - frontend/src/hooks/useDebouncedValue.ts
    - frontend/src/hooks/useDebouncedValue.test.ts
    - frontend/src/hooks/useQuote.ts
    - frontend/src/hooks/useTrade.ts
    - frontend/src/hooks/useHolding.ts
  modified:
    - frontend/src/api/client.ts
    - frontend/src/api/client.test.ts
    - frontend/src/lib/money.ts
    - frontend/src/lib/money.test.ts
metrics:
  completed: 2026-10-28
  tasks: 2
---

# Phase 4 Plan 04: Frontend trade API contract and hooks Summary

Typed, runtime-guarded trade API (quote, execute, holding) with `ApiError.detail`, `formatQuantity`, and TanStack hooks (debounced quote, trade mutation with cache invalidation, holding), with no client-side money math.

## Commits
- Task 1: feat(04-04) typed trade API layer, ApiError.detail, formatQuantity
- Task 2: feat(04-04) debounced quote, trade and holding hooks

## Verification
lint, typecheck, prettier, vitest (133 passed, coverage 94% overall) and build pass. `parseFloat|Number(` count is 0 in trades.ts and money.ts.

## Deviations from Plan
None. `ApiError`'s 5th constructor argument defaults to null, so no other call sites needed changes.

## Notes
- useQuote, useTrade and useHolding have no direct tests (0% coverage, as the plan states); 04-07's TradePage tests must exercise them.
- Playwright and docker not run (as instructed).

## Self-Check: PASSED
