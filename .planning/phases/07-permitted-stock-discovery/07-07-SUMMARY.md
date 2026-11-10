---
phase: 07-permitted-stock-discovery
plan: "07"
subsystem: infra
tags: [calendar, dependencies, provenance, approval, uv]
requires:
  - phase: 07-05
    provides: Product-specific fail-closed admission contracts
provides:
  - Official calendar package/source review and exact eight-package prospective resolution
  - Explicit owner approval before project lock mutation or local installation
affects: [07-08, 07-13]
tech-stack:
  added: []
  patterns: [Exact dependency resolution approval before installation]
key-files:
  created:
    - .planning/phases/07-permitted-stock-discovery/07-PACKAGE-REVIEW.md
  modified:
    - .planning/STATE.md
key-decisions:
  - "Owner approved the exact eight-package resolution for project uv lock changes and isolated local installation/testing; provenance limitations and all runtime/security gates remain."
patterns-established:
  - "Unsupported legitimacy protocol remains ASSUMED after bounded explicit approval; approval is not a safety certification."
requirements-completed: []
duration: 5min continuation; prior review recorded in 9279c01
completed: 2026-11-10
---

# Phase 7 Plan 7: Calendar Dependency Review Summary

**Official package/source evidence and an exact eight-package resolution now have explicit owner approval for Plan 08's local lock and installation work.**

## Performance

- Completion date: 2026-11-10.
- Continuation: approximately 5 minutes; time waiting for owner approval excluded.
- Tasks: 2/2, including the blocking human checkpoint.
- Files: review packet plus scoped summary/state/roadmap records; no application, lock or image changes.

## Accomplishments

- Preserved Task 1's official PyPI and tagged-source identities, prospective
  wheel-only resolution and documented limitations without repeating its review.
- Recorded the actual reply **“Approve reviewed dependencies and continue local
  execution”** to the question naming all eight exact versions and its limitations.
- Kept installation separate in Plan 08, which must compare the actual lock to
  this packet before installing, preserve existing versions, use wheels only,
  and prove real image imports/calendar behavior and strict security scans.

## Task Commits

1. **07-07-01: Prepare a concrete package and transitive review** — `9279c01`.
2. **07-07-02: Approve the reviewed calendar package** — `fd887da`.

## Reviewed Resolution and Source Identities

Approved versions: exchange-calendars 4.13.2, numpy 2.5.4, pandas 3.1.1,
pyluach 2.3.0, toolz 1.2.0, tzdata 2026.6, korean-lunar-calendar 0.4.0 and
python-dateutil 4.0.0. The review packet retains official versioned registry links,
wheel hashes, immutable source references and unchanged-target checksums.
The prospective combined resolution changed zero existing locked versions.

The source commit is unsigned; no wheel attestation was obtained. The installed
legitimacy protocol remains **ASSUMED**, not passed. Registry identity and approval
do not establish successful installation, runtime/native compatibility, calendar
correctness or clean security scans. Those proofs remain Plan 08/13 work.

## Verification

- `git diff --check` passed for the approval record and summary.
- Task 1 commit and the Task 2 approval commit exist; review packet exists.
- The packet records the exact approved packages and scope before any Plan 08
  pyproject/lock mutation. No installation was performed by this continuation.
- Documentary checkpoint closure needs no application test rerun.

## Deviations from Plan

None. Prior review was resumed at the explicit checkpoint rather than repeated.
The stale STATE frontmatter status is corrected during scoped progress recording;
Phase 7 remains executing and requirements remain pending final verification.

## Issues Encountered

None in checkpoint continuation. Task 1's protocol, provenance and resolver
limitations remain documented in the review packet; no limitation was waived.

## User Setup Required

None for Plan 08's approved isolated local work. Provider access/display rights,
private verification and final UI acceptance remain separate later checkpoints.

## Next Phase Readiness

Plan 07 is complete (7/14 plans); Plan 08 may begin the reviewed uv lock change,
wheels-only installation and calendar implementation/proof. A materially different
resolution requires review before installation. Existing runtime base, interpreter,
nonroot operation and HIGH/CRITICAL including unfixed scan gates remain enforced.
No production, provider access, publication or stock execution was authorized.
Whole-phase MKT-01 and all other Phase 7 requirements remain pending.

## Self-Check: PASSED

- Review packet exists; completed Task 1 `9279c01` and Task 2 `fd887da` exist.
- Explicit approval is recorded; no missing checkpoint answer or implementation stub.
- No new application trust surface was introduced by this documentary plan.
