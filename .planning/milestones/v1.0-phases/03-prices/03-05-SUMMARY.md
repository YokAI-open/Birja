---
phase: 03-prices
plan: 05
subsystem: api
tags: [scheduler, redis-lock, prices, kraken]
requires:
  - phase: 03-prices/02
    provides: coins/prices tables
  - phase: 03-prices/03
    provides: price_rules, kraken client
provides:
  - tasks/scheduler.py run_cycle, CycleResult, LOCK_KEY, build_source, SOURCE_TIMEOUT_S
  - services/prices.py load_active_coins, upsert_prices (as_of never backwards)
  - services/fake_prices.py (dev/CI source, refused in prod)
  - Settings price_source, price_poll_interval_seconds, price_max_move, price_confirm_tolerance, price_confirm_polls
  - prices.py on the 100% critical-path list (ci.yml and CLAUDE.md identical)
affects: [03-07]
key-files:
  created:
    - backend/app/tasks/__init__.py
    - backend/app/tasks/scheduler.py
    - backend/app/services/fake_prices.py
    - backend/tests/test_scheduler.py
    - backend/tests/test_fake_prices.py
  modified:
    - backend/app/core/config.py
    - backend/app/services/prices.py
    - backend/tests/conftest.py
    - backend/tests/test_config_prices.py
    - .github/workflows/ci.yml
    - CLAUDE.md
metrics:
  completed: 2026-10-28
---

# Phase 3 Plan 05: Refresh cycle, fake source and price writes Summary

A single locked refresh cycle (Redis SET NX PX 45 s, Lua compare-and-delete in finally) fetches all coins in one call, evaluates each mid, and upserts accepted prices with as_of = arrival time; rejected data leaves the last good price aging.

## Commits

- 9348189 feat(03-05): scheduler settings, fake price source, price writes
- Task 2 feat(03-05) commit: run_cycle, tests, CI/CLAUDE.md list (see git log)

## Verification

- Full backend suite: 280 passed, coverage 99.83%; critical-path report (incl. price_rules.py, prices.py) 100%. scheduler.py and fake_prices.py also 100%.
- ruff check, ruff format --check, mypy clean. actionlint 1.7.7 clean.
- Tests run on the test stack with respx; no Kraken calls.

## Deviations from Plan

- Orchestrator addition implemented: source call wrapped in `asyncio.timeout(SOURCE_TIMEOUT_S = 35)` (< LOCK_TTL_MS 45 s) with a test that patches it small and asserts source_error plus lock release.
- Worktree base was reset to f36577d at start (merge-base check failed).
- Added tests beyond the list: unexpected exception contained, release failure logged, no active coins, foreign lock never deleted.

## Known Stubs

None.

## Self-Check: PASSED
