---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "02"
subsystem: api
tags: [history, fastapi, postgresql, pagination]
requires: []
provides:
  - Server-filtered private mixed History before bounded seek and hydration
  - Backwards-compatible v3 continuation and query-bound filtered v4 continuation
affects: [25-04, 25-05]
tech-stack:
  added: []
  patterns: [typed-filter-pair, query-bound-cursor, owner-scoped-sql]
key-files:
  created: []
  modified:
    - backend/app/api/v2/history.py
    - backend/app/schemas/event_history.py
    - backend/app/services/event_history.py
    - backend/tests/test_event_history.py
    - backend/tests/test_event_history_api.py
    - backend/tests/test_event_history_cursor.py
    - backend/tests/test_stock_catalog_event_history.py
key-decisions:
  - "Filter the owned SQL sources before seek and limit, with the existing three-column tie order."
  - "Keep v3 for all/all and bind v4 to the exact active portfolio, activity and asset."
requirements-completed: [FLOW-02]
completed: 2026-11-26
---

# Phase 25 Plan 02 — Filter private mixed History

The mixed History endpoint accepts optional `activity` and `asset` values.
Defaults are `all` and `all`. The response preserves the existing event
schema, monetary strings and exact catalog identity. A filtered request
receives v4 continuations with both filter values. Mixed all/all continues
to use the original v3 encoding, and trade-only History retains v2.

Filters apply to owned sources before the descending recorded time, kind rank
and source ID seek. Dividend results include original payments and posted or
held decisions. Correction details carry the original payment across page
boundaries. The route returns a fixed private error for invalid filters.
Closed and foreign roots receive the existing unavailable response.

| Task | Result | Commit |
|---|---|---|
| 25-02-01 | Typed filters and bounded query-specific cursor validation | `c4ecc71` |
| 25-02-02 | Server filters and guarded service, API and exact catalog tests | `e7a9fe6` |

## Verification

- Task 1 cursor and schema suite passed 152 tests.
- The final seven-file guarded PostgreSQL/API suite passed 316 tests in
  210.86 seconds on the disposable stack. It checked exact catalog stock
  provenance, owned ties and pages, the older match skipped by an unfiltered
  first page, filtered correction lineage, invalid scope, retained v3 and
  legacy v2, and closed and foreign targets.
- The plan's three scoped modules reached 100% statement and branch coverage
  across 350 statements and 154 branches. The separate coverage report passed.
- Ruff lint and format checks passed. Mypy checked 149 source files.

## Deviations

Extended the existing exact catalog ticker-reuse fixture with a filtered
Sell/Stocks assertion. The filtered source predicates use SQLAlchemy's typed
true and false expressions. The final coverage replay ran on stable source.
The suite reported four existing Pandas deprecation warnings.

## Self-Check: PASSED

The two task commits are present. All scoped files and the exact static and
guarded test evidence were verified. The backend contract is ready for Plan
25-04.
