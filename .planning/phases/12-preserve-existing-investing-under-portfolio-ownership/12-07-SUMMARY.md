---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "07"
subsystem: database
tags: [postgresql, alembic, portfolio, authorization, preservation, schema-admission]
requires:
  - phase: 12-04
    provides: authenticated migration-only expansion and immutable legacy association
  - phase: 12-05
    provides: static stock SQL companion and collected final authority scenarios
  - phase: 12-06
    provides: static dividend SQL companion and collected final authority scenarios
provides:
  - Actual final0017 paired ownership constraints, concurrent indexes and closed-root financial guards
  - Installed checksum-bound stock/dividend authority with finite association exceptions removed
  - Explicit startup and request-write schema admission and retained-consumer refusal contracts
affects: [12-08, 12-10, 12-11, 12-12, 12-13, 12-16, 12-17, 12-18, 12-27]
tech-stack:
  added: []
  patterns: [concurrent candidate-key preparation, trigger-only active-root lock, source-bound schema admission]
key-files:
  created:
    - backend/alembic/versions/0017_portfolio_ownership.py
    - backend/app/db/schema_contract.py
    - backend/tests/test_portfolio_schema_admission.py
  modified:
    - backend/app/main.py
    - backend/tests/test_portfolio_migrations.py
    - backend/tests/test_migrations.py
    - backend/tests/test_portfolio_stock_authority.py
key-decisions:
  - Keep immutable global split applications outside portfolio association; retain nullable legacy digest markers
  - Serialize each owned financial INSERT and holding mutation against the exact root without granting scheduler cash UPDATE
  - Require0017 for current startup/write admission; classify0015/16 explicitly as migration_only
  - Retained source/schema consumer contracts remain separate from deployment and recovery qualification
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-02, PSAFE-03]
duration: 26 min
completed: 2026-11-16
---

# Phase 12 Plan 07: Final Schema Closure and Explicit Revision Admission

**Real0017 installs paired financial lineage and immutable authority, closes migration exceptions, and refuses unsafe runtime schemas before startup or writes.**

## Accomplishments

- Actual authenticated migrations validate all seven owned-table associations,
  enforce required roots and complete owner/event/coin/revision/predecessor FKs,
  retain user-global retry uniqueness and replace obsolete user-only holding,
  split-effect and dividend-payment uniqueness. Account user-only uniqueness is
  removed last, after final authority and constraints exist. No public portfolio
  management routine or funding grant is introduced.
- All new lookup and candidate-key indexes on populated tables are prepared
  concurrently under explicit autocommit. Candidate keys attach through UNIQUE
  USING INDEX. Fixed definition/table/owner/live/attachment checks reject
  incompatible remnants; invalid compatible concurrent remnants can be rebuilt.
  Account and holding user lookup indexes retain coverage after legacy unique
  keys are removed. Final actual model/schema parity is exact.
- Finite association triggers and associate_legacy_portfolio_only() are removed.
  Immutable owned records regain unconditional mutation refusal. Global split
  applications remain global, retain their original IDs/digests/NULL markers,
  and keep unconditional UPDATE/DELETE refusal. New applications require
  explicit SMALLINT2 through the installed stock digest guard.
- Both static SQL companions are read from fixed packaged Alembic paths and
  SHA256 checked before execution. Existing signatures, invoker/definer roles,
  quote/admission/session/time checks, independent arithmetic and final-business
  validation ordering remain intact. No old migration or asset bytes changed.
- A new trigger-only check_portfolio_financial_write() validates active roots
  on all seven owned INSERT paths and holding mutations, prevents root/holding
  reassignment, and preserves frozen account state. It locks the exact paired
  root FOR UPDATE. Its fixed body is SECURITY DEFINER, migration-owned, with
  search_path=pg_catalog,public,pg_temp and PUBLIC EXECUTE revoked. There are no
  caller arguments or useful normal SQL invocation; runtime roles gain no cash
  setter or lifecycle function. This avoids requiring scheduler cash privileges
  merely to serialize the active-root boundary.
- Existing broad app table UPDATE on accounts/holdings is narrowed to cash and
  quantity/cost_basis respectively. Financial read and INSERT/sequence grants
  are explicit; scheduler cash/accounting DML remains denied. Runtime role and
  schema-USAGE prerequisites are provisioned only by the guarded disposable test
  administrator, never by application migration role creation. The revision
  marker has SELECT only for runtime schema admission.
- Current startup and POST/PUT/PATCH/DELETE request admission require0017.
  Both0015 and0016 explicitly return the internal migration_only reason; other
  incompatible/unknown schemas refuse without repair or auto-migration. HTTP
  failures expose only a generic503. Retained0014 and retained0008 consumer
  contracts are explicit finite read-only lanes, not a generic compatibility
  bypass for current investing.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-07-01 | 23ecf13 | Final ownership migration and real SQL/preservation proofs |
| 12-07-01 correction | 9a8a9d6 | Concurrent index preparation and exact final metadata parity |
| 12-07-02 | 58a874a | Startup/write schema admission and twenty actual-revision cases |
| 12-07-02 correction | 1deec11 | Narrow revision SELECT and two restricted-role admission cases |

