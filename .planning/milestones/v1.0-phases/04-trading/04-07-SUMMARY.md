---
phase: 04-trading
plan: 07
subsystem: frontend
tags: [react, tanstack-query, trading, idempotency]
requires: [04-04]
provides: [TradePage, "/trade/:symbol route", "Markets Trade links"]
affects: [frontend/src/App.tsx, frontend/src/pages/MarketsPage.tsx]
key-files:
  created: [frontend/src/pages/TradePage.tsx, frontend/src/pages/TradePage.test.tsx]
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
decisions:
  - "Idempotency key lives in a useRef; cleared only in edit handlers (side, kind, input, New order) and in mutate onSuccess / terminal-code onError / price_changed. Quote refetches never touch it."
  - "Confirm requires the debounced order to equal the current order and a non-placeholder quote, so a stale preview from a previous input can never be confirmed."
  - "Non-live (Delayed or Stale) prices show the MASTER pause message and disable Confirm; no quote is requested."
metrics:
  tasks: 2
  completed: 2026-10-28
---

# Phase 4 Plan 07: Trade page Summary

The `/trade/:symbol` page (preview, confirm, fill, refusals, price_changed) and a Trade link on every Markets row, with an idempotency key that survives quote refetches.

## Commits

- e4b3847 feat(04-07): Link Markets rows to the /trade/:symbol route
- 23949eb feat(04-07): Build the trade page with preview, confirm and fill

## Verification

Run in the worktree: `npm ci`, eslint, `tsc -b`, prettier --check, `vitest --coverage` (161 tests pass; 98.88% statements overall), `vite build`. No Playwright or docker run (per instructions).

- TradePage has 25 tests. They drive useQuote (debounce, 30 s refetch, 401 invalidates `["me"]`, unknown_coin), useTrade (success invalidates me, holding and prices) and useHolding through the page.
- Idempotency cases tested: same key on network-error retry; same key when a 30 s refetch moves the mid between the failed attempt and the retry (expected_mid is the new mid); new key after an edit, after a fill, after price_changed; double-click sends one POST.
- Refusal dispatch on `detail.code`: insufficient_cash, below_minimum, order_too_large, insufficient_quantity, stale_price, price_changed (valid and invalid quote), unknown_coin (quote and trade), network error.

## Deviations from Plan

- MarketsPage fixture has 15 coins (not 16 as the plan text says); the link assertion uses 15.
- Rule 3: the worktree was created at the wrong base and was reset to 1945ae8 as instructed.
- Plan commit trailer used as instructed by the orchestrator (Opus 5.5), overriding the system attribution line.
- useTrade does not invalidate `["me"]` on a 401 (only useQuote and usePrices do); left unchanged as 04-04 code, not covered by this plan.

## Known Stubs

None.

## Notes

- `useQuote.ts` line 22 (the "No order to quote" guard) stays uncovered; it is unreachable because the query is disabled when the order is null.
- Delayed (aging) prices also pause trading and show the same MASTER message; MASTER only defines copy for stale.
- Money is only formatted, never computed; the only added string logic is a "+" prefix for non-negative cash deltas.

## Self-Check: PASSED

TradePage.tsx, TradePage.test.tsx exist; commits e4b3847 and 23949eb exist.
