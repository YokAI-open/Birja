---
phase: 06-deploy
reviewed: 2026-11-06T13:13:08Z
depth: deep
source_base: 8a76a68cf54f46fb0267c9d97f0da91d91b117e1
source_head: 674fcbbcd84d4ff6bf7e88262dfd80576abfc04b
files_reviewed: 39
files_reviewed_list:
  - .github/workflows/ci.yml
  - backend/alembic/env.py
  - backend/app/core/config.py
  - backend/app/db/connection.py
  - backend/app/main.py
  - backend/app/tasks/scheduler.py
  - backend/tests/test_config.py
  - backend/tests/test_config_scheduler.py
  - backend/tests/test_db_connection.py
  - deploy/RUNBOOK.md
  - deploy/backup-manifest.sql
  - deploy/backup-quota.py
  - deploy/backup-snapshot.py
  - deploy/backup-status.sh
  - deploy/backup.sh
  - deploy/configure-db.sh
  - deploy/db-security.compose.yml
  - deploy/db/bootstrap-roles.sql
  - deploy/db/pg_hba.conf
  - deploy/deploy-entrypoint.sh
  - deploy/deploy.sh
  - deploy/init-prod-env.sh
  - deploy/provision-db-tls.sh
  - deploy/recovery-bundle.sh
  - deploy/restore-check.sh
  - deploy/smoke-prod.sh
  - deploy/systemd/birja-backup.service
  - deploy/systemd/birja-backup.timer
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-backup.sh
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-db-config.sh
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-restore-safety.sh
  - deploy/tests/test-rollback-db-security.sh
  - deploy/verify-restore.py
  - docker-compose.ops-test.yml
  - docker-compose.prod.yml
findings:
  critical: 2
  warning: 1
  info: 0
  total: 3
status: issues_found
---

# Phase 06: Code Review Report

**Depth:** deep. **Scope:** explicit current changed-source override, derived from the validated base-to-HEAD Git diff, including incomplete Plan 08. Summary-only file selection was not used. No structural pre-pass was supplied.

## Narrative Findings (AI reviewer)

### Critical Issues

