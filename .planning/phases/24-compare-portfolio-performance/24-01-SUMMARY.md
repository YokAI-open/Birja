---
phase: 24-compare-portfolio-performance
plan: "01"
subsystem: database
tags: [postgresql, alembic, portfolio, authorization]
requires:
  - phase: "21"
    provides: "Reviewed portfolio and catalog schema and restricted authority"
provides:
  - "Revision 0028 and its exact catalogue, migration source, and role grants"
  - "An owner-bound daily valuation relation and an active-root lock for the scheduler"
affects: [24-03, 24-04, 24-06, 24-07]
tech-stack:
  added: []
  patterns: [additive-migration, exact-schema-admission, append-only-runtime-grants]
key-files:
  created:
    - backend/alembic/versions/0028_portfolio_daily_values.py
    - backend/alembic/sql/0028_portfolio_daily_values.sql
    - backend/app/models/portfolio_daily_value.py
    - backend/tests/test_portfolio_daily_schema.py
  modified:
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/portfolio_migrate.py
    - backend/app/db/dev_bootstrap.py
    - backend/app/db/schema_contract.py
    - deploy/db/bootstrap-roles.sql
key-decisions:
  - "Use the existing private migration and explicit role bootstrap sequence for 0028."
  - "Give the scheduler column-scoped insert and conflict-key reads with the active-root lock."
patterns-established:
  - "The insert guard holds the matching open portfolio's shared root lock through the caller transaction."
requirements-completed: [TREND-03]
duration: 11min
completed: 2026-11-26
---

# Phase 24 Plan 01 — Daily value schema

Revision 0028 adds one owner-bound observation per active portfolio and UTC
day. The root lock and insert trigger serialize capture with portfolio closure.
The schema accepts exact complete totals and separate incomplete observations.

## Tasks

| Task | Commit | Verification |
|---|---|---|
| Add the reviewed relation and active-root lock | `7fd96a3` | Two real PostgreSQL scratch tests verified populated 0027 preservation, empty downgrade, populated downgrade refusal and observation constraints. |
| Admit and authorize the exact 0028 schema | `f9bc9e1` | Eight selected PostgreSQL checks passed, including fresh and populated migration, authenticated runtime roles, exact grants, metadata agreement and 0027 consumer compatibility. |

The existing administrative role bootstrap script ran against the guarded
local PostgreSQL test container and matched the reviewed 0028 grants.
Ruff lint and format checks passed on nine affected Python files. Mypy passed
on all 146 app source files.

## Integration contract

- `portfolio_daily_values` uses `(portfolio_id, user_id)` ownership and a
  unique `(portfolio_id, utc_day)` constraint. The 22:00–24:00 UTC range and
  complete/null amount semantics are checked in PostgreSQL.
- `public.lock_portfolio_daily_value_root(bigint,bigint)` takes owner and
  portfolio in that order. The scheduler holds its transaction through
  insertion. The trigger also checks the exact active root on direct insert.
- The scheduler may select `portfolio_id` and `utc_day` for discovery and
  conflict handling. Use `RETURNING portfolio_id` when needed and keep reads
  of monetary history on the app role.
- Bind capture and the private history read to
  `require_schema(..., consumer="portfolio_daily")`. The ordinary portfolio
  consumer still admits its reviewed predecessors.
- The 0028 catalogue and ACL digests are pinned in the bootstrap and mirrored
  in the SQL admin entry point. Capture, UI and encrypted recovery evidence
  remain part of the subsequent Phase 24 plans.

## Decisions and deviations

The migration creates the table and routines privately. The explicit role
bootstrap grants read and append privileges after exact schema admission.
That follows the existing migration sequence and preserves the recognized
fresh and upgraded grant states. Role tests exercise the migrated and
bootstrapped states separately.

The tests use individually named scratch databases created on the guarded
local PostgreSQL test server. The scratch roles are authenticated and the
databases are removed in fixture cleanup. Synthetic data verifies the UTC
window, duplicate handling, exact prior values and terminal-write refusal.

## Self-Check: PASSED

Verified task commits, migration payload, model, scoped grants and tests in
the milestone worktree.
