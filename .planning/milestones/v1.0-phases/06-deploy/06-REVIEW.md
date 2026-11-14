---
phase: 06-deploy
reviewed: 2026-11-06T13:13:08Z
rereviewed: 2026-11-06T13:33:35Z
depth: deep
source_base: 8a76a68cf54f46fb0267c9d97f0da91d91b117e1
source_head: 674fcbbcd84d4ff6bf7e88262dfd80576abfc04b
rereview_head: a5540c34c05c79e34b6b4b17a170ed74c999f9ae
rereview_source: c8e23fd400844e2d3a834229afb3b514bc1ecc2e
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
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 06: Code Review Report

**Depth:** deep. **Scope:** explicit current changed-source override, derived from the validated base-to-HEAD Git diff, including incomplete Plan 08. Summary-only file selection was not used. No structural pre-pass was supplied.

**Current result after final focused independent re-review at `a5540c3`: zero active source findings.** CR-01, CR-02 and WR-01 are resolved, including CR-01's authorization-boundary follow-up. CR-02 uses the explicitly approved revised request-budget contract. Counts above describe active source findings. The initial findings and intermediate re-review below are retained as history; final evidence follows at the end. The external image gate remains independently pending; `clean` does not mean Plan 08 or deployment acceptance is complete.

## Narrative Findings (AI reviewer)

### Critical Issues

### CR-01: BLOCKER — Completion-based freshness can approve data older than the 26-hour recovery window

