---
phase: 24-compare-portfolio-performance
plan: "03"
subsystem: database
tags: [postgresql, alembic, portfolio, catalog, regression]
requires:
  - phase: 24-01
    provides: "Revision 0028 and reviewed schema and role grants"
provides:
  - "Fresh and upgraded 0028 verification with retained predecessor cases"
  - "Existing portfolio and catalog workflows verified on 0028"
affects: [24-04, 24-06, 24-08]
tech-stack:
  added: []
  patterns: [moving-head-fixtures, explicit-predecessor-admission]
key-files:
  created: []
  modified:
    - backend/tests/test_dev_bootstrap.py
    - backend/tests/test_portfolio_migrate.py
    - backend/tests/test_portfolio_schema_admission.py
    - deploy/tests/test-dev-bootstrap.py
    - backend/tests/test_portfolio_closure_critical.py
    - backend/tests/test_portfolio_dividend_authority.py
    - backend/tests/test_portfolio_dividends.py
    - backend/tests/test_portfolio_splits.py
    - backend/tests/test_portfolio_strategy_lifecycle.py
    - backend/app/tasks/stock_catalog_import.py
key-decisions:
  - "Exercise 0028 alongside 0027 in the real restricted migrator successor matrix."
  - "Extend the explicit catalog import revision admission to 0028 in both existing modes."
requirements-completed: [TREND-03]
duration: 29min
completed: 2026-11-26
---

# Phase 24 Plan 03 — Migration and finance baseline

Fresh and upgraded 0028 databases preserve existing cash and starting cash,
catalog operations, terminal portfolio closure, dividends and splits. The
restricted migrator test exercises 0027 and 0028 alongside earlier revisions.

## Tasks

| Task | Commit | Verification |
|---|---|---|
| Qualify current-head migration and schema fixtures | `4a36bba` | 242 guarded PostgreSQL tests passed in 18m19s. The disposable Docker fresh and upgrade bootstrap lanes also passed. |
| Preserve protected finance and lifecycle behavior | `1c535b6` | 101 guarded tests passed in 9m08s, including the existing catalog publication and restricted operator rehearsals. |

The migration run included `test_portfolio_daily_schema.py`, `test_migrations.py`,
`test_dev_bootstrap.py`, `test_portfolio_migrate.py` and
`test_portfolio_schema_admission.py`. Its module-entrypoint test reported one
Python `runpy` warning. All tests passed. The finance run included the five
files specified in the plan and `test_stock_catalog_publish.py`. Ruff lint and
format checks passed on the nine affected backend files. Mypy passed on the
catalog import module.

The Docker proof used the locked test-builder image
`birja-backend-test:phase24-fixtures`. It checked the exact reference cash
and baseline values, retained catalogue admission on 0025, restricted role
refusals, and repeat grant application. The harness reported removal of
its owned containers, networks and volumes.
[Docker bootstrap log](/tmp/birja-phase24-dev-bootstrap.log)

## Deviations from plan

**[Rule 3 — Compatibility blocker]** Catalog import used finite revision
lists that ended at 0027. The task added explicit 0028 admission to both
existing modes in `backend/app/tasks/stock_catalog_import.py`. The older
entries remain supported, and the existing operator and disposable manifest
tests passed with the new head. The change shares the Task 2 commit.

## Self-Check: PASSED

Verified both task commits, scoped changes and observed test results. The
orchestrator owns shared roadmap and state updates.
