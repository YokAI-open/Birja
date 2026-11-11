---
phase: 08-corporate-action-safe-ownership
plan: "01"
subsystem: database
tags: [postgresql, alembic, accounting, privileges, stock-quotes]
requires:
  - phase: 07-permitted-stock-discovery
    provides: "Reviewed0010 catalogue, admission and monotonic quote storage"
provides:
  - "Nine constrained durable action/ownership tables in additive0011"
  - "Epoch-zero quote compatibility with final-statement nonzero refusal"
  - "Restricted append/quantity privileges and NOLOGIN operator prerequisite"
affects: [08-02, 08-05, 08-06, 08-08, 08-09]
tech-stack:
  added: []
  patterns: [deferred-current-revision, append-only-runtime-grants, explicit-local-quote-units]
key-files:
  created:
    - backend/alembic/versions/0011_stock_action_accounting.py
    - backend/app/models/corporate_action.py
    - backend/tests/test_stock_action_migrations.py
  modified:
    - backend/app/models/stock.py
    - backend/app/models/trade.py
    - backend/app/models/__init__.py
    - backend/app/services/stock_quotes.py
    - backend/tests/test_stock_quotes.py
    - backend/tests/test_migrations.py
    - deploy/db/bootstrap-roles.sql
key-decisions:
  - "A restricted migrator never gains CREATEROLE: privileged bootstrap preprovisions the NOLOGIN operator before0011."
  - "Provider validation never supplies unit epochs; the legacy writer assigns local zero and refuses committed nonzero state or stored units."
  - "No full requirement checkbox is completed by schema infrastructure alone; final phase verification remains necessary."
requirements-completed: []
requirements-addressed: [DIV-01, DIV-02, ACT-01, ACT-02, ACT-03]
duration: 18 min
completed: 2026-11-11
---

# Phase 8 Plan 01: Durable Action Accounting Summary

**Additive0011 preserves legacy financial rows while constraining economic identities, whole-share movements, entitlement lineage and restricted runtime writes.**

## Performance

- Duration: approximately18minutes, 2026-11-11, completed10:36UTC.
- Tasks:2/2; source/test/SQL files:9.
- No dependency installation, private provider request or production operation.

## Accomplishments

- Nine typed models enforce bounded normalized evidence, finite whole quantities, exact cents basis, economic/causal uniqueness, source/revision correspondence and safe epoch bounds. Deferred event pointers support insertion ordering without cross-event revision assignment. Split applications are unique by economic event; corrections cannot acquire another application through a new revision. Entitlement supersession stays within the same event/user.
- Existing quote insert/newer/equal/older behavior remains exact with explicit validated-field mapping and local unit_epoch0. INSERT SELECT checks committed nonzero action state; conflict updates cannot reset an already nonzero stored quote. Actual pre-statement committed state tests pass for both insert and update. Complete gate-bound split/write serialization remains08-09.
- Runtime roles cannot rewrite/delete immutable accounting or mutate operator resolutions/admissions. Scheduler receives holdings SELECT/UPDATE(quantity), immutable append/identity usage and limited current-pointer/state mutation. Operator is NOLOGIN, noninheriting, nonprivileged and has no runtime membership or write grant.
- Populated0010 financial snapshots survive upgrade and empty downgrade exactly. Any durable event/accounting or stock financial reference refuses downgrade before alteration. Existing0009/0010 files are unchanged.

## Task Commits and TDD Gates

1. Task08-01-01 RED `a0ba4eb`: real migrated PostgreSQL assertion failed because nine durable accounting relations were absent, not because an import failed.
2. Task08-01-01 GREEN `ddba730`: generated/reviewed0011, typed models, explicit quote mapping and constrained unit writes;75targeted tests passed6.12s before task commit.
3. Task08-01-02 RED `96eb57e`: actual upgraded-role assertion failed because quantity-only scheduler UPDATE was absent.
4. Task08-01-02 GREEN `6282251`: conditional migration grants, fresh-bootstrap parity and actual SQLSTATE42501 checks.

