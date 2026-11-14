---
phase: 06-deploy
plan: "14"
subsystem: infra
tags: [backup, recovery, flock, restic, postgres, provenance]
requires:
  - phase: 06-deploy
    provides: "06-03 independent recovery artifact and 06-04..06 role/TLS fixtures"
provides:
  - "Canonical validated shared operation lock with parent-safe inherited handles"
  - "Private durable restore evidence and an explicit exact remote recovery gate"
  - "Authenticated deploy-recovery-v2 profile and install-once recovery hooks"
affects: [06-07, 06-08, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [kernel-backed inherited lock validation, atomic recovery evidence, immutable installed recovery]
key-files:
  created: [deploy/tests/test-deploy-prerequisites.py]
  modified: [deploy/configure-db.sh, deploy/provision-db-tls.sh, deploy/backup-snapshot.py, deploy/verify-restore.py, deploy/tests/ops-fixtures.py, deploy/tests/test-backup.sh]
key-decisions:
  - "Every synthetic operation uses guarded config-root/operation.lock; production retains /var/lock/birja-deploy.lock."
  - "Ordinary nightly status remains bounded; rollout separately requires fresh exact snapshot and matching full-restore evidence."
  - "Specialized hooks require authenticated deploy-recovery-v2 before runtime probes or installation; generic legacy verification remains supported."
requirements-completed: []
duration: "15min recorded RED-to-closeout interval, excluding initial context loading"
completed: 2026-11-03
---

# Phase 06 Plan 14: Deployment Recovery Prerequisites Summary

**Kernel-validated shared locks, durable completed restore evidence, and repeated exact recovery through one immutable installed artifact.**

## Performance and Task Commits

All three tasks completed serially. The first RED commit was recorded at 09:13:56 UTC; closeout was around 09:29 UTC. Initial context loading preceded that interval. Seven source/test files changed, including one explicitly authorized existing-test path adaptation; the eighth file is this summary. No application dependency was added.

| Task | RED | GREEN |
|---|---|---|
| 14-01 Shared validated lock | `4d679e8` | `24b62d3` |
| 14-02 Durable recovery evidence/gate | `f396478`, corrected meaningful RED `792b1ef` | `dab3647` |
| 14-03 Authenticated profile/install-once lifecycle | `b706643` | `493eb88` |

Task 14-01 RED exposed recursive role/TLS flock acquisition, accepted unheld/wrong-inode descriptors, and backup's different inode. Task 14-02's first intercepted method binding was incorrect; `792b1ef` corrected it and reached successful retrieval/verification before failing on absent durable evidence. Task 14-03 RED used a complete checksummed legacy artifact, accepted by generic verification, and exposed a Docker call before capability rejection. Every task has a meaningful RED before its production GREEN.

## Interfaces for Plan 06-07

- `backup-snapshot.py.acquire_operation_lock(path, inherited_fd=None)` returns an owned context-managed duplicate or standalone held file. It checks canonical non-symlink regular path, expected owner, no group/other writes, same device/inode, bounded numeric descriptor and kernel `FLOCK ADVISORY WRITE` evidence. Standalone acquisition is nonblocking with `O_NOFOLLOW` and inode rechecks. Closing the owned handle never explicitly unlocks the parent's description.
- `load_config` derives internal `_config_root` from the guarded synthetic config path. `Job.lock`, role/TLS helpers, restore and gate use `<root>/operation.lock`; production uses `/var/lock/birja-deploy.lock`. No JSON/environment lock-path override exists. The inherited descriptor locator remains `BIRJA_BACKUP_LOCK_FD`.
- `recovery_binding(c)` computes `source_project`, `db_name`, `db_user`, `repository_sha256`, `config_sha256`, `toolchain_sha256`, `bundle_sha256`. Installed bundle identity is derived from the immutable recovery release directory and verified inventory/checksum file, with actual helper/runtime executable hashes. Noninstalled execution has no bundle identity and cannot satisfy the rollout gate. Config identity binds source definition, repository, recovery/credential material and stable safety policy; changing observed quota times/counters alone does not change it. Current headroom is still checked.
- `recovery_gate(c, snapshot_id, expected)` requires exactly the binding fields above plus `source_release` and `source_revision`. It acquires the shared lock, requires matching latest backup attempt/success and restore attempt/success, exact snapshot equality, private versioned state, matching digests/identities and nonfuture ordered timestamps within configured freshness (at most 26h). It rechecks actual exact remote snapshot scope/time and byte-identical manifest through bounded restic metadata/dump calls after current quota validation. It returns only `snapshot_id`, `recovery_verified`, `completed_utc`; private hashes stay private.
- CLI: `python3 <installed-release>/deploy/backup-snapshot.py recovery-gate --snapshot ID --source-release SHA40 --source-revision REV --bundle-sha SHA64 [--synthetic CONFIG]`. Duplicate/unknown options fail; local config/tool expectations are computed locally. The release/revision describe the **prechange source**, independent of a future candidate ref. A new nightly snapshot can pass ordinary status while requiring a new explicit restore before rollout. Existing backup/status wrapper syntax is unchanged.
- `restore-check --synthetic CONFIG --snapshot ID --isolated-clone` selects only fixed `birja-restore-check`; default synthetic behavior remains available. The separate clone retains the unchanged reviewed Compose SHA, absolute Compose/env-file isolation, no mounts/ports, tmpfs storage and complete existing verifier. Caller-owned `birja-ops-test` is untouched by this option. Production still requires the existing approved-clone guard.
- Private state: `restore-last-attempt.json` is published before retrieval; `restore-last-success.json` and matching successful attempt are published only after verification, clone teardown and staging removal succeed. Each record binds exact snapshot, source/repository, release/revision, manifest/dump/material, config/tool/bundle, unique attempt ID and UTC/epoch start/completion. Failure/interruption/cleanup failure leaves an unusable latest attempt even if an earlier success remains.
- `verify-restore.py.bundle_verify(archive, sha, required_profile=None)` and `bundle_install(archive, sha, synthetic_root=None, required_profile=None)` accept the optional authenticated profile requirement. CLI: `bundle verify|install ... --require-profile deploy-recovery-v2`. Profile validation follows external archive SHA, exact inventory, checksums, approved restic provenance and image identity, and precedes `runtime()`, Docker load, extraction/install or archived execution. New packages declare `recovery_profile=deploy-recovery-v2`; generic legacy verification remains valid.
- `ops-fixtures.py.installed_recovery(archive_arg=None)` is a context manager yielding attributes `root`, `archive_sha`, `release`, `tools`, `config_path` (plus internal archive/immutable tracking). It validates/installs/initializes once, creates the old-host file context/local encrypted repository, and **never owns source Compose up/down or seed**. Exact supplied archives use separately recorded SHA and never trigger fallback packaging. The transferred trusted installer also requires the profile.
- `recovery_roundtrip(session, *, source_revision, source_release)` uses the same installed launchers for backup/status/exact retrieval/full isolated restore/strict gate, asserts immutable archive/helper/launcher identity and returns the selected snapshot ID. It accepts fixed identity values only, uses the separate clone, and does not start/stop/seed the source. Caller owns source population, roles/TLS/0008 and old-image selection. Per-attempt source identity/config changes require a fresh backup/restore, never rewriting previous evidence to match.

## Verification

- Final dedicated stdlib suite: **14 passed in 7.315s**, zero Docker/provider calls. Selected `--locks`, `--evidence`, `--fixtures` and default-all execution are supported. Actual role/TLS embedded main paths and actual backup/restore/gate entry paths share one parent FD passed explicitly with `pass_fds`; independent calls contend and parent ownership survives child exit. Rejection covers unheld/shared/wrong inode/symlink/unsafe mode/closed FD and ownership mismatch. Ownership mismatch uses a substituted effective-UID observation against the real owned inode because the sandbox cannot chown to an unmapped UID.
- Evidence tests cover failed latest attempt, verification/interruption/teardown failure, missing installed identity, expected source/digest mismatch, stale/future/wrong snapshot state, current remote absence/future time, stable config versus volatile quota observation, private atomic files, and ordinary nightly success without full restore.
- Profile test uses all real approved restic bytes/provenance and complete archive checksums; only its small synthetic image's trusted identity is substituted. Generic legacy verification succeeds. Legacy, absent and unknown profiles reject specialized selection and trusted installation with zero runtime/Docker/installer/default-builder calls. Repeated-hook tests exclude source lifecycle calls and use the same installed launcher paths with explicit separate-clone selection.
- Existing backup regression: **17 passed in 46.258s**, including real approved local restic encryption/latest-only rotation and failure preservation. Local benchmark: 12,233 archive bytes; 1,199 packed bytes added; 3,940 repository bytes; 14 tool invocations; 7,510ms measured transaction; 5,270ms child CPU; 59,904 KiB peak child RSS; zero network bytes/requests. These synthetic local measurements are not B2 cost or production-size evidence.
- Existing restore safety: **3 passed in 0.961s**. Existing supplied-input self-test: **20 rejections**, zero Docker/package/install calls.
- Real default artifact recovery: **77.774s**, **199,618,560-byte** artifact. Same installed artifact completes two full recovery/gate rounds, including separate fixed clone, concurrent writer snapshot proof, exact private row/money/session/schema equality, restricted restore and generated identities. Existing row/manifest/FK/index/sequence, encrypted checksum/manifest, truncation and unavailable-repository negatives remain. Original source revision 0007, checkout, credentials and Compose assertions pass.
- Final exact supplied artifact recovery: **74.248s**, **199,618,560 bytes**, archive SHA `443fd82aa4ef034140d2811cddec40bddd45316af17cd99458999a5b7e2f31a5`. Same complete assertions and two recovery rounds pass. Default packaging was replaced with a hard failure after creating the supplied artifact: **fallback package calls=0**, selected archive unchanged. The outer private temporary artifact directory was removed afterward.
- Existing roles integration: setup **4.077s**, integration **33.595s**; 12 input/lock rejections, populated ownership transfer/repeatability, actual services/scheduler, concurrent 0008 validity and **65 denied operations** pass.
- Existing TLS integration: setup **12.203s**, integration **37.935s**; actual PG18 app/scheduler/migrator SSL, bad CA/hostname/plaintext rejection, service credential/mount isolation and renewal pass.
- Final affected Python/embedded-Python AST, shell syntax, Ruff lint/format and git whitespace checks pass. No tracked deletion occurred. Final Docker queries explicitly returned **zero containers, networks and volumes for both birja-ops-test and birja-restore-check**. Fixtures ran serially.

## Deviations from Plan

**[Rule 3 - Necessary regression call-site adaptation]** The existing backup test opened the former `state/operation.lock` at two call sites (contention and inherited ownership). After normalization those two tests correctly failed while the other 15 passed. The orchestrator explicitly authorized the single-file literal path adaptation in `deploy/tests/test-backup.sh`; both now open root `operation.lock`, preserving every assertion. Included in `dab3647`; all 17 tests then passed. No compatibility fallback or additional runtime file was introduced.

The implementation exceeds the scope document's approximate line estimate because durable state checks, behavioral negatives and formatting require more lines. It remains within the six declared source/test files plus the explicitly authorized one-file test adaptation; no new subsystem, dependency or ownership expansion occurred.

## Issues and Authority

Initial repository index writes and Docker access required existing sandbox escalations, which were approved for scoped local commits and fixed synthetic operations. The initial uv wrapper could not write its external cache; the existing locked `.venv/bin/ruff` ran directly instead. No tool/package was installed. No authentication gate occurred.

No goal-blocking stub or unmitigated new trust surface was found in the affected-file scan. The new lock/evidence/archive surfaces are covered by this plan's threat model. Local privileged/root custody remains its accepted trust boundary.

All operations-ledger restrictions persist: B2 US$0 paid usage policy and current fresh allowances, latest-only verified replacement, 26h ceiling, bounded resources and independent recovery custody. No provider request, production/private-secret read, actual authentication/trade/email, deploy/restart, push, PR, merge or release occurred. Local recovery is synthetic proof only; **DEPL-01/02 and actual provider/live acceptance remain pending**, hence `requirements-completed: []`.

Plan 06-07 can now consume the hooks for pre-hardening, post-roles/TLS/0008 and actual v0.3.1 rollback in one caller-owned lifecycle. Its retained orchestrator/overlay/old-image runner remains its original responsibility. The parent owns STATE/ROADMAP/handoff updates; this executor intentionally did not stage or edit them. Unrelated `.claude/` remains untouched.

## Self-Check: PASSED

All seven owned/authorized source/test files and this summary exist. RED/GREEN commits `4d679e8`, `24b62d3`, `f396478`, `792b1ef`, `dab3647`, `b706643`, `493eb88` resolve in history in the recorded order. Final scoped checks, full real recovery/role/TLS proofs, exact supplied-artifact identity and explicit empty fixed-project cleanup queries are recorded above. No required work in this prerequisite remains.
