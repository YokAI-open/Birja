---
phase: 13-create-and-compare-independent-strategies
plan: "03"
subsystem: database
tags: [postgresql, schema-admission, least-privilege, bootstrap, portfolios]
requires:
  - phase: 13-02
    provides: Immutable0020 management authority and once-only onboarding
provides:
  - Complete0020 current-source admission with exact catalogue and ACL validation
  - Finite authenticated forward migrator with pinned0015–0020 source assets
  - Separate unchanged retained0017 bootstrap literals and canonical0020 grants
  - Fresh/populated authenticated role negatives and actual production SQL proof
affects: [13-04, 13-05, 13-15, 13-17]
tech-stack:
  added: []
  patterns: [versioned catalogue contracts, canonical restricted regrants, authority-created fixtures]
key-files:
  created:
    - backend/tests/test_portfolio_management_admission.py
    - backend/tests/test_portfolio_management_grants.py
  modified:
    - backend/app/db/schema_contract.py
    - backend/app/db/portfolio_migrate.py
    - backend/app/db/dev_bootstrap.py
    - backend/app/db/portfolio_bootstrap.py
    - deploy/db/bootstrap-roles.sql
    - backend/tests/portfolio_fixtures.py
key-decisions:
  - "Current portfolio source admits only0020 and verifies source-owned catalogue plus exact ACL fingerprints before startup/write dispatch;0018/0019 remain migration-only."
  - "Retained0017 bootstrap SQL literals remain exactly equal to qualified4b4320b;0020 has a distinct fixed catalogue and privilege contract."
  - "Canonical0020 regrants reset table, column, sequence and routine ACLs before restoring narrow app/scheduler/operator rights; ordinary accounts INSERT and users UPDATE remain denied."
  - "All17 public signatures remain present: nine private validators/canonicalizers, four app entrypoints, three scheduler entrypoints and one operator entrypoint."
  - "Current preflight rejects every public rewrite rule, service database/schema ownership and effective runtime schema CREATE, including implicit pg_database_owner privileges."
requirements-completed: [PSAFE-07, PFUND-01, PFUND-02]
duration: 25min
completed: 2026-11-18
---

# Phase 13 Plan 03: Exact Schema and Grant Admission Summary

**Current0020 writes require the complete pinned catalogue and exact restricted grants, while fresh and upgraded bootstrap preserve financial authority and frozen0017 compatibility.**

## Performance

- **Original execution duration:** approximately17min,2026-11-18 08:18–08:35UTC; review repairs add approximately8min through08:47UTC
- **Tasks:**2/2
- **Implementation/test files:**8, plus this summary
- **Combined verification:**87passed in181.59s
- **Final focused verification:**4passed in11.11s after strengthening the operator NOLOGIN guard

## Accomplishments

- Current source admits only0020. Explicit retained0017/0014/0008 profiles retain finite older revision sets;0015/0016/0018/0019 refuse as migration-only. Malformed, duplicate, absent and unknown revisions refuse. An actual schema-contract module read from qualified4b4320b refuses0020 without writes.
- Admission now checks the immutable catalogue projection and exact ACL projection through the existing startup and write middleware. Incomplete columns/constraints/triggers, altered helper security/search paths, overloads, unsafe roles/schema CREATE, omitted execution grants and excess funding/provenance/users privileges refuse before request dispatch. Admission never repairs or grants anything.
- The forward migrator authenticates the genuine restricted session identity, accepts only supported0007–0020 revisions and enumerated source-owned relations/routine signatures, pins all ten migration/SQL assets and targets0020. Dev bootstrap preserves a distinct authenticated child, migration-only rejection and temporary migrator password lifecycle. Retained0017 requires explicit forward migration for current dev startup.
- The unchanged0017 `PREFLIGHT_0017_SQL` and `GRANTS_0017_SQL` are separate from current0020. An independent test reads qualified4b4320b and compares both complete literals for exact equality. No old manifest is recalculated from current HEAD.
-0020 catalogue hashing includes complete public routine definitions/owners, relation ownership, column types/defaults/identity/nullability, constraints/validation, indexes/readiness, trigger definitions/enabled state and identity-sequence definitions/dependencies. Sorted JSON projections exclude mutable rows, sequence positions and OIDs. Expected hashes are committed source constants, established on the approved immutable migration source and inspected against its named function/privilege inventories; runtime never learns or accepts a database-supplied expected hash.
- Canonical regrant clears table/column/sequence/routine privileges before restoring the intended source-owned inventory, including preserved operator reads/execution. App retains users SELECT/INSERT, ordinary financial cash/holding writes and exact entrypoint execution. Accounts INSERT/sequence access, metadata/baseline/closure writes, users UPDATE and all creation/latch table/sequence writes stay unavailable. Canonicalizers and trigger validators retain no non-owner EXECUTE. Scheduler cannot execute any management entrypoint. Operator stays NOLOGIN.
- Actual `deploy/db/bootstrap-roles.sql` runs through psql on both fresh and populated0020. Its preflight occurs before role/grant mutation, validates the same catalogue and finishes with the same exact ACL fingerprint. Disposable container discovery verifies the guarded published test port and Compose postgres label, rather than assuming a plan-specific container name.
- Shared portfolio-world fixtures create roots through actual0020 authority, preserve their independent cash/closed test states and add explicit zero-book legacy provenance. Legacy economic snapshots exclude only newly added metadata, including name_key; no money/history field is removed from the oracle.

