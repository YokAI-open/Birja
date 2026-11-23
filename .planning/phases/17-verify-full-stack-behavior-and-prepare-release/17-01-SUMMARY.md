---
phase: 17-verify-full-stack-behavior-and-prepare-release
plan: "01"
requirements-completed: [QA-02]
status: complete
completed: 2026-11-23
---

# Plan 17-01 — Verify the Candidate Locally

The reviewed application at ef60a64 passed lint, formatting, typecheck, build
and all 1,332 frontend tests. Independent code review and its follow-up are
recorded in Phase 16. UI and native 200% acceptance apply to the same app tree.

The fresh whole browser run returned 85 passed, eight failed and an expected
deployed-only CSP skip. All eight corrected scenarios passed within a
16-scenario follow-up. This provides local coverage of 93 distinct runnable
scenarios across the actual runs. The application, packages, API fixtures
outside the three affected specs, and backend inputs match between runs.
The complete historical outcome is retained in
[Phase 16 results](../16-adopt-the-approved-interface/16-01-SUMMARY.md).

Backend lint, formatting and mypy passed. Backend, database tooling,
Compose test file, CI workflow, Python and Node lock and parser inputs match
the v0.6.2 release test inputs. Reuse 3,703 backend passes and 100% critical
coverage from the [CI receipt](../../releases/0.6.2/CI-RECEIPT.md). The
fresh duplicate suite passed 1,374 before intentional interruption and
owned cleanup. It supplies partial evidence only.

The scope is ready for its PR publication checkpoint. The hosted CI and
merge approvals remain required.
