---
phase: 02-authentication
plan: 03
subsystem: auth
tags: [postgres, alembic, sqlalchemy, accounts, verify-code]
requires:
  - phase: 02-authentication
    provides: OtpStore, CSRF dependency, test fixtures (02-02)
provides:
  - users and accounts tables (migration 0002) with named CHECK/UNIQUE constraints
  - get_or_create_user (ON CONFLICT DO NOTHING) granting 10000.00 exactly once
  - POST /api/v1/auth/verify-code returning {email, cash_usd}
affects: [02-04, 02-07]
key-files:
  created: [backend/app/models/__init__.py, backend/app/models/user.py, backend/alembic/versions/0002_users_and_accounts.py, backend/app/services/accounts.py, backend/tests/test_accounts.py, backend/tests/test_auth_verify.py]
  modified: [backend/alembic/env.py, backend/app/services/auth.py, backend/app/schemas/auth.py, backend/app/api/v1/auth.py, backend/tests/conftest.py, backend/tests/helpers.py, backend/tests/test_migrations.py, backend/tests/test_auth_request_code.py]
key-decisions:
  - "Route allow-list test reads app.openapi() paths because this FastAPI version includes routers lazily (app.routes has no path for them)"
  - "migrated fixture is a sync session fixture (alembic upgrade head) that running_app depends on"
requirements-completed: []
duration: 25min
completed: 2026-10-27
---

# Phase 2 Plan 03: verify-code and the $10,000 account Summary

A user who got a code can sign in: the first success creates one user and one $10,000.00 account, enforced by Postgres constraints and an ON CONFLICT insert.

## Tasks

| Task | Result | Commit |
|------|--------|--------|
| 1 users + accounts schema, migration 0002, get_or_create_user | Hand-reviewed autogenerate (all 4 named CHECKs, identity PKs, working downgrade); 10-way concurrency test gives 1 user, 1 account | 90df75e |
| 2 POST /auth/verify-code | Single invalid_code 400 for all failures; cash_usd as string; allow-list and enumeration tests | e797c9d |

## Verification

- Backend suite: 64 passed, coverage 98.9% (branch); otp/auth/accounts/security 100%; ruff, format, mypy clean.
- Test stack torn down with `down -v`.

## Deviations from Plan

- Autogenerate output already contained all four CHECK constraints; only comment markers removed and ruff-formatted.
- The acceptance step inspecting `\d accounts` on a rebuilt dev stack was not run (no local `.env`, D-02); the same constraints are verified by the test-stack tests and the model/schema drift test.
- Route allow-list uses OpenAPI paths instead of `app.routes` (see key-decisions).
- test_accounts.py's sign-in and allow-list cases were added in the Task 2 commit since they need the endpoint.

## Known Stubs

None.

## Self-Check: PASSED

- Files present, commit 90df75e and e797c9d exist, suite green.
