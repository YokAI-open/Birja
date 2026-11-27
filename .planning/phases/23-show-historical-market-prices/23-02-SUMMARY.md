---
phase: 23-show-historical-market-prices
plan: "02"
subsystem: market-history
tags: [fastapi, redis, scheduler, alpaca, kraken]
requires:
  - phase: 23-01
    provides: "Typed selectors, history windows, normalized series, and isolated source adapters"
provides:
  - "Authenticated chart API and coalesced expiring read demand"
  - "Exact identity, calendar and source evidence checks at read, fetch and publication"
  - "Isolated chart worker and bounded shared provider accounting"
affects: [23-03, 23-04]
tech-stack:
  added: []
  patterns: [memory-only-display-cache, bounded-demand, shared-attempt-accounting]
key-files:
  created:
    - backend/app/api/v2/market_history.py
    - backend/app/services/market_history_authority.py
    - backend/app/services/market_history_demand.py
    - backend/app/tasks/market_history.py
    - backend/tests/test_market_history_api.py
    - backend/tests/test_market_history_scheduler.py
  modified:
    - backend/app/api/v2/router.py
    - backend/app/core/config.py
    - backend/app/schemas/market_history.py
    - backend/app/services/kraken.py
    - backend/app/tasks/scheduler.py
    - backend/app/tasks/stock_scheduler.py
    - docker-compose.yml
    - docker-compose.prod.yml
key-decisions:
  - "Historical equity scope binds an explicitly evidenced start date to each exact provider identity."
  - "Use the admitted calendar to derive stable completed-bar windows."
  - "Kraken history waits for a known ticker window and reserves for both observed attempts and the overlapping retry and pair fallback budget."
requirements-addressed: [CHART-01, CHART-03, CHART-04]
requirements-completed: []
duration: 18min
completed: 2026-11-26
---

# Phase 23 Plan 02 Summary

Birja can now read or queue a selected history series through the authenticated
API, with scheduler-only upstream access and shared provider attempt accounting.

## Implementation

- `POST /api/v2/market-history/query` uses the Phase 23 typed instrument and
  range contract, authentication, CSRF and private no-store handling. A stale
  catalog version returns `409 listing_changed`. The API resolves current
  identity and scope before queueing and checks them again before returning
  a cached series.
- The memory-only cache uses fingerprints for the exact source scope,
  identity, range and window. Redis bounds demand to 64 distinct pending
  entries and 12 enqueue attempts per account per minute. Duplicate reads
  share one request and the API has a two-second cache-operation bound.
- The scheduler processes one job at a time under a five-second deadline.
  It checks exact authority before each actual attempt and before publishing.
  Successful cache lifetimes are at most 120 seconds for 1D or 600 seconds
  otherwise, further bounded by evidence retention and permission expiry.
- Alpaca history can use at most four attempts per minute and reserves at
  least half of the lowest applicable account ceiling for existing work.
  Kraken history can use at most six requests per minute and one per second,
  subject to lower aggregate IP and per-pair headroom. The ticker callback
  observes actual retries and fallback without waiting on history Redis.

## Tasks and verification

| Task | Commit | Result |
|---|---|---|
| Read or queue authenticated history | `819648b` | Six API cases passed with real disposable PostgreSQL and Redis. |
| Consume bounded display jobs | `d5a0e37` | Thirteen scheduler cases passed with the same guarded datastores and fixture HTTP. |

The focused cases exercise anonymous access, CSRF, exact listing versions,
queue deduplication and capacity, expiry, optional configuration, cache
outage, authenticated publication, normalized decimal closes, source budget
limits, and mapping or calendar changes during an upstream attempt. A cached
chart publication preserved the existing BTC quote and trade count. Ruff
passed on changed Python files, mypy passed all 145 app source files, and
both Compose entry points parsed with synthetic settings.

## Deviations from Plan

- The default-off `MARKET_HISTORY_SCOPE_JSON` setting needed explicit
  passthrough to both API and scheduler in the existing development and
  production Compose allowlists.
- The worker shares the existing Alpaca ceiling calculation and lets the
  existing ticker transport record its actual attempts. These adaptations
  keep chart reservation out of current price and order logic.

## Open provider qualification

The operator setting is unset. Live history rights, representative coverage
and actual provider ceilings remain open, so CHART-04 retains its live gate.
No live upstream calls were made. [Source qualification](23-SOURCE-QUALIFICATION.md)

## Self-Check: PASSED
