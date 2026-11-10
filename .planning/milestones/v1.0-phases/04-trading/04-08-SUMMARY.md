---
phase: 04-trading
plan: 08
subsystem: api
tags: [fastapi, pydantic, trading, concurrency, idempotency]
requires: [04-06]
provides: [POST /api/v1/trades/quote, POST /api/v1/trades, GET /api/v1/holdings/{symbol}]
affects: [04-07 frontend, 04-09 e2e/CI]
key-files:
  created:
    - backend/app/schemas/trades.py
    - backend/app/api/v1/trades.py
    - backend/tests/test_trades_api.py
    - backend/tests/test_trading_concurrency.py
  modified:
    - backend/app/api/v1/router.py
    - backend/tests/test_accounts.py
requirements-completed: [TRADE-01, TRADE-02, TRADE-03, TRADE-05, TRADE-06, TRADE-07, TRADE-08]
completed: 2026-10-28
---

# Phase 4 Plan 08: Trade routes and concurrency proof Summary

Thin FastAPI trade routes (quote, execute with 201/200-replay, holding) with plain-decimal money output and stable `detail.code` errors, plus real-Postgres concurrency tests proving no overspend, oversell or double fill.

## Commits
- 580eef3 feat(04-08): trade quote, execute and holding routes
- eff86e2 test(04-08): API tests for every endpoint, status and code
- 20f8538 test(04-08): concurrency proof and route allow-list update

## What was built
- `schemas/trades.py`: `Money` (PlainSerializer, `format(v, "f")`), `QuoteIn` (extra=forbid, exactly one input, sells by quantity, dp caps), `TradeIn`, `QuoteOut`, `FillOut`, `HoldingOut`.
- `api/v1/trades.py`: three routes, CurrentUserDep on all, `verify_csrf` on both POSTs, `Cache-Control: no-store`, `STATUS` map, `detail.quote` on `price_changed`.
- Tests: 33 API test cases (17 functions, parametrized) and 4 concurrency tests.

## Mutation check
Removed `.with_for_update()` from the Account select in `trading.py`: `test_parallel_buys_never_overspend` failed in 3 of 3 runs (`UniqueViolationError: uq_holdings_user_coin`, two concurrent first buys creating the holding row). Line restored via `git checkout`, tests green, `git diff` on trading.py clean; mutated file never committed.

## Verification
- Full suite: 476 passed, coverage 99.89% (gate 80%).
- Critical-path list from CLAUDE.md plus trade_math, trading, api/v1/trades, schemas/trades: 100%.
- ruff, ruff format, mypy clean.

## Deviations from Plan
**[Rule 1 - Bug/consequence] `test_route_allow_list_has_no_cash_mutation`** in `backend/tests/test_accounts.py` pins the exact OpenAPI route set; added the three new trade routes. No service bugs found.

Minor: `to_order` uses `cast(Decimal, ...)` instead of `assert` (ruff S101). The 04-08 plan's "at least 20 `async def test_`" grep is 17 functions (33 with parametrization); every contract status is asserted.

## Known Stubs
None.

## Self-Check: PASSED
Files and the three commits exist; test stack torn down.
