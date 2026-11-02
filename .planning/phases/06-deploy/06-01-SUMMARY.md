---
phase: 06-deploy
plan: "01"
subsystem: infra
tags: [backup, restic, backblaze-b2, provenance, operations]
requires:
  - phase: 05-portfolio-and-history
    provides: Verified application merged into develop at 8a76a68
provides:
  - Owner-approved backup operating policy and exact B2 destination
  - Signed-checksum-verified restic 0.19.1 for isolated local testing
  - Preserved feature branch and explicit production authority boundaries
affects: [06-02, 06-03, 06-08, 06-09, 06-12, 06-13]
tech-stack:
  added: [restic 0.19.1 (isolated /tmp tooling only)]
  patterns: [Create-before-delete verified snapshot rotation, pinned signed executable acquisition]
key-files:
  created: [.planning/phases/06-deploy/06-OPERATIONS-DECISIONS.md]
  modified: []
key-decisions:
  - "Backblaze B2 S3 free tier only; US$0 paid usage; Birja-backup/prod at s3.eu-central-003.backblazeb2.com."
  - "Nightly 03:00 UTC with up to 15 minutes jitter; maximum data loss/freshness 26 hours; recovery target 4 hours."
  - "Keep one verified completed snapshot; verify replacement before removing previous; failures preserve previous."
  - "Owner checks daily; password/config/database/CA recovery material held independently in off-server password manager."
  - "Official restic 0.19.1 Linux amd64 approved only for verified isolated local tooling; host installation remains gated."
patterns-established:
  - "Count old/new coexistence, repack overhead, hidden versions and unfinished uploads in quota safety."
  - "Acquisition authority does not authorize storage access, production installation, publication or deployment."
requirements-completed: ["DEPL-01", "DEPL-02"]
duration: 61min
completed: 2026-11-02
---

# Phase 6 Plan 1: Backup Operating Contract and Provenance Summary

**Approved B2 latest-only recovery policy and signed-checksum-verified restic 0.19.1 local tooling on the prepared deployment feature branch.**

## Performance

- **Started:** 2026-11-02T10:33:55Z (Task 1 commit timestamp; earlier task preparation time was not recorded)
- **Completed:** 2026-11-02T11:34:14Z (final task commit verification)
- **Duration:** Approximately 61 minutes wall time including owner checkpoint discussion; not active CPU time
- **Tasks:** 3/3
- **Files:** One operations ledger plus this summary; local binary/verification material outside the repository

## Accomplishments

- Preserved `feature/phase-06-deploy` from updated develop `8a76a68cf54f46fb0267c9d97f0da91d91b117e1`; existing planning and unrelated `.claude/` survived.
- Completed both explicit owner checkpoints using actual answers; no auto-approval or repeated provider selection.
- Recorded exact-case bucket `Birja-backup`, endpoint `s3.eu-central-003.backblazeb2.com`, prefix `prod`, free-only budget, schedule, recovery targets, retention and custody.
- Verified and installed the approved official executable only at `/tmp/birja-test-tools/restic-0.19.1/restic`.

`requirements-completed` above reproduces the plan's required coverage IDs for tooling. It does **not** claim DEPL-01 or DEPL-02 is satisfied. Both requirements remain pending their actual live acceptance; no requirement checkbox should be completed from this policy/provenance plan.

## Task Commits

1. **06-01-01: Prepare implementation feature branch** — `90f4d79` (docs)
2. **06-01-02: Record approved backup policy and custody** — `a348d25` (docs; final destination/policy acceptance)
3. **06-01-03: Verify approved local restic acquisition** — `89df24d` (docs)

Earlier policy discussion commits retained: `0dd33ff`, `4a5a0d3`, `b29dfec`, `385f16f`, `4f86fe2`, `0570828`, `b27b282`. Separate planning commit `57ba625` belongs to the orchestrator. No previous task or branch creation was repeated.

## Files Created/Modified

- `.planning/phases/06-deploy/06-OPERATIONS-DECISIONS.md` — non-secret operating choices, historical checkpoint discussion, exact acquisition approval, verification results and pending authority.
- `/tmp/birja-test-tools/restic-0.19.1/` — approved ephemeral executable, official compressed archive, signed checksum files, public key and isolated GPG home; not committed.

## Decisions Made

The owner selected B2's S3 API, US$0 paid use, maximum 26-hour data loss and freshness, 4-hour recovery target, and nightly 03:00 UTC plus up to 15 minutes jitter. The selected repository address is `s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`; it has not been contacted.

The latest explicit retention instruction supersedes multi-version retention and disabled-pruning defaults: keep one verified completed recovery point, upload/verify the replacement before scoped deletion/prune, preserve the previous copy on failure, serialize operations and protect quota/headroom. No actual provider deletion is authorized by this policy record. Minimal database/config recovery and efficient checks must avoid unnecessary nightly full downloads; initial real retrieval/restore is mandatory.

The owner stores password/storage/database/CA recovery material independently in an off-server password manager, includes required config in encrypted recovery material, and checks backup status daily. No credentials were supplied, read or written.

## Verification

- Plan checks passed: correct feature branch, develop ancestor, `git diff --check`; task commits contain no deletions.
- Official [installation documentation](https://restic.readthedocs.io/en/stable/020_installation.html) and [v0.19.1 release](https://github.com/restic/restic/releases/tag/v0.19.1) independently checked before execution.
- Official `SHA256SUMS.asc` verification returned exit 0, GOODSIG and VALIDSIG for expected full fingerprint `CF8F18F2844575973F79D4E191A6868BD3F7A907`. Signature time: 2026-07-05 07:59:26 UTC. Isolated keyring has no web-of-trust certification; expected fingerprint was explicitly pinned.
- Compressed artifact SHA-256 matched the unique signed entry before extraction/execution: `f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c` (10,107,515 bytes).
- Extracted executable SHA-256: `20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639` (30,941,346 bytes). Directory, executable and GPG home modes: 0700.
- Exact executable `version` returned exit 0: `restic 0.19.1 compiled with go1.26.4 on linux/amd64`. No repository initialization or backup command ran.
- Stub scan found no TODO/FIXME/placeholder implementation. No runtime/application file changed; application suites were not run for these documentation/approval tasks. No new network endpoint, auth path, schema or private data surface was implemented.

## Deviations from Plan

No unapproved deviation. Owner's explicit latest-only/resource-limit instructions replace earlier retention proposals. The owner approved local executable acquisition only; production host installation is deliberately pending. The approved binary was verified/acquired within that scope.

## Issues Encountered

Sandbox DNS blocked the initial public GitHub download; approved network escalation succeeded. GPG import attempted an unavailable agent socket; public signature verification succeeded with `--no-autostart`, without starting a service or weakening verification. No authentication gate or package-manager install occurred.

## Next Plan Readiness

Ready for 06-02 local implementation/synthetic tests using the exact verified executable path or a per-command test PATH. `/tmp` tooling is ephemeral; reacquisition/replacement must repeat verification. The orchestrator owns STATE/ROADMAP/handoff updates after this committed summary.

Production host installation; bucket privacy/Object Lock/lifecycle/version cleanup; actual free-tier controls, usage and resource ceilings; storage access; real backups/retrieval/isolated restore; actual nightly timer proof; role/TLS rollout; friends' inbox/trade checks; push/PR/merge/release/deploy remain separately gated. No live result was inferred from local provenance checks.

## Self-Check: PASSED

Verified the ledger and local executable exist, all three task commits resolve, plan branch/ancestry/whitespace checks pass, and no tracked deletion occurred. Unrelated untracked `.claude/` remains preserved.
