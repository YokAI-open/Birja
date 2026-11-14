---
phase: 06-deploy
plan: "07"
subsystem: infra
tags: [rollback, postgres18, tls, recovery, compose, deployment]
requires:
  - phase: 06-14
    provides: Validated inherited locks, durable exact recovery gate and install-once recovery hooks
provides:
  - Immutable retained deployment bundle and guarded stable legacy launcher
  - Separate current SSLContext and actual v0.3.1 verify-full compatibility routing
  - Three-stage same-installed recovery proof with default and exact supplied artifacts
affects: [06-08, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [retained orchestration, validated managed launcher handoff, explicit owner migrator]
key-files:
  created: [deploy/deploy-entrypoint.sh, deploy/db-security.compose.yml]
  modified: [deploy/deploy.sh, deploy/smoke-prod.sh, deploy/tests/test-rollback-db-security.sh]
key-decisions:
  - Keep privileged Compose and migration source in the retained bundle; vary only application source across supported checkouts.
  - Use URL verify-full only for the exact old release; current code retains its shared verified SSLContext policy.
  - Preserve the exact legacy path using installer-managed sparse exclusion and a validated lock-held remove/checkout/finally-restore handoff.
requirements-completed: []
duration: "Approximately 30min resumed execution, excluding the prior interrupted session"
completed: 2026-11-03
---

# Phase 6 Plan 7: Retained Secure Rollback Summary

**Actual v0.3.1 and current application services retain limited roles, verified TLS and complete recoverability on schema 0008 across immutable retained deployment routing.**

## Task Commits

1. **07-01 behavioral RED** — `4d551ac`, preserved from the interrupted execution: actual old-image plaintext session fails the required TLS assertion.
2. **07-01 compatibility contract and overlay** — `e7bbf5d`: actual current/old image services, TLS negatives, retained Git fixture, strict recovery-gate and repeated immutable recovery.
3. **07-02 retained orchestration and smoke** — `d37ce7d`: versioned verified bundle, stable launchers, lock reuse, explicit migrator, fresh exact recovery gate and redacted security checks.

## Delivered Behavior

- The explicitly gated installer copies reviewed orchestration, production Compose, overlay, nginx dependency closure, role/TLS helpers, smoke, shared lock helper and current backend migration context into `/var/lib/birja/ops/releases/<manifest-sha>`. It verifies file hashes and exact inventory, records the attested tested source, and atomically switches `current`. `/usr/local/sbin/birja-deploy` remains the supported entrypoint. No installer was run on the actual host layout.
- Every deployment composes the retained base and retained security overlay; the checked-out application's older Compose never determines database/runtime routing. Backend and scheduler get their own limited URLs and public CA; migration gets the retained current owner context. The exact v0.3.1 checkout gets asyncpg's `ssl=verify-full` plus `PGSSLROOTCERT`; current code receives no URL TLS query and uses its existing verified SSLContext. Main, v0.3.1 and the bundle's tested immutable source are the explicit supported set; historical rollback SHAs are restricted accordingly.
- The installer excludes `/deploy/` from application sparse checkout and installs a fixed root-managed legacy launcher. Git can report that exact tracked launcher as modified; the guard permits only its exact validated contents and that single status record, rejecting all other source changes. Under a kernel-validated held shared descriptor, `checkout_source` removes only this owned launcher, performs ordinary Git checkout and atomically recreates it in `finally`, including checkout failure. During the handoff the path is absent, never an old privileged executable. No force checkout, blanket reset, main-workspace sparse change or host layout migration was used.
- Standalone and parent-held installer locking are supported. The retained runtime acquires the canonical operation lock through the installed recovery helper, inherits FD 9 into Bash, and the actual checkout and recovery gate independently validate its held ownership. Closing a duplicate preserves the parent's lock. Existing reexec, pending-marker, rollback stack and static-release behavior remains present.
- Preflight requires an exact fresh remotely present snapshot plus completed full-restore evidence bound to the actual prechange release/revision and installed tool/config/bundle identity. The command invokes the installed recovery artifact's strict gate before application checkout or live migration. Migration runs through the explicit `migrate` service, retaining 0008 on app rollback. Service-log dumps are removed and migration diagnostics are withheld in favor of step/exit reporting.
- Smoke adds only own-session TLS/restricted non-owner role and backup freshness checks. Its existing placeholder check now executes in the actual backend container, avoiding creation through an old checkout's Compose. Full origin/public smoke was not run: that remains a live action requiring the later approval.

## Verification

- **Complete default artifact:** final runner passed in **113.735s**, including actual retained deploy-gate acceptance and missing/failed/stale evidence rejection, full recovery on populated 0007, populated owner migration to 0008, current app/scheduler service calls with TLS, actual old-image rollback service calls and the final recovery. An earlier complete pass was **106.692s** before the additional direct deploy-gate checks.
- **Exact supplied artifact:** passed in **107.927s**, using archive SHA `443fd82aa4ef034140d2811cddec40bddd45316af17cd99458999a5b7e2f31a5`. Packaging was replaced with a hard failure after producing the selected archive; **default/fallback calls = 0**, selected bytes unchanged. The private outer artifact directory was removed. This interface remains available to 06-08 for its final units/quota artifact.
- Both variants install their selected recovery artifact once. The same immutable hashes and installed launchers perform backup, exact encrypted retrieval, complete isolated restore and strict recovery gate before hardening, after current roles/TLS/0008 and after actual old-image rollback. Recovery children run with the feature checkout denied. Source ownership and teardown remain with this runner; the separate clone is fixed `birja-restore-check`.
- The old image comes from the local v0.3.1 archive, with byte-identical current/old dependency lock and project metadata checked before reuse of the existing dependency image. No fetch or host branch checkout occurs. Actual signup/account creation, rotating/revoked sessions, buy, sell, replay and scheduler prices work under restricted roles; their own sessions report TLS. Missing CA, independently signed CA, hostname mismatch and plaintext are specifically rejected. Current and old schema remains 0008 after rollback.
- Actual private temporary installer/Git tests pass repeated old/current/old ref selection, both stable and legacy entrypoints, unsupported refs, immutable bundle hashes, real rollback history/static selection, inherited installer lock preservation, checkout failure restoration, modified launcher rejection and unheld checkout lock rejection. The final inherited-installer variant passed separately after its bounded lock correction; the database acceptance path did not change.
- Fast recovery input negatives: existing **20** rejection cases plus **6** wrapper option cases, including equals-form duplicate arguments; zero Docker/install/default fallback calls on rejection. Existing five shell regression files were **not edited**: **8/8 + 14/14 + 18/18 + 11/11 + 7/7 = 58/58** assertions pass.
- Restore safety **3/3** passed in **1.020s** during final verification. Four affected embedded Python blocks parse successfully; shell syntax and git whitespace checks pass. Final explicit queries returned **zero containers, networks and volumes for both fixed projects**. No tracked deletion occurred. Fixtures ran serially.

## Deviations and Corrections

**[Rule 3 — Blocking legacy checkout mechanics]** The initial sparse-managed launcher proposal did not itself permit Git checkout: Git detected the existing excluded tracked launcher as modified. The orchestrator authorized the bounded exact-file handoff and narrow status exception within the existing owned files. Real temporary Git tests proved the failure and the correction. No broader regression rewrite or additional subsystem was required.

**[Rule 1 — Fixture correctness]** Initial interrupted fixture code guessed the PG18 HBA path and used Docker archive copy against tmpfs. The corrected runner queries PostgreSQL's actual HBA path and writes private bytes via stdin inside the live container mount namespace, preserving root:999/0640 custody. Service-specific Settings selection and the specific old-driver missing-CA exception were corrected. Temporary fixture failures always ran bounded cleanup; they were not accepted as successful proofs.

**[Rule 2 — Shared-lock correctness]** Installer reuse of an existing parent lock was added through the already reviewed recovery lock interface, preventing recursive flock rejection during the later approved rollout. The actual temporary installer runs under inherited FD 9 and proves the parent still excludes independent contenders afterward.

## TDD Gate Compliance

The preserved behavioral RED `4d551ac` precedes both GREEN commits. A distinct task-02 RED commit was not created during the interrupted implementation; actual Git/gate failures were observed before their corrections, but no retrospective RED commit was fabricated. This is a per-task commit-sequence limitation, not missing runtime acceptance evidence.

## Downstream Handoff and Authority

- 06-08 must document the managed sparse checkout and the sole validated launcher status exception. Retained operational helpers and smoke live at `/var/lib/birja/ops/current/deploy/`; `/srv/birja/deploy/` retains the managed launcher only. The actual installer requires the explicit approved operation and exact tested clean source attestation; installation remains a later live gate.
- Keep the configured backup source release synchronized with the actual successfully deployed source before a new backup/restore. The strict prechange gate intentionally rejects mismatching source identity; new source/config/security material needs new completed recovery evidence. Installing a deployment bundle does not replace the independent installed recovery artifact.
- Local proof is synthetic. Full application/frontend/browser/CI, final artifact units/quota integration and independent security/code review remain in 06-08. Real provider recovery, scheduled execution, production installation/role/TLS rollout and friends' inbox/trade acceptance remain in later approved plans. **DEPL-01/02 remain open**, hence `requirements-completed: []`.
- All operations-ledger policies remain binding: B2 US$0 paid usage, fresh allowance/headroom evidence, latest-only verified replacement, 26h ceiling, bounded resources and independent recovery custody. No provider request, production/private-secret read, actual authentication/trade/email, production deploy/restart, new package/global tool, push, PR or merge occurred. Unrelated `.claude/` remains untouched. The parent owns STATE/ROADMAP updates.
- Consulted official [Git sparse checkout documentation](https://git-scm.com/docs/git-sparse-checkout) and [asyncpg API documentation](https://magicstack.github.io/asyncpg/current/api/index.html); used existing locked dependencies and approved images/tool bytes.

No goal-blocking stub or new security surface outside the plan's deployment/file/config/database threat model was found. No authentication gate occurred.

## Self-Check: PASSED

All five owned implementation/test files and this summary exist. Recorded RED/GREEN commits `4d551ac`, `e7bbf5d` and `d37ce7d` resolve in history in that order. Final default and exact supplied recovery, fast regressions, private temporary launcher/lock tests and explicit fixed-project cleanup are recorded above. Shared planning state is left to the parent orchestrator.
