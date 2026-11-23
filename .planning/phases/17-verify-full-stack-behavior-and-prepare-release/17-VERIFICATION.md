---
phase: 17-verify-full-stack-behavior-and-prepare-release
status: passed
verified: 2026-11-23
requirements: [QA-02, QA-03]
---

# Phase 17 verification

- Code review and owner acceptance, including native 200% browser zoom, are
  recorded in [Phase 16 UAT](../16-adopt-the-approved-interface/16-HUMAN-UAT.md)
  and the [milestone audit](../../v1.3-MILESTONE-AUDIT.md).
- The final isolated browser suite passed all 93 runnable cases. The
  deployed-site CSP case was skipped in that environment.
- The approved candidate passed all six required checks on
  [PR #41](https://github.com/YokAI-open/Birja/actions/runs/45176790570).
  Backend passed 3,703 tests with 100% critical-path coverage. The ops job
  passed PostgreSQL recovery, roles, TLS and rollback.
- The merge into develop preserved the checked candidate tree. All six
  [develop checks](https://github.com/YokAI-open/Birja/actions/runs/45184429735)
  also passed at merge commit `1902eab33b7db4dfa3b74af30bb7230447f994b7`.

The [Plan 17-02 summary](17-02-SUMMARY.md) records the checked PR head and
merge tree. The release PR will run the required checks on its own head.
