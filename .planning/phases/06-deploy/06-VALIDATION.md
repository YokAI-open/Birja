---
phase: 6
slug: deploy
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-30
---

# Phase 6 — Validation Strategy

Planning contract only. No tests, services, backups, installations or live
operations have run for Phase 6. Exact task IDs and producer dependencies
are reconciled below. Independent plan review and all execution results
remain pending.

## Test Infrastructure

Reuse pytest/asyncio, Vitest, Playwright and existing offline shell tests.
The research proposes new backup/restore/role/TLS operational runners and
an isolated PostgreSQL 18 fixture; producer tasks must create them before
their commands are referenced as executable checks. No production or dev
database is a test target. No real identity or email automation.

Quick feedback: run the produced offline restore-safety/backup checks first,
before PostgreSQL setup, settings fixture lifecycle or old-image builds.
The 06-03 restore-safety producer includes real packaging/manifest/path and
installation guard tests; these assert behavior with zero Docker calls on
rejection, rather than source-text or syntax-only checks. Target under 30
seconds for this first feedback; actual duration is pending and must be
measured, never presumed. Record fast-check time, fixture/image setup time
and complete integration time separately, including cold-cache runs. A fast
pass cannot replace complete real PG18 recovery/role/TLS/old-image proof.
The 06-03-02 and 06-07-02 runner producers define optional
`--recovery-bundle <archive>`; omission uses their existing build-produced
default, while supplied input must replay the exact verified archive without
repackaging or fallback. Each runner's `--self-test-recovery-bundle-inputs`
provides fast option/path/hash/manifest/provenance/dependency-closure negatives
with zero Docker/install/download calls. 06-08 invokes these established
interfaces on the final tested-unit artifact: old-host installation and full
backup/retrieval/restore, then unchanged launchers/hash before/after hardening,
with no target feature checkout. Static planning does not establish a pass.
Long gates run serially with bounded progress reporting; exceeding the
target is recorded honestly and does not weaken critical integration.

## Per-Task Verification Map

Reconciled: 30 tasks in 13 sequential waves. All commands are produced in
the same task's RED phase or an earlier plan. Actual test runs and runtimes
remain pending; structural planning checks do not prove execution.

| Task(s) | Requirement | Verification / producer | Status |
|---|---|---|---|
| 06-01-01 | Both | Existing git branch/base/diff checks before source mutations | pending |
| 06-01-02,03 | Both | Explicit operating-policy and blocking-human provenance decisions | pending human |
| 06-02-01,02 | DEPL-02 | Produces test-backup.sh and backup/status/snapshot/manifest; RED then GREEN | pending |
| 06-03-01 | DEPL-02 | Produces test-restore-safety.sh and actual test-db-operations.sh lifecycle | pending |
| 06-03-02 | DEPL-02 | Produces recovery-bundle.sh/ops-fixtures.py; fast bundle guards then --backup-restore, tamper negatives and old-checkout-only populated0007 install | pending |
| 06-04-01,02 | DEPL-01/SC4 | Extends real runner --roles; populated0007->0008 and denials | pending |
| 06-05-01,02 | DEPL-01/SC4 | Produces test-db-config.sh and focused test_db_connection.py/config tests | pending |
| 06-06-01,02 | DEPL-01/SC4 | Extends real runner --tls/--all; real handshake/credential negatives | pending |
| 06-07-01,02 | DEPL-01/SC4 | Fast existing offline regressions/restore guards then real old-image test-rollback-db-security.sh; same installed recovery entrypoints before/after hardening | pending |
| 06-08-01 | Both/SC2 | Extends fast backup timer/status; final bundle packaging/old-host install rehearsal with tested units | pending |
| 06-08-02 | Both/SC3 | Produces test-ci-ops.py and required ops job; prior backup/safety | pending |
| 06-08-03 | Both | Full backend/frontend/image/audit/coverage + serial ops/rollback and separate reviews | pending |
| 06-09-01 | DEPL-02 | Explicit scoped host/backup/private-manifest/retrieval/timer approval | pending human |
| 06-09-02 | DEPL-02/SC2 | Approved exact recovery artifact transfer/hash verification/install on unchanged v0.3.1, then real remote restore/calendar activation | pending live |
| 06-10-01,03 | Both | Explicit feature push/merge/version-preparation choices | pending human |
| 06-10-02 | DEPL-01/SC3 | Prior CI contract + actual feature-head all-job/browser/ops CI | pending remote |
| 06-11-01 | DEPL-01 | Git diff + prior CI/backup/safety; selected-version candidate gates | pending |
| 06-11-02 | DEPL-01 | Explicit release push/PR approval | pending human |
| 06-11-03 | DEPL-01/SC3 | Prior CI contract + actual release-head all-job CI | pending remote |
| 06-12-01 | Both | Individually scoped release/tag/backmerge/live approval | pending human |
| 06-12-02 | Both/SC4 | Prior quick tests + approved recovery recheck, live SSL/roles and smoke | pending live |
| 06-13-01 | DEPL-01/SC1 | Owner/friends Gmail + Outlook signup/trade/portfolio/history | pending human |
| 06-13-02 | Both/all4SC | Prior CI contract/diff + independent/separate exact-evidence goal verification | pending |

