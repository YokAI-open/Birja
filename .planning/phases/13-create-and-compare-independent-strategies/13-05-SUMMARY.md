---
phase: 13-create-and-compare-independent-strategies
plan: "05"
subsystem: recovery
tags: [postgresql, recovery, quarantine, source-authentication, portfolios]
requires:
  - phase: 13-04
    provides: Exact0020 producer, V2 inventory and independent management oracle
provides:
  - Explicit V1/V2 recovery consumer and authenticated0020 quarantine reconstruction
  - Actual no-owner/noACL logical restoration preserving all29tables and22identity tails
  - Genuine fixed0017/current0020 smoke source selection and migration/rollback refusals
affects: [13-15, 13-17]
tech-stack:
  added: []
  patterns: [source authentication before imports, transactional ACL reconstruction, independent before-backup oracle]
key-files:
  created: []
  modified:
    - deploy/verify-restore.py
    - deploy/tests/test-portfolio-recovery-contracts.py
    - deploy/tests/test-portfolio-management-recovery.py
    - deploy/tests/test-portfolio-migration-runner.py
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/test-portfolio-smoke-image.py
key-decisions:
  - "0020 restore retains administrative database/schema ownership and gives only the restricted migrator explicit CONNECT."
  - "Retained0017 smoke uses the complete fixed4b4320b release; current0020 never overlays its runtime."
  - "The focused real logical proof is distinct from later frozen-source encrypted/image/TLS qualification."
requirements-completed: [PSAFE-07, PFUND-02]
duration: 14min
completed: 2026-11-18
---

# Phase 13 Plan 05: Verified Consumer and Retained Recovery Summary

**Versioned recovery restores original metadata, creation grants, initialization latches and sequence state while management and scheduler economic helpers remain quarantined.**

## Performance

- Approximately14minutes, 2026-11-18 09:14–09:28UTC.
- Tasks:2/2; six implementation/test files plus this summary.
- Each task has an actual failing test commit before its implementation commit.

## Accomplishments

- The consumer admits exact V1 and V2 member inventories separately. V2 requires0020, deploy-recovery-v3, its additional exact source payloads and the fixed complete0017 archive. Legacy revision arrays, literal0017 fingerprints, ten original routine signatures and earlier SQL hash expectations retain their meanings. Unknown/partial revisions and crossed payload versions refuse. Missing producer/consumer/CORE/unit/image/source members refuse before runtime use.
- Six independent current source pins are checked before importing current bootstrap authority. The restored noACL schema, complete routine definitions, ACL projection, catalogue, unsafe-role/rewrite/ownership checks, initialization/grant invariants and identity inventory must match reviewed constants before grant SQL. All17 authenticated routine signatures are revoked; grants are reconstructed in one transaction and app create/initialize/metadata plus scheduler dividend apply/hold/root-lock remain revoked. Complete quarantined authority is rechecked afterward. Account INSERT and metadata/initialization grants remain inaccessible.
- The actual0014→0017→0020 producer/restoration proof retains the legacy123.45cash/7777baseline book, zero-book initialization, renamed original creation payload, closed original key and name-reusing successor. A separately fresh0020 migration/bootstrap is also admitted with empty provenance journals. The before-backup oracle compares every29-table row and22sequence tails after restore; the oracle is never regenerated from restored data.
- Real populated0020 downgrade refuses before writes, and the schema consumer loaded from the authenticated complete fixed0017 archive refuses an actual0020 connection. Original app replay at cap and closed/conflicting original refusals still pass without changing table/sequence bytes. Eight mutations of the independently measured noACL projection (journal, latch, sequence, schema, helper, ACL, source catalogue, unsafe authority) refuse before any grant SQL.
- Smoke now selects current0020 management or immutable0017 source/runtime/fixture explicitly. Retained builds use complete authenticated source; no HEAD substitution or source overlay occurs. Generated programs read the exact selected schema through verified TLS before application imports. Current generated verification wires actual separate app/scheduler clients, original-key replay and account/initialization privilege assertions. Image contracts retain dirty source, source-change, build-failure, immutable-ID and revision/RootFS refusal cases.

## Task Commits

1. Task1 RED: `14a21c6` — Specify versioned restore consumer admission; actual V2 rejection/missing source-authentication failures.
2. Task1 GREEN: `a7f595d` — Authenticate and quarantine versioned restores, including actual noACL roundtrip.
3. Task2 RED: `6d1d931` — Require genuine retained smoke source; actual missing selected-runtime dispatch failures.
4. Task2 GREEN: `154c508` — Prove source-bound recovery transitions and retained/current smoke wiring.

