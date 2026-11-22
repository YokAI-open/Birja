---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: standard
reviewed_commit: 2ef1f58abc376c6b587e936d98e985809a7246f9
files_reviewed: 3
files_reviewed_list:
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-portfolio-smoke-image.py
coverage: complete
rechecked_finding: CR-02
source_disposition: resolved
integrated_cold_verification: pending
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 12 CR-02 independent repair review

## Narrative Findings (AI reviewer)

CR-02 is resolved in the reviewed source commit. No new BLOCKER or WARNING was established. All three complete file blobs were read directly from immutable commit `2ef1f58abc376c6b587e936d98e985809a7246f9`, independently of the current main worktree. The original finding and `/tmp/phase12-cr02-REVIEW-FIX.md` were also read.

The former workstation-only cached image ID and alternate Smoke.Dockerfile overlay are removed. `build_current_runtime` obtains the exact committed backend Git archive, verifies its complete extracted inventory before and after Docker's build, and builds the declared Dockerfile `runtime` target. Dirty backend source, changed HEAD, failed build/inspection, changed extracted source and mismatched immutable image metadata refuse execution. The image receives the committed source label; its content ID, Config, RootFS, application tree and context digest use the existing binding API. A clean runner can acquire the declared runtime through this factory without a previously seeded workstation runtime. Current commit/tree lookup works with a normal checked-out commit; the surrounding retained-source campaign already requires full history and CI retains its full-history checkout.

The smoke dispatch calls the factory before provisioning its database, records its current0017 image binding beside the selected archive, and uses the immutable image ID for every client. Each transport invocation still verifies the image, current source and exact archive. Cross-reference review of `portfolio-sources.py`, `run-portfolio-validation.py`, `verify-restore.py` and the declared backend Dockerfile found compatible binding fields and archive membership: the modified smoke helper remains in `PORTFOLIO_PAYLOAD_V1`, and the unchanged runner authenticates packaged helper bytes and subsequently created image records. The new offline test is wired through the existing CI unittest entrypoint; it is not an operational recovery archive dependency.

The cold path retains its independent pre-backup oracle, encrypted restic repository, fixed payload hashes, source server destruction before new-server creation, authenticated recovered archive, quarantined restored authority and same-root comparison through the migration reader. The repair does not remove these checks or weaken the existing security/coverage gates. No additional packages or alternate runtime bases are introduced.

The six new regressions exercise clean-image dispatch, required declared build and immutable-ID inspection, pre-build dirty refusal, failed-build refusal without image adoption, HEAD/context mutation, and source-label/RootFS substitution. The existing CI suite's complete blob was checked as well as its added loader, so this assessment is not based solely on passing test counts.

## Verification boundary

This is an independent source recheck, not an actual cold-recovery result. The fixer's reported offline and actual Docker image receipts were reviewed as evidence descriptions; this reviewer ran no tests, Docker commands, databases, providers or production operations. No source files or commits were changed. Parent integration and a source-bound actual current0017 encrypted cold proof remain required before final phase verification; this report does not claim they passed.
