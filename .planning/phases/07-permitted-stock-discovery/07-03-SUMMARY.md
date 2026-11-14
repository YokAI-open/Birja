---
phase: 07-permitted-stock-discovery
plan: "03"
subsystem: recovery
tags: [postgresql, exact-recovery, schema-contracts, stock-discovery]
requires:
  - phase: 07-01
    provides: Reviewed additive schema0009 and separate catalogue0010
  - phase: 07-02
    provides: Preserved crypto boundaries after the additive migrations
provides:
  - Explicit supported0007/0008/0009/0010 producer and consumer contracts
  - Exact stock/admission/calendar hashes and bounded schema/identity validation
  - Checksummed successor recovery-contract inventory with legacy compatibility
affects: [07-04, 07-13, 11-mixed-asset-recovery]
tech-stack:
  added: []
  patterns:
    - Dispatch on reviewed revision before parsing absent stock objects
    - Preserve canonical legacy SQL bytes and select inert successor fragments
    - Restore evidence and derived generations exactly without establishing authority
key-files:
  created: [deploy/tests/test-stock-recovery-contracts.py]
  modified:
    - deploy/backup-manifest.sql
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
    - deploy/recovery-bundle.sh
    - deploy/tests/test-backup.sh
    - deploy/tests/test-restore-safety.sh
key-decisions:
  - Keep standalone legacy SQL unchanged; successor callers use manifest_sql and schema_guard_sql.
  - Historical expired or mismatched-generation evidence is restored exactly, never renewed or repaired.
  - Successor inventory binds supported revisions and producer/SQL/consumer hashes; absent metadata remains valid for old artifacts.
requirements-completed: []
requirements-supported: [SAFE-01]
duration: 16min
completed: 2026-11-10
---

# Phase 7 Plan 03: Revisioned Recovery Contracts Summary

**Exact revision-selected recovery manifests include all stock identities, quotes, derived sessions and admission evidence while retaining byte-compatible legacy hashes.**

## Performance

- Approximately16minutes,2026-11-10T14:14Z–14:30Z, including isolated PostgreSQL setup and verification.
- Tasks:2/2; source/test files:7. No dependencies added.

## Accomplishments

- Producer and consumer explicitly admit only0007/0008/0009/0010. They select the contract before PostgreSQL can parse absent columns/tables. Extra/missing public relations, columns or sequences are refused, including a zero-column extra table.
- Canonical legacy query SHA256 remains `52753d97387ec491c6494d327a6037d847cdc323bafb571c2dac6bdb0d28b5a5`. The original standalone SQL is preserved with inert commented stock fragments;0007/0008 canonical output remains unchanged. **Successor callers must use `backup-snapshot.py:manifest_sql(revision)` and `schema_guard_sql(revision)`, or `verify-restore.py:canonical`; executing the raw SQL file directly remains a legacy-only operation.**
- New lanes hash expanded coin metadata and every column of stock_instruments, stock_quotes, stock_sessions and stock_data_admissions. Monetary text stays exact NUMERIC; timestamps use aware UTC with six microseconds. Nullable identity/verification/boundaries and empty tables are included. JSONB retains every calendar evidence/override/provenance field and generation; mutable session generation references remain derived state.
- Producer and consumer share exact column/table contracts and stock column types/nullability, validated check/FK names, required unique indexes, identity-sequence ownership/configuration and bounded numeric/session/admission schema checks. Unsupported quote source/feed and invalid midpoint rows cannot pass. Existing cash, starting cash, quantity, basis, fees, cash delta, idempotency and schema equality remain enforced. Restore checks sequence progression without consuming values, including both new identities.
- Recovery inventory now records supported revisions and exact producer/SQL/consumer payload hashes. All remain in the existing CORE allowlist and archive checksum envelope; no extra unverified payload is introduced. Old immutable inventories without successor metadata remain readable. Original-volume, target-isolation, read-only source and private artifact protections remain enforced.

## Task Commits

1. Task07-03-01 RED: `90cce47` — Specify revision-aware recovery dispatch.
2. Task07-03-01 GREEN: `b75b4a1` — Version exact stock recovery manifests.
3. Task07-03-02 RED: `6349876` — Reject equal but unsupported restore contracts.
4. Task07-03-02 GREEN: `9e581f7` — Enforce successor restore and payload invariants.

