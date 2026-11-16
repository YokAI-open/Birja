---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "17"
subsystem: infra
tags: [portfolio, recovery, immutable-evidence, schema, authorization]
requires:
  - phase: 12-15
    provides: actual scoped financial services and production router composition
  - phase: 12-16
    provides: fixed final0017 authority and restricted bootstrap contracts
provides:
  - Exact0017 producer projections and fixed schema/role/routine/trigger admission
  - Explicit migration_only refusal for0015/16 and unchanged retained manifest SQL
  - No-ACL clone authentication before fixed quarantined grants and exact financial equality
  - Actual mixed legacy NULL/new2 logical restore and reader/marker refusal proof
affects: [12-18, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [fixed catalogue fingerprint, pre-grant clone authentication, quarantined definer ACL]
key-files:
  created:
    - deploy/tests/test-portfolio-recovery-contracts.py
    - deploy/tests/fixtures/portfolio-recovery-0017.json
  modified:
    - deploy/backup-snapshot.py
    - deploy/backup-manifest.sql
    - deploy/verify-restore.py
    - deploy/backup.sh
    - deploy/restore-check.sh
key-decisions:
  - Pin the complete final catalogue independently; never trust a hash supplied by a backup
  - Restore only fixed reviewed grants after exact no-ACL schema and function authentication
  - Withhold payout/hold/root-lock EXECUTE in the quarantined clone
  - Keep logical-contract proof distinct from encrypted same-archive image/TLS qualification
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 16 min
completed: 2026-11-16
---

# Phase 12 Plan 17: Exact Portfolio Recovery Contracts

**Fixed final-schema snapshots and pre-grant clone authentication preserve owned financial evidence and mixed legacy/new digest interpretation.**

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-17-01 | f845cc8 | Exact producer/catalogue projections and explicit staged refusal |
| 12-17-02 | 4d77402 | Quarantined consumer, projection equality and actual mixed logical restore |

## Accomplishments

- Added exact0017 admission for27 tables,65 validated foreign keys,20 identity
  sequences and10 complete public routine declarations. Fixed fingerprints
  include types/defaults/nullability, constraints/indexes, complete function
  definitions, owners, trigger definitions/enabled state, role attributes and
  memberships, runtime table/column/sequence privileges and schema CREATE.
  Unknown routines/overloads and unsafe additional/grant-option ACLs refuse.
- The producer appends portfolio lineage on all seven owned financial tables,
  Account name/closed state, complete terminal closure records and SQL NULL-or2
  global split markers. Original IDs, exact monetary strings, timestamps,
  economic JSON and stored digest text remain in canonical hashed projections.
  Root counts, marker counts and invalid ownership checks are independently
  admitted. Dump-selected identity states include terminal-record identities.
- Retained0007–0014 SQL fragments remain byte-compatible.0015/16 explicitly
  raise migration_only before snapshot export reaches pg_dump/upload; wrapper
  entrypoints continue delegating to source-owned Python validation. No cloud,
  default backup command, installed recovery service or production config ran.
- The cold0017 path authenticates the exact no-owner/no-ACL catalogue before
  reconstructing fixed permissions. Fresh fixed runtime/operator roles are
  NOLOGIN; unsafe existing role attributes/memberships refuse before grants.
  The clone has no PUBLIC CONNECT. Only authenticated fixed signatures are
  revoked/granted, with payout/hold/root-lock EXECUTE withheld from scheduler.
- Consumer equality compares every table fingerprint, financial aggregate,
  lifecycle/marker count, complete schema and exact archived sequence state;
  each next identity is also checked against actual maximum IDs. No manifest
  body, function, identifier, role or grant becomes executable SQL.

## Verification

| Check | Result |
|---|---|
| `python3 deploy/tests/test-portfolio-recovery-contracts.py` | PASS,10 contracts with independent catalogue/authority/data mutations |
| Same command with `--postgres` | PASS, actual migrated mixed NULL/2 logical dump/restore, exact equality, marker refusals and reloaded journal reader |
| `python3 deploy/tests/test-stock-recovery-contracts.py` | PASS,16 offline retained contracts;8 preexisting opt-in PostgreSQL modes not run here |
| Actual0017 producer projection/admission on isolated birja-test | PASS |
| Python compilation, Bash syntax, `git diff --check` | PASS |

The synthetic actual proof starts from the guarded disposable test database,
uses the existing real0014 two-user/global split fixture, upgrades through
0017 and applies the later single global version2 split across active siblings
with a frozen old portfolio. One logical dump is restored with no owner/ACL
into an initially absent clone. Exact source/clone equality passes; scheduler
cannot insert a new missing-marker application, application cannot update a
marker, and migration owner cannot rebind a legacy marker. Reloading the real
journal reader reconstructs both versions and the frozen boundary successfully.
The clone is dropped and the source disposable schema reset to actual0017.
No real financial rows, keys, DSNs or archive payloads were displayed.

## Deviations from Plan

1. **[Rule3 — Independent mutation oracle]** Added the sanitized fixed JSON
   catalogue fixture alongside the named test module. It contains source-owned
   declarations/ACLs and zeroed synthetic counts/hashes, no economic rows or
   secrets. Runtime validation uses pinned constants, not this test fixture.
2. **[Rule1 — Cold restore PUBLIC EXECUTE]** The first real clone proof found
   that pg_restore --no-acl restores default PUBLIC EXECUTE on retained invoker
   routines, whereas ordinary bootstrap assumes migration-time revocation.
   Added fixed10-signature revocation after authentication and before grant
   reconstruction; the affected mixed restore proof then passed.
3. **[Rule2 — Sequence closure]** Added the terminal closure identity to both
   dump-state extraction and consumer progression checks, rather than checking
   only the new root/financial table rows.

## Carry Forward

- This is a logical-contract proof. The full encrypted same-archive, retained
  source/image, verified TLS/role and serial cold recovery campaign remains
  Plans18/27; no claim of its completion is made.
- Include the actual final helper inventory (check_portfolio_financial_write,
  check_stock_split_digest_version, lock_stock_portfolio_roots) and source-owned
  bootstrap/migrate modules from16 in source/image qualification. Recovery tools
  stay stdlib-only; fixed standalone restore grants mirror that bootstrap.
- The current producer/consumer CORE bytes and supported revision metadata have
  changed; package one current archive and bind subsequent stage/role/TLS proofs
  to its exact bytes. Retained0013/14 programs must use their pinned retained
  source consumers, not substitute current root-aware runtime code.
- All28 milestone requirements remain unchecked pending integrated proof and
  human acceptance. Phase7 live gaps and disabled admissions remain unchanged.

## Known Stubs

None. No placeholder callable, permissive schema wildcard, fabricated final
schema, skipped new test or help-only result substitutes for the contract proof.

## Self-Check: PASSED

Both task commits exist; all seven created/modified artifacts exist. No tracked
file deletion, package/lockfile change, provider request, production operation,
branch switch, push or merge occurred. Unrelated `.claude/` remains untouched.