## Verification

Existing locked virtualenv only, with UV_CACHE_DIR=/tmp/birja-uv-cache and
uv run --no-sync. No installation, provider call or production operation.

| Check | Result |
|---|---|
| Actual retained0007–0014→0017 preservation/immutability plus inventory | 9 passed in59.88s on concurrent-index source |
| Fresh final inventory after user lookup/index and metadata grant fixes | 1 passed in5.41s |
| Four ownership/authority families, actual0017 test_final_sql_* | 66 passed in4.61s on final closeout source |
| Entire final schema-admission module | 22 passed in76.25s |
| Existing actual model/schema parity test | 1 passed in1.82s |
| Ruff check and format, seven touched files | PASS |
| Mypy schema_contract.py/main.py | PASS, two source files |
| git diff --check | PASS |

The retained-origin cases preserve unequal actual balances/baselines and a
genuine two-user global split, compare original economic/JSON/digest bytes, and
reject even migrator mutations after finalization. Final SQL cases now actually
execute the previously collected02/03/05/06 assertions: sibling holdings,
paired causal forgeries, retries, explicit digest markers, same-root split
effects, closed-root refusal, exact dividend/correction math and role denials.
Deferred constraints are forced in the assigned scenarios. No manual schema,
create_all, skip or xfail substitutes for Alembic0017.

Admission cases use actual staged/retained/final revisions, exercise the
independent HTTP write gate without startup, verify final startup, unchanged
snapshots on refusal, no automatic migration, and actual app/scheduler role
revision reads without UPDATE permission. These local connections are not the
verified-TLS/cold-recovery proof scheduled in16/18/27.

## Deviations from Plan

1. **[Rule2 — Missing critical functionality] General active-write guard.** The
   stock companion deliberately returned early for crypto, so the first real
   authority run exposed a closed-root crypto fill that was not refused. Added
   the narrow trigger-only root guard above instead of broadening role grants.
   Exact owner/config/EXECUTE inventory is tested and must be retained in ops.
2. **[Rule1 — Integration bugs] Complete root constraints and test probe.** The
   obsolete application/user split unique key blocked a valid sibling effect;
   removed it in0017. The stock immutability probe updated an ALWAYS identity
   column, producing428C9 before the intended permission/trigger check; it now
   targets unchanged cash_after and still requires23514/42501 refusal.
3. **[Rule3 — Isolated prerequisites] Guarded role/inventory adaptation.** Added
   exact new helper signatures and restricted disposable app/scheduler roles and
   schema-USAGE prerequisites to the existing test bootstrap. No production
   role-creation or authenticated migration predicate was weakened.
4. **[Rule2 — Project compliance] Concurrent final indexes and admission read.**
   Corrected initial ordinary index construction to the established concurrent
   pattern, added the two missing model-declared lookup indexes, and granted
   only SELECT on alembic_version for actual restricted runtime admission.

## Threat Flags

| Flag | File | Description |
|---|---|---|
| threat_flag: trigger_definer | backend/alembic/versions/0017_portfolio_ownership.py | New fixed-path private root-lock trigger; exact body/owner/search_path/ACL and trigger inventory must enter16/17 bootstrap/recovery manifests |

## Known Stubs

None. The final schema and assigned SQL/admission behavior are implemented and
tested. This is still a coordinated phase boundary, not a separately deployable
partial application release.

## Next Plan Readiness and Remaining Gates

- Ready for12-08 owned-active resolver and identity-only services. Current
  Account.id is portfolio_id; all financial rows require explicit roots. New
  service/API/browser consumers must use that contract; collection-only resolver
  cases outside final_sql still belong to their later implementation plans.
- Preserve check_portfolio_financial_write() as a trigger-only SECURITY DEFINER,
  check_stock_split_digest_version() as the private invoker, all portfolio_* and
  immutable triggers, nullable/no-default SMALLINT marker, concurrent index and
  full paired-constraint inventory in16/17 bootstrap/recovery authentication.
- Schema contracts are consumer admission primitives. Plan16 owns actual dev/
  retained tooling wiring and the safe migration-to-final operational route;
  17/18 own exact current/retained recovery consumers. Do not claim an existing
  retained deploy binary was modified or qualified by these module tests.
- Existing retained migration tests that use implicit head/down-to-base need
  explicit retained-source fixtures under the final full-suite integration;
  final0017 deliberately refuses downgrade before writes. The parity test is
  qualified now; unrelated old financial API/service tests are not represented
  as passing before their explicit-root plans are implemented.
- Full service/browser coverage, verified TLS, same-archive cold restore,
  security/image scans and both genuine owner UI/native200% checks remain
  pending. All28 milestone requirements remain unchecked. Phase7 deferred live
  outcomes and admissions are unchanged. No publication or production action.

## Self-Check: PASSED

All seven assigned/deviation paths exist; commits23ecf13/9a8a9d6/58a874a/1deec11
exist on feature/milestone-v1.2. No tracked files deleted, no new dependencies,
hidden routes or skipped authority assertions. Unrelated .claude/ untouched.