### CR-01: BLOCKER — Completion-based freshness can approve data older than the 26-hour recovery window

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:845-853`; consumers at `:454-469` and `:406-446`.

**Issue:** The logical data point is established by the exported database snapshot, before dumping/uploading/verifying/pruning. The successful record instead sets `epoch` to the final publication time. Ordinary status compares that completion timestamp to 93,600 seconds. The rollout gate checks that timestamp, restore timestamps and the restic snapshot's upload-time timestamp, but never checks the authenticated manifest's earlier `started_utc`. A permitted long job therefore extends the period in which older data is reported fresh. This affects the approved maximum data-loss window, not just the cosmetic displayed time.

**Reproduction/evidence:** An offline direct call to the actual `status()` with matching private attempt/success records, completion age 93,500 seconds and `freshness_seconds=93600`, returned `0` and `step=complete`. With a permitted 3,500-second snapshot-to-completion duration, that data point is 97,000 seconds old (26h56m40s). Source tracing confirms no data-snapshot timestamp is present in the success record or checked by status; the gate likewise accepts upload freshness instead of snapshot freshness. No provider or production data was used.

**Fix:** Record separate data-snapshot/start and completion timestamps. Conservatively use job start, or capture the actual exported-snapshot time. Bind this time into the private manifest and successful state, preserve completion for operational reporting, and enforce the configured RPO against the data time in both status and the remote manifest gate. Fail closed for historical records lacking the required timestamp rather than silently treating completion as the data time.

**Regression:** Advance a fake clock during a successful dump/upload, then check both status and rollout at the 26-hour data boundary while completion remains younger. Assert rejection; also cover UTC/epoch disagreement, future values and matching authenticated remote manifest timestamps.

### CR-02: BLOCKER — Configured local request/download ceilings do not constrain the admitted work

**File:** `/home/YokaiExchange/deploy/backup-quota.py:348-356`; consumers `/home/YokaiExchange/deploy/backup-snapshot.py:530-575` and `:577-601`; operator contract `/home/YokaiExchange/deploy/RUNBOOK.md:207-211`.

**Issue:** The protected controls call these values local work ceilings. Refresh copies them into `request_remaining`/`download_remaining_bytes`, but quota only requires download budget to exceed one staged archive and request budget to exceed a constant 1,000. Neither value is charged, propagated to restic, or checked against a conservative upper bound for the complete operation. Every restic command receives the same fixed download rate and shared timeout regardless of the selected budget. Twenty subprocess calls do not bound HTTP requests to 1,000; one list/check/prune can issue many requests. Independent native inventory calls are bounded at 128, but that bound does not cover restic.

**Reproduction/evidence:** A synthetic call to the actual `Job.quota()` accepted `max_stage_bytes=100000000`, `timeout_seconds=3600`, download budget 100,000,000 bytes and request budget 1,000, with sufficient measured storage/disk reserves. The fixed rate-times-time allowance is 3,774,873,600 bytes, approximately 37 times that configured download ceiling. Metadata reads, checks and pruning can download repository metadata beyond the newly staged archive; restore verification also consumes remote reads. Source inspection shows no later use that enforces either configured ceiling. This is an admitted-work mismatch, not a claim that a particular real account was billed or that exact traffic was measured.

**Fix:** Make admission and execution agree. For downloads, reject a budget smaller than a conservative whole-operation bound, or derive a shared rate/time allowance from the budget with protocol/retry overhead reserved. For requests, derive and validate a conservative total bound from actual inventory/object counts and all command/retry phases, or enforce a shared transport request counter. Include native preflight and repeated restore/gate operations where they share the budget. Abort before upload/deletion when the selected budget cannot cover the bounded work. Keep console caps owner-attested and retain the distinction from provider billing allowances.

**Regression:** Admit a deliberately small but schema-valid local budget and use a synthetic HTTP boundary with many metadata objects/retries to prove work stops or is rejected before exceeding it. Verify cumulative accounting across commands and that shrinking either budget changes the admission/execution decision. A mock asserting subprocess count is not sufficient.

### Warnings

### WR-01: WARNING — Restore and rollout require fresh quota but have no refresh-only producer

**File:** `/home/YokaiExchange/deploy/verify-restore.py:688-689`; `/home/YokaiExchange/deploy/backup-snapshot.py:426` and `:582`; `/home/YokaiExchange/deploy/backup-quota.py:384-395`.

**Issue:** The installed restore and recovery gate consume quota observations with a five-minute lifetime but never refresh them. The only supported installed producer refreshes quota and immediately creates/rotates a new backup, also overwriting the latest backup-attempt record. A valid same-day recovery point therefore cannot be restored using the documented command more than five minutes after its quota observation. A restore that itself takes over five minutes may complete successfully but cannot subsequently pass the rollout gate. Running the only refresh entrypoint replaces the selected backup, making the completed restore refer to an older ID. The accepted 26-hour snapshot window and four-hour recovery target do not imply this five-minute execution window.

**Reproduction/evidence:** The actual quota check rejected the otherwise valid synthetic quota after advancing its observation age by 301 seconds. The restore invokes that check before retrieval, and the gate invokes it again after a completed restore. The installed launchers route quota refresh only through `backup-quota.main`, which unconditionally calls `backup.main(["backup", *args])`. The runbook forbids manually forging fresh observations. This is a source-traced availability problem; no live restore was attempted.

**Fix:** Add a guarded, locked refresh-only preflight and call it before restore and remote recovery-gate work. Preserve existing backup/restore attempt/success identity records during this refresh; it must neither create/forget snapshots nor imply a backup succeeded. Reuse inherited lock handling and revalidate the refreshed budgets against the specific operation.

**Regression:** With a fixed exact snapshot and completed restore evidence, advance the clock past 300 seconds; refresh through the real supported seam and prove restore/gate work without backup, forget or prune calls or rewritten evidence. Also simulate a successful restore longer than five minutes and an inventory-refresh failure that leaves all prior recovery points intact.

## Scope and security coverage

This independent pass traced the privileged launcher and retained manifest verification, sparse Git checkout/legacy handoff, supported-ref routing, kernel-backed inherited lock proof and duplicate lifetime, consistent exporter/dump/manifest flow, exact-ID verification before rotation, private attempt/success publication, isolated restricted restore, bundle inventory/provenance, installed helper paths, B2 authorization/host/redirect/scope/pagination/response/time limits, systemd entrypoint, role grants/HBA, app/scheduler/migrator credential separation and shared TLS policy, and required CI aggregation. Findings above focus on actual consumer behavior across these boundaries. No UI changes: visual review is N/A.

The phase-specific ASVS 5.0 Level 1/STRIDE assessment covered privileged configuration input, credential/privacy handling, TLS and datastore authorization, recovery integrity/evidence, supply-chain provenance and operational failure handling. It is not whole-application ASVS certification. The source review did not identify an additional proved auth bypass, injection or plaintext DB fallback in the changed paths. This does not convert passing tests or static inspection into production acceptance.

Accepted boundaries remain: root-controlled host/config custody; few-friends single-host availability; latest-only retention after successful new-copy verification; no historical recovery promise. Owner-attested console $0 caps and daily checks are the approved policy, not defects and not machine billing proof. Failure after the authorized new-copy verification/deletion commit point does not require an impossible atomic rollback of remote pruning; pre-verification failures must still preserve the old copy.

B2 API shape/POST compatibility and version pagination were checked against primary [authorization documentation](https://www.backblaze.com/apidocs/b2-authorize-account) and [file-version documentation](https://www.backblaze.com/apidocs/b2-list-file-versions). No account or credential was accessed.

## Existing external gate and review limits

**BLOCKED external image gate:** `06-LOCAL-GATES.md` already records unresolved HIGH/CRITICAL image scan results for the exact reviewed images. Keep this as one external supply-chain acceptance gate, separate from the three source findings counted above. Attribution/remediation belongs to the orchestrator's next role; this review did not pull replacement images, rerun scans or assume every reported CVE is exploitable in the application. Plan 08 task 03 and live advancement remain blocked until that gate and these source findings are resolved/reviewed.

The fresh backend 616-test/99.80%/critical-100%, frontend 264-test, audits/build/smoke, and exact-artifact recovery/roles/TLS/old-image rollback results are recorded prior evidence in `06-LOCAL-GATES.md`, not tests rerun or independently certified here. This pass used static cross-file analysis plus two small offline synthetic probes of the actual status/quota consumers. No production/private configuration, provider calls, real auth/trades/email, Docker lifecycle, installation, publication or source edits occurred. Actual CI, provider recovery, timer execution and live friend acceptance remain later gates. Only this report was written; no commit was made.
