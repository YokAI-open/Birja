---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "06"
subsystem: ci
tags: [github-actions, recovery, utc, workflow-contracts]
requires:
  - phase: 24-compare-portfolio-performance
    provides: Exact same-archive recovery graph and measured local runtime
provides:
  - Bounded hosted recovery budget and tested UTC fixture window
  - Required preflight, clock wait, and source-bound recovery order
affects: [25-07]
tech-stack:
  added: []
  patterns: [offline contract execution of the actual workflow clock step]
key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - deploy/tests/test-ci-ops.py
key-decisions:
  - Use a 65-minute recovery horizon and serial step with a 126-minute clock wait and 225-minute enclosing job.
  - Keep preflight, clock wait and serial recovery in order under the existing archive and receipt verification.
requirements-completed: [FLOW-04]
duration: 4 min
completed: 2026-11-26
---

# Phase 25 Plan 06 — Recovery CI timing

The hosted ops job has a 65-minute serial recovery window with a matching
UTC clock check. The bounded wait allows 126 minutes and the enclosing job
allows 225 minutes.

## Execution record

Both tasks completed between `2026-11-26T19:23:30Z` and
`2026-11-26T19:27:05Z`.

| Task | Commit | Evidence |
|---|---|---|
| 25-06-01 | `8be2071` | 115 offline CI tests passed in 31.608 seconds. The actual workflow clock code ran against a simulated clock at 00:00, 01:00, 22:54:59 and 22:55 UTC. |
| 25-06-02 | `d47d35a` | 115 offline CI tests passed in 29.930 seconds. The recovery contract rejected omitted and misplaced clock steps. The Phase 24 selector dry run reported the ordered seven stages. |

At 00:00 the simulated wait finished at 01:00 on the same day. The clock
returned immediately at 01:00 and 22:54:59. At 22:55 the 65-minute window
crossed midnight, and the wait finished at 01:00 the next day after 125
minutes. The test clock advanced without wall-clock sleeping.

The selector returned `image-transition`, `retained-roundtrip`,
`current0028-cold`, `roles`, `tls-upgraded`, `tls-fresh` and
`selected-rollback` in order. A byte comparison with the phase baseline
`16f7763` verified that the workflow diff contains exactly the four timing
values. The existing suite exercised the required job dependencies, audit
and coverage commands, image policy, two archive digests and cleanup
contracts. `git diff --check` passed.

## Candidate evidence

The Phase 24 serial run measured 56m 19s locally. The 65-minute serial bound
provides 8m 41s of headroom against that run. The Phase 24 backend run measured
2h 04m 43s alongside the other local work. The backend job uses its existing
120-minute budget. [Phase 24 recovery receipt](../24-compare-portfolio-performance/24-RECOVERY-RECEIPT.md) · [Phase 25 research](25-RESEARCH.md)

Hosted timing and the exact candidate recovery receipt are pending for
Plan 25-07. The local selector result documents the stage graph. The
authorized hosted job supplies the measured archive and receipt.

## Self-Check: PASSED

Both task commits exist and contain only the files declared by their tasks.