**Re-review disposition:** resolved by `0a68575` plus final boundary correction `c8e23fd`; intermediate gate-boundary case preserved below.

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:845-853`; consumers at `:454-469` and `:406-446`.

**Issue:** The logical data point is established by the exported database snapshot, before dumping/uploading/verifying/pruning. The successful record instead sets `epoch` to the final publication time. Ordinary status compares that completion timestamp to 93,600 seconds. The rollout gate checks that timestamp, restore timestamps and the restic snapshot's upload-time timestamp, but never checks the authenticated manifest's earlier `started_utc`. A permitted long job therefore extends the period in which older data is reported fresh. This affects the approved maximum data-loss window, not just the cosmetic displayed time.

**Reproduction/evidence:** An offline direct call to the actual `status()` with matching private attempt/success records, completion age 93,500 seconds and `freshness_seconds=93600`, returned `0` and `step=complete`. With a permitted 3,500-second snapshot-to-completion duration, that data point is 97,000 seconds old (26h56m40s). Source tracing confirms no data-snapshot timestamp is present in the success record or checked by status; the gate likewise accepts upload freshness instead of snapshot freshness. No provider or production data was used.

**Fix:** Record separate data-snapshot/start and completion timestamps. Conservatively use job start, or capture the actual exported-snapshot time. Bind this time into the private manifest and successful state, preserve completion for operational reporting, and enforce the configured RPO against the data time in both status and the remote manifest gate. Fail closed for historical records lacking the required timestamp rather than silently treating completion as the data time.

**Regression:** Advance a fake clock during a successful dump/upload, then check both status and rollout at the 26-hour data boundary while completion remains younger. Assert rejection; also cover UTC/epoch disagreement, future values and matching authenticated remote manifest timestamps.

### CR-02: BLOCKER — Configured local request/download ceilings do not constrain the admitted work

**Re-review disposition:** resolved by `80a7a2f`, under the approved native-request-only contract and separately bounded restic work described below.

**File:** `/home/YokaiExchange/deploy/backup-quota.py:348-356`; consumers `/home/YokaiExchange/deploy/backup-snapshot.py:530-575` and `:577-601`; operator contract `/home/YokaiExchange/deploy/RUNBOOK.md:207-211`.

**Issue:** The protected controls call these values local work ceilings. Refresh copies them into `request_remaining`/`download_remaining_bytes`, but quota only requires download budget to exceed one staged archive and request budget to exceed a constant 1,000. Neither value is charged, propagated to restic, or checked against a conservative upper bound for the complete operation. Every restic command receives the same fixed download rate and shared timeout regardless of the selected budget. Twenty subprocess calls do not bound HTTP requests to 1,000; one list/check/prune can issue many requests. Independent native inventory calls are bounded at 128, but that bound does not cover restic.

**Reproduction/evidence:** A synthetic call to the actual `Job.quota()` accepted `max_stage_bytes=100000000`, `timeout_seconds=3600`, download budget 100,000,000 bytes and request budget 1,000, with sufficient measured storage/disk reserves. The fixed rate-times-time allowance is 3,774,873,600 bytes, approximately 37 times that configured download ceiling. Metadata reads, checks and pruning can download repository metadata beyond the newly staged archive; restore verification also consumes remote reads. Source inspection shows no later use that enforces either configured ceiling. This is an admitted-work mismatch, not a claim that a particular real account was billed or that exact traffic was measured.

**Fix:** Make admission and execution agree. For downloads, reject a budget smaller than a conservative whole-operation bound, or derive a shared rate/time allowance from the budget with protocol/retry overhead reserved. For requests, derive and validate a conservative total bound from actual inventory/object counts and all command/retry phases, or enforce a shared transport request counter. Include native preflight and repeated restore/gate operations where they share the budget. Abort before upload/deletion when the selected budget cannot cover the bounded work. Keep console caps owner-attested and retain the distinction from provider billing allowances.

**Regression:** Admit a deliberately small but schema-valid local budget and use a synthetic HTTP boundary with many metadata objects/retries to prove work stops or is rejected before exceeding it. Verify cumulative accounting across commands and that shrinking either budget changes the admission/execution decision. A mock asserting subprocess count is not sufficient.

### Warnings

### WR-01: WARNING — Restore and rollout require fresh quota but have no refresh-only producer

**Re-review disposition:** resolved by `ea4cd28`.

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

**BLOCKED external image gate:** `06-LOCAL-GATES.md` already records unresolved HIGH/CRITICAL image scan results for the exact reviewed images. Keep this as one external supply-chain acceptance gate, separate from source finding counts. Attribution/remediation belongs to the orchestrator's next role; this review did not pull replacement images, rerun scans or assume every reported CVE is exploitable in the application. Plan 08 task 03 and live advancement remain blocked until the external gate and other acceptance work are complete.

The fresh backend 616-test/99.80%/critical-100%, frontend 264-test, audits/build/smoke, and exact-artifact recovery/roles/TLS/old-image rollback results are recorded prior evidence in `06-LOCAL-GATES.md`, not tests rerun or independently certified here. This pass used static cross-file analysis plus two small offline synthetic probes of the actual status/quota consumers. No production/private configuration, provider calls, real auth/trades/email, Docker lifecycle, installation, publication or source edits occurred. Actual CI, provider recovery, timer execution and live friend acceptance remain later gates. Only this report was written; no commit was made.

## Independent fix re-review — `bd96d81..ea4cd28` at HEAD `f0fae41`

Read the full `06-REVIEW-FIX.md` and actual six-file source/test/runbook diff, then traced the resulting runtime consumers. Re-review scope is the fixes and their cross-file interactions within the original 39-file scope, including installed adjacent-module imports, unchanged authenticated bundle closure, shared lock/deadline inheritance, config identity and evidence preservation. This is not a repeat of the full original test run or a final supplied-artifact acceptance claim.

### Historical iteration-1 CR-01: BLOCKER — The remote gate does not recheck data freshness at the authorization boundary

**Current disposition:** resolved by `c8e23fd`; the account below preserves the pre-correction finding and reproduction.

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:400`, `:408-454`.

The new separate integer `data_epoch`/canonical UTC, completion ordering and authenticated manifest binding correctly close the original completion-versus-data confusion. Missing historical fields, contradictory UTC and future data times now fail closed. However, the gate invokes `data_time(backup, c)` before its refresh-only inventory and remote snapshot/manifest requests. Its `now` variable is likewise captured before those operations. After the requests it checks only equality of manifest/local data time, then returns `recovery_verified=True`. A valid point can expire while those operations run and still authorize the subsequent deployment.

**Independent offline reproduction:** Used the actual existing Evidence fixture to prepare private, mutually matching backup/restore state and authenticated manifest, then called the actual `recovery_gate()`. Set entry data age to 93,590 seconds and advanced a fake wall clock by 20 seconds inside the refresh boundary; only remote/host boundaries were intercepted. Output: `recovery_verified=True data_age_at_return=93610 maximum=93600`. No Docker, provider or private production access occurred. The refresh's own native ceiling permits up to 120 seconds, before additional remote checks, so this is within supported operation durations.

**Minimal fix:** After all refresh/remote manifest validation and immediately before returning authorization, rerun `data_time(backup, c)` using a newly read current wall clock. Preserve the early check to avoid unnecessary work. Reject if the selected recovery point expired during the gate. A current-time check should also govern any remaining time-sensitive authorization predicates rather than reusing the pre-I/O `now`.

