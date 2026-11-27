---
phase: 24-compare-portfolio-performance
plan: "04"
subsystem: portfolio
tags: [postgresql, scheduler, fastapi, exact-money]
requires:
  - phase: 24-03
    provides: "Qualified 0028 schema with 0027 portfolio and catalog compatibility"
provides:
  - "Private daily capture using exact current valuation and the active portfolio lock"
  - "One authenticated 30-day value-history response for the owner's active portfolios"
affects: [24-05, 24-06, 24-07, 24-08]
tech-stack:
  added: []
  patterns: [active-root-fence, append-only-observations, bounded-keyset-scan]
key-files:
  created:
    - backend/app/services/portfolio_daily_values.py
    - backend/app/tasks/portfolio_daily_values.py
    - backend/app/schemas/portfolio_daily_values.py
    - backend/tests/test_portfolio_daily_capture.py
    - backend/tests/test_portfolio_daily_api.py
  modified:
    - backend/app/core/config.py
    - backend/app/services/portfolio.py
    - backend/app/services/stock_eligibility.py
    - backend/app/services/stock_valuation.py
    - backend/app/tasks/scheduler.py
    - backend/app/api/v2/portfolios.py
    - backend/tests/test_scheduler_loop.py
    - docker-compose.yml
    - docker-compose.prod.yml
    - .env.example
key-decisions:
  - "Share valuation thresholds between the API and scheduler and retain the ordinary statement's final ownership fence."
  - "Keep the scheduler on its exact root authority and its existing column grants."
  - "Use only current marks with applicable derived, durable storage and backup rights. Retain no market quotes in daily rows."
requirements-completed: [TREND-02, TREND-03]
duration: 22min
completed: 2026-11-26
---

# Phase 24 Plan 04 — Daily capture and private history

The scheduler runs one bounded capture callback per minute on admitted 0028
between 22:00 and 24:00 UTC. Each transaction holds the exact active portfolio
root through its first daily append and uses the existing Decimal valuation
with the original eight-decimal starting cash. Restart and retries preserve
both complete and incomplete observations. There is no historical backfill.

| Task | Commit |
|---|---|
| Capture exact daily values and serialize with terminal closure | `2dc937d` |
| Schedule with schema admission, common thresholds and bounded retries | `13f3f0d` |
| Serve the private bounded exact history batch | `0e43494` |

The scheduler reads only the portfolio/date conflict key from daily storage.
Its cursor advances after each attempt, including rollback and lock timeout.
It processes up to eight roots per tick within a 20-second tick budget and a
two-second budget per root. Dev and prod Compose enable it by default and can
override it with `PORTFOLIO_DAILY_CAPTURE_ENABLED`.
The bare scheduler setting defaults to disabled. Startup on an unavailable or
earlier schema leaves the existing callbacks running.

`GET /api/v2/portfolios/value-history` uses the signed-in owner's active
portfolio roots and returns `start_day`, `end_day`, and `portfolios`. Each
series contains `portfolio_id` and `points`. Each point has `utc_day`,
`captured_at`, `total_value`, and `valuation_complete`. IDs and money are exact
strings, and timestamps are UTC. The window is inclusive with at most 30 dates
and ten portfolios. Absent days are omitted, incomplete points have null
totals, and portfolios with no history have empty points. A final root fence
rejects a close in flight. `ManagementRoute` supplies private no-store behavior
on success and failure. The ordinary 0027 endpoints retain their admission.

## Current-mark permissions

Curated stock marks already require derived use, durable accounting and
backup/restore in the exact original quote and current authority. Catalog
marks require derivation, storage and backup for each mark field under the
listing-specific current grant. Either scope can explicitly exclude the durable
aggregate or its backup using `durable_derived_use` or `durable_derived_backup`.
That portfolio records an incomplete daily observation while the ordinary
statement continues applying its existing mark rules. Raw quote retention still
limits eligibility at capture time. The new relation contains only the exact
portfolio aggregate, its baseline and the observation metadata. All replay
permissions and input prices came from synthetic local fixtures.

## Verification

- All 16 daily capture tests passed on guarded PostgreSQL. They covered both
  closure orders, owner isolation, complete and incomplete conflict handling,
  cash-only values, exact starting cash, featured and catalog stock marks mixed
  with crypto, denied and restricted mark scopes, and UTC rollover before an
  append. The synthetic catalog fixture reported four Pandas warnings.
- All three private API tests passed. They checked owner isolation, exact
  strings, UTC bounds, close-in-flight refusal and ordinary 0027 endpoints
  during trend refusal.
- All 28 scheduler-loop tests passed. The successor and predecessor tests used
  real isolated schema admission. Daily capture tests also exercised bounded
  scans, rollback, lock timeout, duplicates and UTC restart.
- The initial 33-test run passed the current statement snapshot and price
  settings regressions alongside the core capture cases.
- Ruff lint and format checks passed on affected Python files. Mypy passed on
  all 149 app modules. A consolidated branch-coverage attempt was interrupted
  with exit 143 before its report. Plan 24-08 owns the full coverage receipt.

## Deviations from Plan

**[Rule 3 — Type compatibility]** The existing stock authority projection was
typed for HTTP settings though it uses the shared stock account and server
scope. Its annotation now accepts `MarketValuationSettings`, also supplied by
the scheduler. The projection logic and its callers' grants are unchanged.

The current catalog valuation fixtures start on literal 0026. The daily
aggregate tests migrate those synthetic rows to 0028 and apply the reviewed
grants before capture, preserving the retained fixtures for their existing
tests. The exact baseline fixture uses cent-precision cash as required by the
account constraint and independently checks the original eight-decimal baseline.

Positive and restricted catalog fixtures caught a dropped scope decision when
the catalog mark's validity deadline was replaced. Task 1 preserves that
decision through the deadline check. Task 2's real scheduler-role scan found
that the SQL existence check must project the granted conflict key explicitly.
The query now reads only those granted columns.

## Self-Check: PASSED

Verified all three task commits, exact staged paths, the active-root schema
interface and each changed-feature test receipt. The phase orchestrator owns
shared state and roadmap updates.