RED failures were behavioral: unknown revisions were accepted, the old manifest ran without prior revision selection, and matching malformed/unsupported restore state passed. No import/missing-file failure counted as RED.

## Verification

- Exact required `python3 deploy/tests/test-stock-recovery-contracts.py`:3offline tests passed;1real PostgreSQL test explicitly skipped without its opt-in flag. Legacy bytes, dispatch and unknown-revision refusal covered.
- Additional **`python3 deploy/tests/test-stock-recovery-contracts.py --postgres`:4/4passed,35.185s** against fixed disposable birja-test. It actually migrates0007→0008→0009→0010, validates canonical SQL and invokes the real restore verifier against each source manifest. A repeat run safely downgrades only that test database before rebuilding its fixture.
- The real PostgreSQL case proves34 field mutations change their table hash, covering evidence timestamps/rights/quota/attribution and every synthetic calendar source/version/review-expiry/coverage/override leaf, plus derived generation, quote timestamps/Decimals and nullable provider identity. Historical expiry and mismatched generations are preserved without granting authority.
- Actual adverse cases reject extra empty relations/sequences, an authority column added to sessions, missing session CHECK/unique index, changed sequence increment, wrong numeric scale, unsupported feed, altered stock hash and unsafe progression of each new identity sequence. Synthetic SQL fixtures contain no private records. These source/consumer checks are **not yet a pg_dump/pg_restore round trip**; Plan07-04 owns that independent exact clone/TLS/role proof.
- Exact required `bash deploy/tests/test-backup.sh`:**25/25passed,54.973s**, including actual approved restic0.19.1 local encrypted backup/rotation, unknown-schema refusal, previous-success preservation, quota and lock protections. Local evidence:14tool invocations,14,006staged bytes,1,603packed added bytes, zero network bytes/requests; no remote repository used.
- Exact required `bash deploy/tests/test-restore-safety.sh`:**6/6passed,1.360s**, including matching-but-invalid restore refusal, successor payload/revision tamper refusal, legacy inventory compatibility and rejected unsafe targets before runtime/install.
- Scoped Ruff E9/F/I, Python3.11-compatible formatting for producer/new tests, shell syntax and git whitespace checks passed. No full app/frontend/CI/image or production proof is claimed.

## Decisions and Deviations

No architectural change or file-scope expansion. Shared producer validation and consumer dispatch necessarily span both tasks, as their actions specify. Calendar semantic admission/expiry evaluation belongs to07-05/08: recovery preserves historical evidence and generation mismatches exactly and must never treat restoration as permission renewal or repair.

Existing SQL was retained as a standalone legacy query because the old isolated image-transition fixture reads it directly. Successor fragments are selected only through reviewed revision dispatch; a fixed hash test prevents accidental old-query changes. New stock metadata records defaults for exact equality without changing old metadata shape.

The offline backup executable fixture was updated for the new revision-selection exchange and full column metadata. Its module source path is held inside its private synthetic directory; no production environment variable allowlist was expanded. Formatting was explicitly kept compatible with the host operational Python3.11 rather than backend-only Python3.14 syntax.

## Known Stubs and Threat Review

None blocking this contract plan. The new schema/recovery trust boundary is within T-07-06/07/08. Identifiers in operational SQL derive only from fixed reviewed contract constants; source values and operator input are never interpolated as identifiers. Evidence hashes establish exact recovery, not provider permission or calendar authority. No new endpoint, authentication path, dependency or unplanned trust surface was introduced.

## Resources and Next Plan Readiness

Only synthetic birja-test PostgreSQL/Redis and local temporary restic repositories were used; containers/network/tmpfs were removed successfully. No .env/private configuration, real rows, production path/service/timer/volume, B2 or provider was accessed. No retained archive was installed or production tool replaced. Unrelated .claude/ files were preserved. All commits remain local and publication remains deferred.

Ready for07-04 actual restricted-role verified-TLS upgrade and exact isolated dump/restore/retained-artifact proof. That plan must use successor dispatch, preserve the old raw-SQL lane, and prove migrations' grants without repairing them. SAFE-01 remains pending; stock execution remains disabled and no phase completion is claimed.

## Self-Check: PASSED

The new test artifact exists, all four task commit hashes are in branch history, and both tasks have meaningful RED→GREEN commits. Final required suites and actual PostgreSQL corruption proof passed. No tracked-file deletion occurred; synthetic test resources were removed.