## Task Commits

1. **Task1 RED:** `289d2db` — Specify current management schema admission; actual0017 incorrectly accepted,5 preceding negatives passed.
2. **Task1 GREEN:** `dc09b58` — Admit complete management schema and finite migrations;15passed in27.97s.
3. **Task2 RED:** `561459e` — Specify exact management bootstrap and restricted roles; actual fresh0020 preflight refused as old0017.
4. **Task2 GREEN:** `768ca91` — Pin complete management catalogue and least privilege grants; combined87 cases and final4 focused checks pass.

## Verification

From `backend/`, using the existing Python3.14 venv, stripped environment, fake prices and console email:

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_management_admission.py tests/test_portfolio_management_grants.py tests/test_portfolio_authority.py -x --tb=short`

**87passed in181.59s:**15 admission,61 management-grant and11 existing financial-authority cases. This includes fresh/populated restricted app/scheduler sessions, exact nine-private-helper inventory, immutable retained0017 literal equality, malformed revisions, genuine migrator identity, source tampering, financial preservation, direct forgery, overloads, schema CREATE, definition/constraint/trigger drift, missing/excess grants and actual production psql bootstrap.

The final operator NOLOGIN preflight guard was strengthened afterward, with no other implementation change. The following focused check then passed **4cases in11.11s**:two new fresh/upgraded operator-LOGIN refusal cases and two repeated actual production-bootstrap positive cases. The final grants inventory has63 cases; combined and focused runs together cover89 distinct cases, with two production positives repeated. A second complete89-case run after that narrow guard change is not claimed.

Seven changed Python files pass Ruff lint/format. All four changed DB modules pass mypy. `git diff --check` passes. A diff against prior Plan02 head shows no changes to any0015–0020 migration or0017/0019/0020 SQL asset. No file deletions occur in task commits. No stubs or unplanned trust surfaces were found.

PostgreSQL18 catalogue reconstruction and ACL inspection were checked against official [pg_proc](https://www.postgresql.org/docs/18/catalog-pg-proc.html) and [system-information](https://www.postgresql.org/docs/18/functions-info.html) documentation; Context7 tools/CLI were unavailable. No package was installed.

## Pinned Contract Handoff

- `CATALOGUE_0020_SHA256`: `d8f42ef33af7989badf342b5295d8d523cd6bf53839de6156a14e5251b5ee263`
- `ACL_0020_SHA256`: `041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`
- `schema_contract.py`: `99514087f755d1ccfb6f716acbe59bf4b859f83c6a4a2dbc3cdd1fabb7c8de28`
- `portfolio_migrate.py`: `8cd4f70fa37fa657b2d403983ed8765c2d73f47b52721af74f609c651eed4831`
- `portfolio_bootstrap.py`: `d7c432d0694a730c761488350a4678263e00912371c0ed6529f6f9a8ecee5f3b`
- `dev_bootstrap.py`: `56f25075dc298b6d34d56f56907e62e0e0f9189b2cfebbd1c6d47b4177e06e57`
- `deploy/db/bootstrap-roles.sql`: `a29b356bd0c6fe400838d0498a7fe68780009449ba5b233f32a48f707a2e3601`

All17 public signatures remain: the original ten plus the four0019 helpers and three0020 management entrypoints. The nine private/no-nonowner-EXECUTE signatures are `check_portfolio_financial_write()`, `check_stock_fill_integrity()`, `check_stock_split_digest_version()`, `reject_stock_dividend_mutation()`, `stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)`, `portfolio_display_name(text)`, `portfolio_name_key(text)`, `portfolio_description(text)` and `check_portfolio_management_metadata()`. App gets its prior execution assertion plus create/initialize/metadata; scheduler retains dividend apply/hold and root lock; operator retains action resolution. Temporary association helpers remain absent.

## Deviations from Plan

None. The final operator guard preserves the existing NOLOGIN role boundary. During test development, direct SELECT of a trigger-returning function hit asyncpg result-type introspection before a useful permission SQLSTATE; its privacy is instead asserted through the complete exact ACL inventory. The independent callable-helper refusal remains a real restricted-role SQL denial. No production authority repair or architectural change was needed.

## Qualification Limits and Next Plan Readiness

Ready for parent independent review, then13-04/05 source-bound recovery and rollback work. No full backend/coverage, encrypted recovery, verified TLS, browser, provider/live or whole-phase acceptance pass is claimed. Current revision safety fingerprints are available for those successor profiles; retained0017 recovery payload/constants remain unchanged.

Plan15 still owns the wider test/migration inventory updates. Existing `tests/conftest.py` and `tests/test_migrations.py` remain outside this plan's ownership: their ordinary head provisioning does not yet install the complete current bootstrap grants and their retained migration inventory still names0017. Later whole-suite qualification must use the genuine0020 restricted-role harness and preserve explicitly retained revision tests. In particular, an existing authority session can leave head installed; a separate new pytest process's retained provisioning then needs the guarded disposable schema lifecycle handled explicitly. This plan's focused commands reset only their owned throwaway schema and never weakened admission to accommodate those older fixtures.

Only owned `birja-p13-03` PostgreSQL/Redis resources ran, with existing cached pinned images and synthetic credentials. Exact project labels were checked before teardown; container, network and volume queries are empty afterward. No private.env, provider calls, dependency/lock/pin changes, production operations, push, merge or deployment occurred. Issue35's exact accepted policy/2026-12-17T00:00:00Z expiry and the approved Python image pin20261111 are unchanged. Unrelated `.claude/` remains untouched. Parent retains exclusive STATE/ROADMAP/REQUIREMENTS ownership; no global planning file was modified or staged.

## Self-Check: PASSED

All eight declared implementation/test paths exist. All four task commits exist with RED before GREEN for each task. Required focused evidence, static checks and immutable migration comparisons pass. Owned resources are removed; no unintended tracked file deletions or generated untracked files remain. Shared planning state is parent-owned.

## Independent Review Repair Addendum — 2026-11-18

The independent review of initial source7295c52 established two BLOCKER findings. Both were reproduced and repaired within Plan03's existing authority-admission boundary under Rule1/2 authorization. Parent owns the review report and independent re-review; this addendum does not claim that re-review has already passed.

- **CR-01 — Rewrite-rule authority drift:** An owner-installed ON INSERT rule on portfolio_creations could add cash without changing the original catalogue or ACL projections. The shared runtime/dev preflight and production preflight now reject every pg_rewrite row on a public relation, regardless of rule name, event or enabled state. The approved public inventory contains no rewrite rules, so there is no exception or new permitted rule profile. Real enabled and disabled versions of the reported cash-credit rule now refuse authenticated app admission, shared preflight and actual production psql bootstrap before any creation/grant mutation. Account counts/cash and empty creation journals remain unchanged. Hostile rules exist only in the guarded disposable schema and fixture-finally teardown removes them.
- **CR-02 — Implicit database-owner schema authority:** With public owned by pg_database_owner, a runtime database owner has effective schema CREATE through implicit membership. Shared and production preflight now reject app/scheduler/migrator/operator ownership of the current database or public schema and explicitly test effective has_schema_privilege(...,'public','CREATE') for both runtime roles. Tests temporarily assign the disposable database to app and scheduler, independently prove effective CREATE is true, and require authenticated admission/shared/production refusal. Explicit finally cleanup restores database/schema ownership. Valid birja_test administrative ownership and pg_database_owner schema ownership with an administrative database owner remain admitted.

**Repair commits:**

1. `d026a71` — RED: reproduce rewrite and implicit ownership admission gaps. All8 new fresh/upgraded negative cases failed because unsafe current admission incorrectly succeeded; no scaffold/mock substitutes for these PostgreSQL reproductions.
2. `5f5d087` — GREEN: reject rewrite and implicit ownership authority drift. Exactly12 matching guard lines are added to shared and production preflight. Frozen0017 literals, both expected0020 fingerprints and all migration/SQL source pins remain unchanged.

**Final-source verification:**

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_management_grants.py -k 'unexpected_grant_rewrite or implicit_database_owner or valid_administrative' -x --tb=short`

