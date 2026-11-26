---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "07"
subsystem: acceptance
tags: [github-actions, browser, postgres, recovery]
requires:
  - phase: 25-05
    provides: Guarded app and approved prototype comparisons
  - phase: 25-06
    provides: Bounded hosted recovery and exact receipt contract
provides:
  - Verified CI and schema 0028 encrypted recovery on the approved corrective candidate
requirements-completed: [FLOW-04]
completed: 2026-11-26
---

# Phase 25 Plan 07 — Hosted candidate verification

All six required jobs passed for the corrected head `a3b84647735803cdcc392d2bcaf8141b5a83e64f`. The
verified archive and receipt match GitHub’s actual checkout
`da8ded9f08afd6e17cf46260ac7a036383dcc3f1`. [PR #55](https://github.com/YokAI-open/Birja/pull/55) ·
[Hosted run](https://github.com/YokAI-open/Birja/actions/runs/45900726488)

| Task | Verified result |
|---|---|
| 25-07-01 | Local code review and repair recheck passed. The full guarded browser suite passed all 113 runnable cases, with the expected deployed-site CSP skip. [Review](25-REVIEW.md) |
| 25-07-02 | The owner directed continuation at the exact corrective push checkpoint. The fast-forward updated only the existing feature branch and PR. |
| 25-07-03 | All six jobs passed in 58m 14s. The authenticated seven-stage recovery finished in 25m 04s. The downloaded archive and receipt matched the hosted checkout, exact backend context, and selected image binding. [Candidate evidence](25-CANDIDATE.md) |

The first hosted browser attempt exposed 16 failures. Five corrective
commits addressed test assertions and long company-name wrapping, then
recorded the passing full local replay. The final artifact comes from the
corrected run. CHART-04 live-history qualification remains open.

## Self-Check: PASSED

All six job links, the two Git trees and the downloaded recovery digests
are recorded in the candidate receipt. The existing workflow and checks
were used without changing their required status.
