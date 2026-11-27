---
phase: 23-show-historical-market-prices
plan: "05"
subsystem: market-history
tags: [coin-metrics, fastapi, redis, scheduler]
requires:
  - phase: 23-04
    provides: Private market history API and bounded worker
provides:
  - Native production crypto charts from Coin Metrics Community USD prices
  - Distinct chart-only quota and an operator switch on both services
affects: [23-06, 23-07]
tech-stack:
  added: []
  patterns: [coalesced-memory-only-history, fixed-host-source, decimal-closes]
key-files:
  modified:
    - backend/app/core/config.py
    - backend/app/schemas/market_history.py
    - backend/app/services/market_history.py
    - backend/app/services/market_history_authority.py
    - backend/app/services/market_history_providers.py
    - backend/app/tasks/market_history.py
    - backend/app/tasks/scheduler.py
    - backend/tests/test_market_history_providers.py
    - backend/tests/test_market_history_scheduler.py
    - docker-compose.prod.yml
key-decisions:
  - Coin Metrics Community serves chart history in the noncommercial deployment.
  - Preserve actual UTC observation times and visible gaps.
  - Bound the chart source independently of quote and execution feeds.
requirements-addressed: [CHART-01, CHART-02, CHART-03, CHART-04]
requirements-completed: []
completed: 2026-11-27
---

# Phase 23 Plan 05 Summary

Coin Metrics Community now supplies Birja's native crypto chart via the
authenticated history API, coalesced demand and existing dedicated scheduler.

## Behavior

- The 1D chart selects exact five-minute boundaries from minute reference
  rates. The 1W chart uses hourly reference rates. The 1M chart uses published
  daily USD closes and records each at its following UTC midnight.
- Production limits coverage to the 15 curated coins and enables the switch
  in both service definitions. Setting
  `MARKET_HISTORY_COIN_METRICS_ENABLED=false` disables native crypto history.
  Production ignores legacy history scopes. The test and development
  fixtures keep their existing coverage.
- The keyless source uses one bounded response per job and a shared
  20-attempt rolling minute budget. The cache keeps results for up to two
  minutes for 1D and ten minutes otherwise, also bounded by the active
  observation window. Current quotes and trade execution are independent.
- Live sampling found occasional extra decimal places for DOGE and XLM.
  The adapter explicitly rounds excess source precision half-even to the
  existing 12-place contract and preserves shorter values.

## Verification

All 97 focused backend cases passed against disposable PostgreSQL and Redis,
including authenticated private output, scope isolation, independent quota
and provider response checks. Ruff and mypy passed. Synthetic Compose
rendering confirmed both switch values on backend and scheduler.

Twelve requests to the public Coin Metrics endpoint exercised the exact
adapter for BTC, ETH, DOGE and XLM. Each returned 288 complete 1D points,
168 complete 1W points and 30 complete 1M points. The latest observations
were 12:40, 12:00 and 00:00 UTC respectively on November 27. Both daily
and period changes were available in these windows.

Coin Metrics Community is available under a noncommercial license with
attribution. [Community API documentation](https://github.com/coinmetrics/product-docs/blob/master/docs/access-our-data/api/README.md) · [Community data license](https://github.com/coinmetrics/data/blob/master/LICENSE)

## Self-Check: PASSED

The focused tests and public source probes verified the backend candidate.
Production integration and Phase 23 closeout are tracked in
[Plan 23-07](23-07-PLAN.md).