### Research-level capability map

| Capability | Requirement | Secure behavior | Proposed command / producer | Status |
|---|---|---|---|---|
| Backup failures and scheduling | DEPL-02 | No false success, no overlapping run, fresh remote snapshot evidence | `bash deploy/tests/test-backup.sh`; producer required | pending |
| Restore guard | DEPL-02 | Reject dev/prod target before Docker call; reject corrupt artifact | `bash deploy/tests/test-restore-safety.sh`; producer required | pending |
| Real encrypted recovery | DEPL-02 | Retrieve exact encrypted snapshot, restore synthetic financial/session state and constraints privately | `bash deploy/tests/test-db-operations.sh`; isolated fixture/manifest producers required | pending |
| Role/TLS transition | DEPL-01, SC4 | Runtime DDL/admin denial; migrator succeeds; CA/hostname verification and plaintext rejection | Same isolated runner plus focused settings tests; producers required | pending |
| Old-ref rollback | DEPL-01, SC4 | v0.3.1 cannot reinstate privileged/plaintext access | `bash deploy/tests/test-rollback-db-security.sh`; producer required | pending |
| Trading story | DEPL-01, SC3 | Existing fake/console CI happy path remains green | Existing `frontend/e2e/trade.spec.ts` and `portfolio-history.spec.ts` via actual CI | pending |
| Regression | Both | Money/auth/portfolio/history and deployment checks preserved | Existing CI-equivalent backend/frontend/image/deploy gates | pending |

## Sampling and Wave 0

Every automatic task needs an executable automated check or a dependency
on its named test producer. Record intended RED before behavior changes;
do not count missing fixture errors as behavioral regressions. Do not run
destructive database/migration fixtures concurrently. Always tear down
only the fixed isolated project in finally; never production as fallback.

No three consecutive automatic tasks may lack feedback. Full gates pass
before push/review; actual CI and separate approval precede merge.

## Manual-Only Verification

- Choose external storage, cost limits, retention, recovery targets, key
  custody and nightly schedule; supply credentials privately at execution.
- Approve scoped production backup/download/isolated restore, privilege/TLS
  rollout and production deployment only after concrete rehearsal evidence.
- Prove an actual nightly off-server snapshot and a successful retrieval/
  isolated restore; record IDs, times and pass/fail, never private rows.
- Friend/owner performs Gmail and Outlook inbox/sign-up/trade checks after
  an authorized release. No messages are sent by the assistant implicitly.
- Record push/PR, merge and release/deploy choices separately.

## Validation Sign-Off

- [x] Final task map and missing-file producers reconciled with plans.
- [x] Automatic task coverage and feedback continuity verified in planning.
- [x] Isolated integration/rollback and cleanup contracts concrete.
- [x] Human/live prerequisites explicit; no production authority inferred.
- [x] Planning compliance reviewed separately from execution results.

Planning approval: independent recheck passed 2026-11-02, zero active blockers or warnings. All implementation, runtime tests, Wave 0 producers and live evidence remain pending execution.