Both behavioral tasks have observed RED before implementation and GREEN commits in order.

## Verification Executed

- `docker compose -f docker-compose.test.yml up -d --wait`: existing isolated tmpfs PostgreSQL/Redis healthy; no new production/dev resources. Project birja-test; containers birja-test-postgres-1 and birja-test-redis-1; loopback ports55432/56379; test-only credentials. Left running for following plans.
- Actual `alembic revision --autogenerate --rev-id 0011 -m stock_action_accounting`, using synthetic ENV=test/DATABASE_URL/REDIS_URL and dummy signing secrets, against isolated0010. Reviewed the whole draft, added omitted existing-table CHECK, explicit delayed circular FK, stronger economic/FK constraints, empty-only guard and conditional grants. No metadata.create_all shortcut.
- `uv run pytest tests/test_stock_action_migrations.py tests/test_stock_quotes.py tests/test_migrations.py -q -x`: **79passed7.45s** final run. Includes actual metadata/migration equality, upgrade/downgrade, legacy identity/money snapshots, nonfinite/fractional/overflow rejection, duplicate economic/revision/mutation/entitlement/causal/sequence refusal and quote-unit checks.
- `uv run pytest tests/test_stock_action_migrations.py -k grants -q -x`: **4passed1.85s**. Actual restricted-role table/sequence statements return42501; scheduler append and identity operations succeed. Fresh bootstrap executes in an isolated transaction and rolls back owner/password changes; exact9table/3role/7privilege matrix matches upgrade. Detailed column/sequence denials are separately executed. This is not yet retained-tool or restricted-login TLS proof, assigned08-02.
- Scoped Ruff check and format checks: **8files pass**. `uv run mypy app/models/corporate_action.py app/models/stock.py app/models/__init__.py app/services/stock_quotes.py`: **4source files pass**.
- `git diff --check` passes. Stub/threat scan found no TODO/FIXME/placeholder or new endpoint/credential path. New schema/authority boundary is covered by T-08-01-01/02; no unplanned security surface.

Reviewed predecessor SHA256:

| Revision | SHA256 |
| --- | --- |
|0009|9a9510aff3bb616398a239c2d1eec4a81964ad733c7746ed09f122a6992240fa|
|0010|f231c3b62213a0f033a463833ef4cdf6a0b8cb5ee62a20680d1111dc11ad992c|
|0011 initial implementation, superseded by review fixes below|f6700d5b02741b2ac201749ff807dc7744fa4a461331556875649be8273f4be4|