**12passed in32.91s:**eight blocker negatives and four valid-owner cases.

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_management_admission.py tests/test_portfolio_management_grants.py -x --tb=short`

**90passed in214.31s:**15 admission and75 grants cases at final repaired source. This reruns all affected retained literal/source, runtime/financial-role, fresh/upgraded bootstrap, production psql, drift and new review regressions. Changed-file Ruff lint/format, two-module mypy and git diff checks pass. No full-phase campaign or new TLS/recovery qualification is claimed.

**Updated current source hashes:** The following supersede only the two corresponding pre-review handoff hashes above. All other listed source hashes and both0020 catalogue/ACL constants remain unchanged.

- `portfolio_bootstrap.py`: `2429e45f08d72e7adf0dc816e0d5093642a92d8317bff0ad1c74d0cede7212df`
- `deploy/db/bootstrap-roles.sql`: `58a943a3887d4a53acfa798b48a3812ea7f6655324823634f9aabbb7af5a0854`

Owned birja-p13-03-review labels were checked before teardown; its containers, network and volume queries are empty afterward. No unowned source/global planning files, dependency/pin, provider, private environment, production, push or merge operation occurred. The Plan15 fixture-inventory and later recovery/TLS limits above remain in force.

### Repair Self-Check: PASSED

All eight declared implementation/test files and both repair commits exist. Actual RED precedes GREEN. The full affected90-case regression and focused12-case proof pass. Prior migration/SQL bytes and retained0017 literals remain unchanged. No tracked files were deleted; parent-owned review metadata and unrelated.claude are preserved. Ready for parent independent re-review.
