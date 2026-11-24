---
phase: 20-trade-and-value-stocks-from-search
plan: "03"
subsystem: database
tags: [postgresql, alembic, schema-admission, catalog]
requires:
  - phase: 20-02
    provides: Pinned 0026 schema and financial routines
provides:
  - Current 0026 application and migration admission
  - Explicit retained 0025 admission with its original grants
affects: [20-04, 20-05, 20-06, 20-07, 20-09]
requirements-addressed: [SL-01, SL-03, SL-04]
requirements-completed: []
---

# Phase 20 Plan 03 Summary

The current runtime admits revision `0026`. The explicit `retained0025` consumer checks the original `0025` schema and grants. Both Alembic assets for `0025` retain their original bytes.

## Database authority

- The app reads scoped market facts and can insert immutable fill evidence. The scheduler can write normalized quotes, status and action coverage. Binding and admission changes use the enrolled migrator. Runtime admission reads only the approved column projection of catalog permissions.
- The existing role-specific operator routine remains callable with `birja_action_operator`. The runtime roles receive no new operator privileges.
- Dev bootstrap and the finite authenticated migration command check the exact current target. The disposable image harness stages `0024` and `0025`, verifies retained admission, then migrates to `0026`.

Fresh and upgraded databases on the same pinned PostgreSQL image agreed on the `0026` catalogue SHA-256 `0c855fb80619ed1cd46183b87c3357a9183b3592d4504ebce8c722fb61085cc6`, post-grant ACL SHA-256 `6995ecd9a65d5bf659480b524e37e236c31a293cb2ab9f1648ea657c15842994`, and private-default ACL SHA-256 `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`. Preflight passed under the restricted app and scheduler roles.

## Verification

- The app started with the actual app-role credentials and returned health HTTP 200. The restricted scheduler accepted 15 fixture prices in one cycle. The local production bootstrap SQL passed on fresh 0026 and on a 0025-to-0026 upgrade. An empty downgrade returned to the original 0025 contract.
- 116 distinct backend tests passed across the initial run and its targeted continuation. They cover authenticated migration, exact retained admission, the populated upgrade's unchanged ledger, allowed and refused grants, the app-role catalog finalizer, the operator ACL, and existing mixed trade, dividend and split behavior. The first run exposed a fixture setup error resolved by using the enrolled migrator for the ledger seed. Four pandas deprecation warnings remain.
- Ruff, formatting, mypy, compilation and diff checks passed. All six embedded deployment harness diagnostics compile, and its focused current/retained contract passed. The broader static deployment suite passed 42 of 43 checks. Its outstanding recovery source-profile check and the image-based integration run are covered by Plan 09.
