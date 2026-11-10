---
phase: 06-deploy
plan: "03"
subsystem: infra
tags: [postgresql, restic, recovery, isolation, landlock, supply-chain]
requires:
  - phase: 06-02
    provides: Consistent exported snapshots, canonical private manifests and encrypted backup/status contracts
provides:
  - Fixed isolated PG18 exact-snapshot retrieval and restricted restore with private equality verification
  - Immutable recovery-only bundle packaging, verification and installation independent of the app checkout
  - Real encrypted recovery rehearsal with concurrent writes, catalog/identity assertions and corruption controls
affects: [06-04, 06-06, 06-07, 06-08, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [Stdlib recovery verifier, Immutable SHA-addressed releases, Landlock old-host rehearsal]
key-files:
  created: [docker-compose.ops-test.yml, deploy/restore-check.sh, deploy/verify-restore.py, deploy/recovery-bundle.sh, deploy/tests/test-restore-safety.sh, deploy/tests/test-db-operations.sh, deploy/tests/ops-fixtures.py]
  modified: [deploy/backup-manifest.sql, deploy/backup-snapshot.py, deploy/tests/test-backup.sh]
key-decisions:
  - "Recovery launchers resolve an immutable independent release; target installation and commands run with the feature checkout denied by Landlock in the synthetic rehearsal."
  - "Supplied recovery archives require a separate expected SHA and trusted manifest/provenance/dependency verification before installation; no repackaging or default fallback."
  - "Private equality includes schema constraints and indexes; sequence checks prove safe future generated IDs rather than MVCC sequence equality."
patterns-established:
  - "Use only the fixed ops project, absolute reviewed Compose path, --env-file /dev/null, internal network, tmpfs and finally teardown."
  - "A local encrypted repository proves the recovery mechanism; actual off-server and calendar-run acceptance remain separately gated."
requirements-completed: []
duration: interrupted-session
completed: 2026-11-03
---

# Phase 6 Plan 3: Isolated Encrypted PostgreSQL Recovery Summary

**Exact encrypted snapshots restore financial/session state into restricted PG18 clones using verified immutable recovery bundles installed independently of the feature checkout.**

## Performance

- Implementation commits span 2026-11-02T11:53:10Z through 12:09:50Z. Execution was interrupted by a usage limit; total active execution time was not recorded and is not inferred from the overnight gap.
- Closeout completed 2026-11-03 without repeating implementation or changing runtime code.
- Tasks: 2/2; seven new runtime/test files and three necessary backup-contract adjustments.
- Latest complete exact supplied artifact rehearsal: 44.297 seconds including fixture setup, installation, recovery, negative controls and cleanup.
- Earlier executor-observed runs: default build-produced artifact 48.765 seconds; supplied artifact 42.220 seconds. These are prior-session observations, distinguished from the closeout rerun below.
- DEPL-02 remains pending actual production nightly off-server backup/retrieval/restore acceptance; no requirement checkbox is completed here.

## Accomplishments

- Restore entrypoint rejects arbitrary projects, paths, URLs, roles and ambient operational overrides before tool side effects. The reviewed recovery Compose service has no host ports or bind/volume mounts, only an internal network and bounded PostgreSQL tmpfs/resources. The runtime verifies the actual container/network configuration.
- Exact 64-character restic snapshot IDs are scoped to the expected backup set. Private staging is retrieved and verified, dump checksum and archive list checked, then a fresh database is restored with `--no-owner --no-acl --role=birja_migrator --exit-on-error --single-transaction`. No pre-import migration or in-place database restore occurs. Clone cleanup preserves failure status.
- Stdlib verification compares canonical counts, full row digests, exact numeric aggregates, UTC microsecond timestamps, revision, complete constraint/index definitions, FK validity, index readiness and identity progression. It emits booleans rather than rows or private hashes.
- Recovery-only bundles enumerate and checksum helpers, approved restic binary/provenance, reviewed Compose and pinned PostgreSQL image archive. Trusted verification rejects unsafe member paths/types, unexpected/missing members, checksum/provenance mismatches and missing runtime requirements before extraction, executable invocation or image load. Installation uses immutable SHA-addressed releases and stable launchers under the separate recovery root.
- The real integration fixture seeds application signup/account/session and buy/sell/idempotent-replay services at populated revision 0007, without destructive application test fixtures. A writer inserts after snapshot export; restored state still matches the held snapshot.
- A locally archived v0.3.1 checkout represents the old host. Installation itself runs through a transferred trusted verifier under Landlock, with the exact separately verified archive permitted; subsequent installed backup/status/restore commands cannot read the feature checkout. Installation preserves old checkout files, credentials, source Compose and revision.

## Task Commits

1. **06-03-01: Make off-server retrieval safe and executable** — `1f56561` (RED), `ff4dc26` (GREEN).
2. **06-03-02: Prove encrypted round-trip and reject corrupted financial state** — `8578b9a` (RED), `1c43d69` (GREEN).

Both RED/GREEN pairs exist in that order. Closeout verified these commits and reused the implementation; it does not claim to have personally rerun historical preimplementation RED tests.

## Verification

Fresh closeout checks on the committed implementation:

- `bash deploy/tests/test-db-operations.sh --self-test-recovery-bundle-inputs` passed: 20 rejected inputs with zero Docker, packaging or installation calls. Expected parser errors for deliberately malformed inputs are part of the passing test.
- `bash deploy/tests/test-restore-safety.sh` passed all three tests in 1.049 seconds, including rejected targets, unsafe bundle members/manifests and installation guards.
- `bash deploy/tests/test-db-operations.sh --backup-restore --recovery-bundle /tmp/birja-backup-test-artifact-kuc6vhwu/recovery.tar` exited 0. It reported real service seed/buy/sell/replay at 0007; feature checkout denial; installed launcher backup/status/retrieval/restore after local staging removal; concurrent writer isolation; private equality/invariants/identities; attempted constraint violations and generated IDs; row/manifest/FK/index/sequence negatives; encrypted checksum/manifest negatives; truncated-dump and unavailable-repository rejection; unchanged old checkout/credentials/Compose/revision.
- Exact supplied recovery artifact SHA-256: `0d56eeabcb1cf51f63b5ab306a39f2971559ffe059811053067d913955fab725`; size 199,598,080 bytes. This identifies the synthetic tooling artifact, not private database content. The runner used that exact archive without repackaging/fallback.
- Restic executable SHA was rechecked against the approved pin: `20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`.
- Ruff lint and format checks passed for `verify-restore.py`, `ops-fixtures.py` and the adjusted `backup-snapshot.py`. Bash syntax and `git diff --check` passed. No application behavior changed during closeout; no shared application database suite was started.
- Fixed-project Docker queries after the rehearsal returned no containers, networks or volumes. Private rehearsal directories are removed by the fixture's context/finally paths. The intentionally retained input archive remains separate from disposable rehearsal output for later replay.

- `bash deploy/tests/test-backup.sh` passed all 17 tests in 45.528 seconds, including actual approved local-restic encryption/rotation, the retained source-Compose contract, private packaging temporary directories, upload/cleanup/partial failure handling, quota/lock guards and honest status. Its synthetic second replacement measured 11,772 archive bytes, 3,403 local repository bytes, 7,689 ms, 5,433 child CPU ms, 61,532 KiB peak child RSS, 14 counted tool invocations, 930 packed added bytes and zero network bytes/requests. These are local tiny-fixture measurements, not production estimates.

## Resource Evidence and Limits

The 199,598,080-byte tooling artifact includes the image and executable required for independent recovery; it is not the nightly database backup size. Latest supplied-artifact integration took 44.297 seconds with locally cached images/tools. Earlier default-artifact execution took 48.765 seconds including local packaging. No new acquisition, package installation, production/provider request or actual account data was needed. Cold-cache provisioning and real provider request/wire-byte/free-tier budgets remain unmeasured.

## Deviations from Plan

**[Rule 2 — Missing critical functionality] Extend the prior backup manifest/export contract for verifiable restore.** Task 2 changed `deploy/backup-manifest.sql`, `deploy/backup-snapshot.py` and `deploy/tests/test-backup.sh` beyond this plan's original file list. Full constraint/index definitions and revision/schema validation are required to detect missing FK/index corruption and preserve the producer/verifier contract. These scoped changes are included in `1c43d69`; backup regressions are rerun during closeout. No schema migration or unrelated application change was made.

**[Rule 2 — Critical proof] Enforce old-host independence with Landlock.** The synthetic fixture denies access to the feature checkout for both transferred-verifier installation and installed launcher commands, and explicitly tests denied reads. This strengthens the planned old-host rehearsal without adding a runtime dependency to production recovery tooling. Unsupported Landlock fails the synthetic proof rather than silently weakening isolation.

## Issues Encountered

The prior executor reached a usage limit after committing both tasks and earlier successful rehearsals. This continuation inspected commits and reran the final strengthened supplied-artifact proof without restarting implementation. Docker socket access required the runtime's scoped sandbox escalation for the already authorized synthetic project. No authentication gate, provider access or new permission scope was inferred.

## Remaining Evidence / Next Plan Readiness

- Ready for sequential 06-04 populated-role work. Preserve the ops fixture's fixed-project lifecycle; never run destructive application fixtures concurrently.
- 06-08 must package its final tested systemd units through the same producer and replay that exact final archive through the established supplied-artifact interface. This artifact contains no units yet; later unit inclusion is intentional future work, not a recovery stub.
- 06-07 must prove retained installed recovery survives hardening/old-ref rollback. The current old-host test establishes recovery installation/execution independence, not hardened rollback acceptance.
- Fresh provider quota evidence, private bucket/lifecycle/Object Lock/free controls, actual off-server encrypted recovery, production host transfer/install, timer activation and actual scheduled snapshot remain pending 06-08/09 authority and evidence. The temporary local repository is not production off-server proof.
- US$0 B2 policy, latest-only create/verify-before-delete rotation, bounded resources and independent custody remain binding. No `.env`, `.aws`, production credentials/rows/logs, actual authentication/trade/email, production/service change, push, PR, merge or deployment occurred here.
- Stub scan found no goal-blocking TODO/FIXME/placeholder or disconnected implementation. Existing optional `None` defaults represent CLI choices, not stubs. No new endpoint/auth/schema surface outside the plan's privileged file/archive/storage/database boundary was introduced.
- The orchestrator owns STATE/ROADMAP/handoff updates and the separate metadata advancement commit.

## Self-Check: PASSED

All seven declared created files and this summary exist; all four task commit hashes resolve in repository history. Both TDD commit pairs are ordered RED then GREEN. Final exact-artifact rehearsal, backup regression, input/safety guards, lint/format/syntax/whitespace checks passed. No tracked deletion occurred; fixed ops containers/networks/volumes are absent. Unrelated untracked `.claude/` is preserved. The orchestrator owns planning-state advancement.
