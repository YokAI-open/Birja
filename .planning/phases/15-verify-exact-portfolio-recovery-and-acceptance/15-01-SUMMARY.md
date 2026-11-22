---
phase: 15-verify-exact-portfolio-recovery-and-acceptance
plan: "01"
subsystem: testing
tags: [recovery, fixtures, qualification, receipts]
requires:
  - phase: 14
    provides: Qualified current0023 and preserved retained recovery evidence
provides:
  - Authentic installed verifier lifetime for archive-backed cold recovery
  - Finite Phase14/15 outputs and distinct current-only qualification
  - Original phase/suite propagation through durable supervisor and read-only status
affects: [15-02, 15-03, 15-04]
tech-stack:
  added: []
  patterns: [authenticated installed context, finite qualification identity]
key-files:
  created:
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-01-REVIEW.md
  modified:
    - deploy/verify-restore.py
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/test-portfolio-smoke-image.py
    - deploy/tests/run-portfolio-validation.py
    - deploy/tests/run-portfolio-campaign.py
    - deploy/tests/test-portfolio-validation-contracts.py
key-decisions:
  - Use qualification_phase for numeric request identity, preserving existing state.phase execution-stage semantics.
  - Admit only the exact Phase15 canonical synthetic archive in the existing verifier path validator.
requirements-completed: []
requirements-addressed: [PSAFE-04, PSAFE-05, PSAFE-06]
duration: about 8 min
completed: 2026-11-22
---

# Phase15 Plan01: Reproducible Recovery Tooling

**Archive-backed cold checks now use the selected installed verifier and retained
sources; finite Phase15 campaigns preserve earlier proofs and cannot claim a
full result from current-only execution.** All three tasks complete.

| Task | Commit | Actual verification |
|---|---|---|
|1 Installed consumer lifetime|c640789|25 smoke contracts pass,5.911s; Python syntax and diff checks pass|
|2 Finite phase/suite/output selection|3ddc579|38 validation contracts pass,8.810s; syntax/diff checks pass|
|3 Durable original phase propagation|966c10c|42 validation contracts pass,9.037s; syntax/diff checks pass|

Task3's preliminary existing38-contract check also passed8.305s before adding
the four new supervisor cases. No database, Docker, browser, scan, dependency,
provider or production operation was run. Existing process contracts use only
bounded owned stdlib child processes; command doubles are not financial proof.

## Resulting Interfaces

- `installed_recovery_verifier(archive, archive_sha)` authenticates and installs
  the selected v4archive into an owned temporary host, loads its actual verifier,
  and keeps adjacent retained sources alive throughout canonical/restored/verify.
  Exact `manifest`/`quarantined` arguments and non-cold default loader remain.
- Runner `--phase {14,15}` defaults14. `recovery-current` requires15, selects
  `/tmp/birja-phase15-proof/recovery.tar.gz`, executes current0023-cold and validates
  the actual returned authority triple. Its result keeps whole7/final-CI false.
- Default `recovery` retains all seven operations and alone emits the full
  `same_archive_final_ci=true` marker after passing exact authority parity.
- Requests persist `qualification_phase`, suite and selected archive; workers
  derive preflight/child/status behavior from that original identity. Legacy
  format1 requests without the field remain Phase14 and are never rewritten.
  Resume/status remain read-only. Earlier archive hashes and source/image guards
  remain enforced, including after operation failure.

Actual dry-runs returned the Phase15 single current stage and the default
Phase14 seven-stage graph with their correct exclusive canonical paths.

## Review and Limits

Independent bounded six-file static review07e9517..966c10c is clean:
**0 blockers,0 warnings**. See15-01-REVIEW.md. The reviewer ran no tests/services
and claims no restore or CI result. Current results are tooling contracts only;
actual restored financial retries and the fresh matching archive belong to02/03.
No existing historical source hash, schema/ACL, application, image version,
dependency, issue35 scope/expiry or Phase7 obligation changed.

## Deviations from Plan

**[Rule2 — Missing critical interface] Exact Phase15 archive admission.**
During Task2, the existing verifier's synthetic-path validator was found to
admit canonical12/13/14 archives but refuse15. The parent explicitly authorized
adding only `/tmp/birja-phase15-proof/recovery.tar.gz` to that finite list and
adding the file to01's manifest. An offline contract checks exact15 acceptance
and16 refusal. No arbitrary path or production admission was introduced.
Included in3ddc579. No architectural, package or authentication checkpoint.

## Readiness

Ready for15-02's genuine active fill/oracle and restored-only retries. All three
whole Phase15 requirements remain pending until integrated proof and independent
goal verification. Root owns globalSTATE/ROADMAP/requirements updates; this
executor intentionally did not alter them. Work remains local. Unrelated
untracked.claude/ is untouched.

## Self-Check: PASSED

All six modified source/contract files and the independent review exist.
All three recorded task commits exist, actual contract runs exit0, and
`git diff --check` passes. No unexplained tracked deletion or product stub.
