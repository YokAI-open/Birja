---
phase: 06-deploy
plan: "02"
subsystem: infra
tags: [backup, postgresql, restic, quota, operations, tdd]
requires:
  - phase: 06-deploy-01
    provides: Approved operating ledger and signed-checksum-verified local restic 0.19.1
provides:
  - Locked consistent archive/private-manifest producer and encrypted snapshot rotation
  - Separate atomic last-attempt/last-success freshness reporting
  - Offline failure contracts and actual local restic encryption/rotation evidence
affects: [06-03, 06-07, 06-08, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [Exported repeatable-read snapshot, Exact-ID create-before-delete rotation, Fail-closed quota evidence]
key-files:
  created: [deploy/backup.sh, deploy/backup-status.sh, deploy/backup-snapshot.py, deploy/backup-manifest.sql, deploy/tests/test-backup.sh]
  modified: []
key-decisions:
  - "Operations config is validated root-owned JSON at /etc/birja/backup.env; it is never sourced."
  - "Routine assurance is upload verification, exact ID/files, retrieved manifest and structural integrity; full remote retrieval/restore remains separately required."
  - "Quota evidence expires after 300 seconds; unattended provider-usage refresh is a remaining 06-08/09 integration requirement."
  - "Prune uses zero data repacking; residual shared packs and hidden versions remain counted against the next observed quota."
patterns-established:
  - "Unknown/foreign snapshot groups abort before upload or deletion; only exact enumerated prior IDs are forgotten."
  - "An inherited lock descriptor requires matching inode and an existing exclusive flock in Linux fdinfo."
requirements-completed: []
duration: 15min
completed: 2026-11-02
---

# Phase 6 Plan 2: Consistent Encrypted Backup and Honest Status Summary

**Exported PostgreSQL snapshots feed canonical private manifests and encrypted restic replacements, with verified create-before-delete rotation and failure-aware freshness status.**

## Performance

- Started: approximately 2026-11-02T11:35Z; RED commit recorded at 11:39:10Z.
- Completed: 2026-11-02T11:50Z; approximately 15 minutes wall time.
- Tasks: 2/2 implementation tasks; five declared implementation/test files.
- Live DEPL-02 acceptance remains pending. No requirement checkbox was completed.

## Accomplishments

- Source-safe shell entrypoints use strict Bash and private umask. The stdlib producer validates config/target before tool calls, clears ambient credential/endpoint variables, uses argument arrays, and suppresses raw diagnostics.
- The exporter transaction remains alive through canonical manifest extraction, `pg_dump -Fc --compress=none --snapshot=...`, archive header/nonempty validation and `pg_restore --list`. Restic performs the sole compression/deduplication step.
- Reviewed SQL covers all columns of users, accounts, auth_sessions, refresh_tokens, coins, prices, holdings, trades and alembic_version. Ordered SHA-256 row/table digests, counts, exact NUMERIC strings, six-microsecond UTC timestamps and financial aggregates remain private. Invalid financial checks fail before upload.
- The complete job, verification and pruning share the deployment lock. Inherited-descriptor reuse verifies the exact inode and already-held exclusive flock; a bare flag or open unlocked descriptor fails.
- Success requires a full 64-character snapshot ID, exact matching group/files/sizes, byte-equal retrieved private manifest and successful structural check. Only then can explicitly enumerated old Birja snapshot IDs be forgotten and unreferenced data pruned. Foreign groups abort; no wildcard retention, initialization or unlock is performed.
- Last attempt starts as failed/running, independently of last success. Missing, stale, future, corrupt, interrupted or newer failed state returns status 1; invalid config returns 2; only fresh matching success returns 0. Publication follows successful staging cleanup.

## Task Commits

1. **06-02-01: Specify backup happy path and failure contracts** — `bedb9a5` (test; callable preimplementation entrypoints included).
2. **06-02-02: Deliver producer and freshness reporting** — `1d22af4` (feat; includes completed tests and reviewed SQL).

## Verification

- Behavioral RED: 12 test methods executed against callable entrypoints, producing 14 expected assertion failures. Missing files were not counted as behavioral RED.
- Final GREEN: `bash deploy/tests/test-backup.sh` — 16 methods passed in 43.663 seconds; the plan-required second complete run passed all 16 in 43.590 seconds with no implementation changes between runs.
- Tests cover exporter lifetime/snapshot identity, dump/empty/archive/manifest failures, partial/failed uploads, exact ID/content mismatch, structural verification failure, previous-success preservation, rotation order, foreign groups, quota/headroom/hidden/unfinished/other-account storage, stale evidence, request/download ceilings, stage limits, prune interruption, cleanup failure, SIGTERM, concurrent jobs, forged and genuinely held descriptors, source safety and diagnostic redaction.
- The approved binary's SHA-256 is rechecked before the actual local-restic test. It initializes an encrypted temporary local repository, completes two synthetic backups, rotates to one snapshot and verifies status. No network storage or PostgreSQL service is contacted.
- Actual local test caught restic's rooted relative file paths (`/manifest.json`, etc.); expectations were corrected and rerun against the real binary.
- Ruff lint/format, Bash syntax and `git diff --check` pass. Shellcheck is not installed; no installation was attempted. No application behavior changed, so application suites were not rerun.
- No TODO/FIXME/placeholder implementation remains. No security surface beyond the plan's privileged file/config/database/storage boundary was introduced. No schema migration or new network endpoint was added.

## Resource Evidence and Limits

The first full GREEN run's second local replacement measured: bundle 11,772 bytes; local repository 3,402 physical bytes; elapsed 7,486 ms; child CPU 5,188 ms; peak child RSS 60,032 KiB; 14 counted subprocess calls plus the exporter process; 930 packed payload bytes added. Network bytes and provider requests were zero because this repository is local. These small synthetic artifacts are not production-size, compression-ratio, egress or billing estimates.

The runner bounds output files, total staged content, elapsed job time and tool invocations. Restic uses two connections, two S3 retries, 30-second stuck-request timeout, 1 MiB/s transfer limits, two Go CPUs and a 256 MiB Go soft memory limit. There is no wrapper retry loop. `GOMEMLIMIT` is a soft runtime bound, not a hard process RSS limit. HTTP request totals and wire bytes are explicitly marked unmeasured in status metrics; tool invocation counts and packed payload size must not be relabeled as those measurements.

Fresh quota evidence must count visible repository storage, hidden B2 versions, unfinished uploads and all other account use. Upload/repack reserves are added without assumed dedup savings; local staging, download allowance and request reserve are checked before upload. Storage exhaustion or ambiguous/stale evidence fails without deleting the prior recovery point. Zero data repacking reduces temporary work; shared packs may retain unused bytes, which remain part of the next actual quota observation. Hidden versions can remain charged for the provider's one-day lifecycle lag.

## Config and Next-Plan Interfaces

`backup.sh` and `backup-status.sh` take no arguments for production. They accept `--synthetic /tmp/birja-backup-test-*/config` only for the fixed `birja-ops-test` source and local paths. The production config must be root-owned mode 0600 JSON at `/etc/birja/backup.env`; no shell evaluation is used. Root-only password/access-key/secret-key files are referenced, not placed in argv. Production state is `/var/lib/birja/backup`; stable snapshot grouping is host `birja-prod`, tag `birja-db-v1`, source path `/var/lib/birja/backup/stage/backup`. Snapshot contents are `/database.dump`, `/manifest.json`, `/recovery.tar`.

The JSON keys are documented by `CONFIG_KEYS`/`QUOTA_KEYS` in the producer and exercised by the synthetic test fixture. Production adds `approved_host`, `production_enabled`, `access_key_file`, `secret_key_file`; pins Docker/restic install paths, production project and exact destination `s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`. It never lowercases/substitutes the bucket. Recovery tar contains only explicitly selected minimal private recovery files, numbered with their basenames; no recursive directories, images, caches, logs or Redis state are backed up.

Private manifest shape: format, snapshot, release, revision, server_version, pg_dump_version, restic_version, started_utc, finished_utc, archive_sha256, tables[name]={count,sha256}, financial={cash,starting_cash,quantity,cost_basis,fees,cash_delta,negative_cash,fractional_cents,negative_holdings}. A future restore verifier must reproduce the reviewed SQL canonicalization, compare privately and check archive checksum; listability is not restoration proof.

## Deviations from Plan

**[Rule 2 — Critical guard] Explicit fresh provider-usage evidence is required rather than inferring free capacity from logical restic stats.** All implementation files remain within the declared plan. The owner-approved latest-only/resource policy supersedes the earlier generic retention proposal. The test-only callable seam was committed with RED, then replaced completely in GREEN as the plan requires.

JSON at the historically named `backup.env` is a deliberate safe parsing choice. No package/dependency/global installation, architecture change or production operation was needed. The actual local-restic integration test supplements the planned stubs because CLI metadata semantics affect safe rotation.

## Deferred Integration / Remaining Evidence

- **Unattended quota producer is not implemented here.** A later approved provider preflight must atomically refresh root-only JSON quota evidence from current account-visible, hidden-version, unfinished-upload and other-use measurements immediately before each nightly invocation. It must verify actual private bucket, lifecycle/Object Lock settings, free controls and sufficient allowances, and account for concurrent account use and request/wire-byte ceilings. Manually copied constants cannot support unattended operation; evidence older than 300 seconds is rejected. Plans 06-08/09 must implement/rehearse this integration before scheduling/live acceptance; if the selected provider cannot supply trustworthy evidence/controls, retain failure and obtain an owner decision rather than assume US$0 safety.
- Actual PostgreSQL 18 snapshot/dump/restore and financial equality remain 06-03. This plan's PG tools are behavioral stubs; only restic encryption/rotation used a real tool. Initial real off-server retrieval/isolated restore remains mandatory.
- Actual production size, provider byte/request/download use, hard memory enforcement, resource suitability, free-tier sufficiency, bucket privacy/version cleanup and account limits remain unmeasured/unverified. US$0 paid usage is the constraint, not a claimed hard billing guarantee.
- Production host installation/config/credential reads, real backups, provider initialization/deletions, timers, publication, deployment and friends' acceptance remain separately gated. This work did not access `.env`, `/etc/birja/prod.env`, `.aws`, private production rows/auth/balances/logs or the selected remote bucket.

## Self-Check: PASSED

All five declared files exist, RED/GREEN commits resolve, no tracked deletions occurred, and unrelated untracked `.claude/` remains preserved. The orchestrator owns STATE/ROADMAP/handoff updates and final execution advancement.
