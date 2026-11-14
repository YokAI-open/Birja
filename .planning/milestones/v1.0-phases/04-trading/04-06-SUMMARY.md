---
phase: 04-trading
plan: 06
subsystem: trading
tags: [trading, postgres, idempotency, locking, cost-basis]
requires: [04-02, 04-03]
provides: [trading.quote, trading.execute, trading.holding_quantity, Order, Quote, Fill, PriceChanged]
affects: [04-08]
key-files:
  created:
    - backend/app/services/trading.py
    - backend/tests/test_trading_service.py
  modified:
    - backend/tests/helpers.py
    - backend/tests/conftest.py
    - .github/workflows/ci.yml
    - CLAUDE.md
decisions:
  - "Fill is built from the refreshed Trade row (flush + refresh before commit), so new and replayed fills are identical and no post-commit re-read or assert is needed."
  - "Replay fills are built before the rollback, since rollback expires the loaded row."
metrics:
  completed: 2026-10-28
  tasks: 3
---

# Phase 4 Plan 06: Trading service Summary

Locked, idempotent trade execution: account FOR UPDATE, replay lookup before any price check, Live-price check via `freshness()`, holding FOR UPDATE, `plan_trade`, `price_changed` on a different mid, then cash, holding, cost basis and trade row in one transaction.

## Commits
- 22ab0d7 test(04-06): failing service tests (RED)
- c8cf4a2 feat(04-06): trading.py (GREEN)
- 05b6765 chore(04-06): critical-path list in ci.yml and CLAUDE.md

## Verification
- Full backend suite: 439 passed, 99.88% total.
- Critical-path report (now incl. trade_math.py, trading.py): 100% line+branch.
- ruff, ruff format, mypy: clean. No pragma exclusions in trading.py.
- Race backstop, row-gone re-raise and non-swallowed CHECK IntegrityError all covered by monkeypatched real-Postgres tests.

## Deviations from Plan
- Step (9) "re-read the committed row" replaced by `db.refresh(trade)` before commit (same persisted values, avoids an unreachable `None` branch). Behavior unchanged.
- Test count: 25 test functions (3 refusals parametrized).
- CLAUDE.md/ci.yml lists identical, appended in the order trade_math.py, trading.py.

## Known Stubs
None.

## Self-Check: PASSED
