---
phase: 06-deploy
fixed_at: 2026-11-06T13:25:33Z
review_path: .planning/phases/06-deploy/06-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

Three source findings were addressed in isolated per-finding commits. Each
changes operational logic: **fixed: requires human verification** applies to
all three, pending the orchestrator's independent re-review. `all_fixed` counts
applied fixes, not final Phase 08 acceptance. The existing external image
HIGH/CRITICAL gate remains unresolved; no phase advancement is implied.

## Fixed Issues

### CR-01: Enforce the recovery window against data time

**Status:** fixed: requires human verification
**Files modified:** `deploy/backup-snapshot.py`, `deploy/tests/test-deploy-prerequisites.py`
**Commit:** `0a68575`

The conservative job-start epoch and canonical UTC are recorded separately from
completion in private success state and the authenticated manifest. Status
requires identical successful attempt/state records and checks the data age.
The exact remote gate checks the same data age and binds remote manifest data
epoch, data UTC and start UTC to local success. Missing historical data fields,
future times, UTC/epoch contradictions and data/completion ordering fail closed.
Completion remains available for operational reporting.

Regressions reject 97,000-second-old data while completion is only 93,500
seconds old, inconsistent/future/missing timestamps, and a changed authenticated
remote data epoch with its manifest hash updated in synthetic restore evidence.
Existing exact-ID, remote presence, binding, failed-attempt and cleanup checks
remain intact.

### CR-02: Make selected budgets constrain admitted work

**Status:** fixed: requires human verification
**Files modified:** `deploy/backup-snapshot.py`, `deploy/backup-quota.py`, `deploy/tests/test-backup.sh`, `deploy/RUNBOOK.md`
**Commit:** `80a7a2f`

The request setting now explicitly governs native inventory HTTP requests,
counted at the actual opener boundary, including failed attempts and all
pagination/refresh calls. Native response bytes and a per-request protocol
allowance are cumulative. The same API object, consumed bytes and operation
start are retained through nightly preflight into the actual backup consumer;
refreshing cannot replenish these counters. Smaller protected controls can
only tighten an existing operation's native budgets. Native transport retains
its independent 128-call/120-second/2-MB-response limits and prohibits redirects.

Restic does not expose its HTTP count. Rather than asserting a false total HTTP
ceiling, the operator contract states its separate enforced limits: 20 tool
calls, two connections, two S3 retries, stuck-request timeout and one shared
operation deadline. Download admission deducts native accounted bytes and
64 KiB per possible process, then derives a fixed KiB/s rate from twice
rate times (whole-operation timeout plus 20 one-second process bursts), capped
at 1 MiB/s. Each restic command receives that rate and shares the deadline.
Insufficient allowance fails before remote restic work. These conservative
work allowances are not exact wire measurements, provider remaining balances
or a guarantee about owner-attested console billing controls.

Regressions exercise actual native HTTP adapter -> inventory -> refreshed
quota -> real Job admission; a second refresh consumes cumulative requests;
exhaustion blocks the opener; smaller native byte allowance blocks before HTTP;
a smaller download budget reduces the actual restic CLI rate; an uncovered
budget blocks before restic invocation. Existing storage headroom and
create/verify-before-delete tests remain passing.

### WR-01: Refresh inventory without replacing recovery evidence

**Status:** fixed: requires human verification
**Files modified:** `deploy/backup-snapshot.py`, `deploy/verify-restore.py`, `deploy/tests/test-deploy-prerequisites.py`, `deploy/RUNBOOK.md`
**Commit:** `ea4cd28`

Restore and the exact remote recovery gate call a refresh-only preflight before
remote work, reusing and validating their already-held operation lock. Only
the protected configuration's quota observation is persisted. This path never
creates, forgets or prunes snapshots and never rewrites completed backup or
restore evidence. Budgets are revalidated for the actual Job. Freshness is
required at admission; subsequent commands retain the original rate and shared
deadline rather than imposing a five-minute maximum restore duration.

The real-consumer regression starts with a 301-second-old observation, performs
an actual refresh-only synthetic restore whose wall clock advances 301 seconds
within a 3,600-second policy, and runs the exact gate after another 301 seconds.
All four backup/restore records remain byte-identical through gate refresh.
Remote commands are exactly snapshots, restore, snapshots, dump. Inventory
failure adds no remote call and preserves all prior evidence/recovery points.

## Verification

- Full prerequisite contracts: 15 passed; focused evidence: 8 passed after
  setting the long-restore regression's explicit 3,600-second policy.
- Final backup contracts: 25 passed in 51.619 seconds, including real approved
  restic 0.19.1 local encryption/latest-only rotation and old-copy preservation.
- Restore safety: 4 passed in 1.063 seconds.
- Supplied-input rejection contracts: 20 rejections, zero Docker/package/install
  calls (expected argparse diagnostics are part of negative inputs).
- Affected Python AST/ruff lint/format, Bash checks and git whitespace checks
  passed. No new dependency or bundle member was introduced.
- Final focused synthetic PostgreSQL/recovery integration passed in 82.243
  seconds using the existing approved image/restic. The newly packaged
  199,639,040-byte artifact SHA was
  `6da48bcd909ab12c899f7e68ee6d6afb4e8346c4a5ce86a931ece0cd76a4a373`.
  Installed backup/retrieval/restore, concurrent-writer snapshot consistency,
  exact equality/invariants/identities, row/manifest/FK/index/sequence negatives,
  generated IDs, encrypted-checksum failures and old-checkout isolation passed.
  This temporary default artifact was cleaned up; it is not the orchestrator's
  final retained/supplied artifact or a roles/TLS/old-image rollback replay.
- Explicit post-run queries found zero containers, networks and volumes for
  `birja-ops-test`, `birja-restore-check` and `birja-rollback-test`.

The pre-fix reproductions are recorded in the independent source review. No
separate new RED commit was made and no retrospective RED history is claimed.
Per-finding source changes were re-read and checked before their commits.
Application/frontend/full e2e suites were not repeated for these operations-only
changes. No provider/private production access, real auth/trade/email, image
pull, installation, push or deployment occurred. The orchestrator retains final
artifact replay, external image attribution, independent review and later live
acceptance gates.

---

_Fixer: gsd-code-fixer; iteration 1._