**Regression:** Begin with data ten seconds inside the recovery window, advance wall time twenty seconds during refresh and separately during manifest retrieval, and require rejection in both cases. Include a positive case that stays inside the window and retain exact UTC/manifest/epoch matching tests. Ordinary status already checks current time without this intervening I/O.

### Resolved CR-02: Native request accounting and conservative restic admission

The orchestrator explicitly approved a revised technical contract: `local_request_budget` governs native inventory HTTP calls; restic HTTP count is unobservable and is bounded separately by tool calls/retries/connections/deadline. Re-review applies that actual contract rather than requiring an invented total HTTP counter. The runbook now states that distinction and makes no provider-remaining or exact-wire guarantee.

Native request/response accounting is enforced at the actual opener/read boundary. Counts include failed attempts and pagination; a shared `_inventory_api` is retained in the config through `backup.main(..., config=c)`, and subsequent refresh cannot replenish its counters or relax selected budgets. `_operation_started` is also carried into the backup Job. Restic admission deducts consumed native bytes and process reserve, derives an actual CLI download rate from the remaining selected budget and conservative timeout/burst allowance, and uses that fixed rate across commands with the shared deadline. Admission rejects insufficient allowance. The reviewed tests exercise actual API adapter -> inventory -> refreshed config -> actual Job admission, cumulative refresh exhaustion and actual CLI rate changes, rather than relabeling subprocess count as HTTP count. No additional proved defect in those changes was found under the approved bounded-work contract.

### Resolved WR-01: Refresh-only recovery paths preserve exact evidence

Both restore and the exact remote gate now invoke `Job.refresh_quota(lock)` under the validated already-held lock, independently of the nightly backup producer. The helper imports only the adjacent installed `backup-quota.py`, already in the mandatory authenticated CORE bundle, updates the protected quota config and checks actual Job admission without backup/forget/prune or backup/restore identity publication. It excludes internal API/deadline objects from persisted JSON. The stable config binding excludes volatile quota observations while retaining safety policy/material identity. Restic checks freshness at admission and retains the original deadline/rate during longer operations. The regression explicitly runs a delayed refresh and a long restore, then refreshes the gate and verifies unchanged completed evidence and exact remote command sequence. Inventory failure blocks further remote work. CR-01's remaining final-boundary check is separately active above.

### Re-review limits and external gate

The fix report records 25 backup, 15 prerequisite, four restore-safety, 20 input-rejection checks and one 82.243-second PostgreSQL/encrypted-recovery run; these are execution evidence supplied by the fixer, not suites rerun by this re-review. This pass read their new assertions and ran the additional minimal gate-boundary probe above. No image changed, no scan was repeated, and the known external image HIGH/CRITICAL gate remains open. Final retained/supplied artifact recovery and roles/TLS/old-image rollback replay remain orchestrator acceptance work after the active source finding is fixed. Only REVIEW.md was edited; no source, state or commit change was made.

## Final focused re-review — source `c8e23fd`, HEAD `a5540c3`

**Result: CR-01 resolved; zero active source BLOCKERs or WARNINGs.** Read the complete two-file correction and its actual gate regression. The gate now captures `authorized_at` after inventory refresh, remote snapshot lookup, manifest retrieval and authenticated manifest/time binding. Immediately before granting authorization it checks data age/canonical timestamps/ordering with this new current time and rechecks backup completion, restore start/completion and remote snapshot freshness. The earlier admission checks remain. No I/O follows the final freshness check before the result is returned, and the change introduces no new routing, privilege or bundle dependency.

Independently ran the single actual-consumer test `Evidence.test_gate_rechecks_exact_remote_presence_and_all_bindings` through a stdlib unittest suite: **one test passed in 0.296 seconds**. Its new subcases advance the clock 20 seconds during inventory refresh and separately during manifest retrieval, taking data age from 93,590 to 93,610 seconds; both now reject. Positive cases at 93,599 and exactly 93,600 seconds pass, matching the approved inclusive maximum. Existing identity, authenticated-manifest, remote-presence, failed-attempt and historical-data checks in that test also passed. No broader fixture run was needed for this focused correction, and none is claimed.

CR-02 and WR-01 remain resolved under the previously reviewed implementation/approved bounded-work contract. This final pass only revisited the bounded correction and affected invariant; it did not redo the 39-file original review. The external image gate, final retained/supplied artifact replay and later provider/timer/CI/live acceptance remain separate outstanding work. No Docker/provider/private access, source edit or commit occurred; only this report was updated.