## Verification

Final focused commands and results:

- `python3 deploy/tests/test-portfolio-management-recovery.py` — **8passed**,7.01s. Includes actual V2 assembly and consumer verification with mocked external image/registry transport, all source hash mutations, missing CORE/unit/image/source members, independent original-key/metadata/latch/sequence oracle mutations and exact restored-state equality.
- `python3 deploy/tests/test-portfolio-recovery-contracts.py` — **11passed**,0.43s. All original ten0017 contracts plus explicit unchanged V1 inventory/no implicit successor upgrade.
- `python3 deploy/tests/test-portfolio-migration-runner.py` — **6passed**,1.91s. Authenticated retained schema consumer, exact source substitution and unsafe migrator identity refusal, retained release and successor precheckout refusal contracts, stopped-writer/finalization ordering.
- `python3 deploy/tests/test-portfolio-smoke-image.py` — **9passed**,1.77s. Genuine complete fixed0017 build context, rejected partial/unknown revisions before Docker operations, source/image binding and compiled current/retained admission/client wiring.
- `python3 deploy/tests/test-portfolio-fixture-contracts.py` — **8passed**,1.63s; affected prior-plan source/image/oracle contracts remain green.
- `env -i PATH="$PATH" HOME=/tmp python3 deploy/tests/test-portfolio-management-recovery.py --postgres` — **passed at final database-proof source**. Actual migrations, restricted app replay/refusals, populated downgrade refusal, authentic fixed0017 source against actual0020, no-owner/noACL dump/restore, quarantined ACL assertions, independent full oracle comparison, eight measured-noACL pregrant negatives and separate fresh0020 bootstrap pass. Only owned disposable birja-p13-04 resources and existing Python3.14/cached pinned images were used.
- All six changed Python files parse; targeted Ruff E9/F63/F7/F82 and `git diff --check` pass. No whole-file lint success is claimed: existing scripts retain broader lint findings, including the pre-existing unused tempfile import in the retained recovery contracts.

## Deviations from Plan

**1. [Rule2 — Correctness] Administrative recovery boundary ownership.** The actual restore exposed that the old clone recipe made birja_migrator the database owner. Reviewed0020 admission correctly forbids migrator database/schema ownership. The0020 branch now gives only these boundaries to the fixed administrative identity, leaves tables/routines owned by migrator and explicitly retains migrator CONNECT after revoking PUBLIC CONNECT. Actual noACL restoration and full fingerprint/oracle equality prove the adjustment; V1 restoration is unchanged. Commit:`a7f595d`.

**2. [Rule3 — Blocking historical harness] Explicit real successor proof replaces implicit historical staged runner.** The old migration-contract command automatically invoked an unowned Phase12 staged image harness using live current source with0017 expectations. It now runs six offline contracts by default and exposes an explicit `--postgres` mode calling this plan's guarded real0014→0017→0020/fresh/restore/refusal proof. Retained deployment tests use actual immutable release identities and preserve the old deploy entrypoint's successor refusal. No unowned deployment script or old source hash was changed. Commit:`154c508`.

No architecture, package, migration-byte, financial-guard or accepted-risk-policy change occurred.

## Limits and Next Plan Readiness

This is focused logical/authority/source evidence. Actual smoke image builds, restricted app/scheduler verified-TLS smoke execution, restic encryption, source destruction, separate-server cold recovery and the complete same-archive retained/current serial campaign were **not run here**. Generated TLS client/admission code was compiled and contract-checked; this is not a TLS execution receipt. Plan17 still owns those actual frozen-source qualifications. Plan15 retains wider migration/critical/source/serial inventories and deployment integration. This plan does not mark whole requirements or the phase accepted.

The old recovery archive remains untouched at `/tmp/birja-phase12-proof/recovery.tar.gz`, SHA256`d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be`. Exact owned container/network/volume queries are empty after teardown. No private environment, provider, production, new dependency/lock/pin, push or merge operation occurred. Issue35 expiry2026-12-17T00:00:00Z and Python image pin20261111 are unchanged. Unrelated.claude remains preserved. Parent exclusively owns STATE/ROADMAP/REQUIREMENTS/review updates; none were edited or staged here.

## Self-Check: PASSED

All six declared implementation/test paths and this summary exist. Four task commits exist, with RED before GREEN for both tasks. No tracked file deletions or task-generated untracked output remains. Stub scan found no TODO/FIXME/placeholder markers in the six changed sources; no new unplanned endpoint/auth/schema trust boundary was introduced. Shared planning progress remains parent-owned.