API/SQL reference checks: [SQLAlchemy2.0 constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html), [PostgreSQL18 GRANT](https://www.postgresql.org/docs/current/sql-grant.html).

## Decisions and Operational Prerequisites

`birja_migrator` is intentionally NOCREATEROLE. Bootstrap can prepare the NOLOGIN operator on predecessor schemas; a restricted0011 upgrade without that role raises an explicit prerequisite error. It never grants the migrator administrative authority. Plan08-02 must include this privileged preparation before its restricted TLS upgrade proof. No login is provisioned here.

The metadata requirement-ID list records this plan's assigned coverage, not complete end-to-end DIV/ACT acceptance. REQUIREMENTS.md remains unchecked pending the rest of Phase8.

## Deviations from Plan

**[Rule1 — Compatibility] Update existing migration head assertion.** Adding0011 invalidated tests/test_migrations.py's hardcoded0010. Updated only EXPECTED_HEAD to0011 in `ddba730`; real baseline/roundtrip/schema comparison pass. No unrelated fixture/admission edits.

## Issues Encountered

Permission-test drafts initially attempted an identity-column UPDATE (PostgreSQL rejects identity assignment before authorization) and superuser-session SET ROLE (session superuser remains authorized). Corrected tests to nonidentity immutable fields and catalogue membership assertions. One allowed-append test accidentally committed its synthetic event; the next downgrade correctly refused. Removed only that synthetic fixture and changed the test to explicit rollback. All final tests pass and runtime roles/test fixtures are cleaned. These were verification-harness corrections, not waived product failures.

## Remaining Gates

Ready for08-03 in Wave1 and08-02 exact recovery/TLS integration. No corporate-action processing, stock execution, cash payments, live activation or public History is enabled. Phase7's scheduled one-shot and owner-deferred live acceptance are untouched. Full-phase coverage/audits/image gates, financial concurrency, owner UI and external activation stay assigned to later plans. Nothing pushed/deployed.

## Self-Check: PASSED

All created source/test files exist; four task commits are present; final targeted tests and static checks pass; predecessor files remain unchanged. No required implementation stub remains in this plan.

## Focused Independent Review Corrections

The independent08-01 review found two blockers in the initial implementation:
same-event verified aliases could not observe their original economic revision,
and ownership cause FKs did not bind owner/instrument or split-result units.
These findings supersede the initial invariant claims for those exact boundaries.

Observed behavioral RED `0abc846` demonstrated three genuine failures: a valid
same-event alias was rejected by the originating-source FK, and forged cross-user
and cross-instrument fill causes were accepted. GREEN `5d0353a` implements:

- `stock_action_observations.event_id` with indexed FK and composite
  `(source_id,event_id)` / `(revision_id,event_id)` references. A verified alias
  observes the original revision without rewriting its originating source,
  duplicating the fingerprint or losing scoped mutation uniqueness. Cross-event
  source and revision references are refused by PostgreSQL.
- `stock_split_applications.coin_id`, indexed and tied to the event's instrument,
  plus unique `(id,coin_id,new_unit_epoch)`. Ownership split causes reference
  `(application_id,coin_id,unit_epoch)`; wrong instrument or resulting epoch fails.
- Existing `trades` gain unique `(id,coin_id,user_id)` using a concurrently built
  index attached as `uq_trades_id_coin_user`. Ownership fill causes reference
  `(trade_id,coin_id,user_id)`. No existing financial row is rewritten. The
  legacy history-index test compares its original financial constraints while
  the complete current metadata/schema comparison verifies the new causal key.

The unmerged local0011 was amended only after safely downgrading the empty
isolated ledger to0010. No durable record was removed to downgrade. No function,
trigger, SECURITY DEFINER or runtime privilege widening was needed. Actual
matching fill/split movement INSERTs succeed under app/scheduler grants, while
scheduler SELECT on trades still fails42501. Operator preprovisioning remains
required before restricted0011 migration.

Final corrected proof: **88targeted tests pass8.14s**, including alias/adversarial
causal cases, actual roles, quote persistence, preserved legacy snapshots and
complete ORM/migration parity. Scoped Ruff/format5files and mypy2models pass;
git diff --check passes. All test fixtures roll back and isolated runtime-role
fixtures clean up. The birja-test stack remains available for next plans.

Frozen source identities after corrections:

| File | SHA256 |
| --- | --- |
|0011_stock_action_accounting.py|4a5e5a9a29198096e6cd47ea126f9cca4fd88ca050c8d952f73c82d02f62e6eb|
|corporate_action.py|84d5129e7e57811008f494c5231123b4ce1264f86910177f5c5cb27a8b0fc6fb|
|trade.py|5211c0b884c58537a467c4d51e42b47534b5a0431514649ae07e33f92f7842f2|

Plan02 canonical recovery must include both new fields, new composite constraints
and the existing-trades composite unique index. Independent re-review is
**pending**; executor verification does not declare the review clean. Requirements
remain addressed, not completed. No03 sources, provider access, production,
scheduled process or publication changed.

Review-fix self-check: both RED/GREEN commits and all revised files exist;
reported final tests/static checks were actually executed and passed.
