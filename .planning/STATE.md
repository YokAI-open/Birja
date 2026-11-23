---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Birja Interface Redesign
current_phase: 17
current_plan: 2
status: awaiting_ci_fix_publication
last_updated: "2026-11-23T10:52:54+00:00"
last_activity: 2026-11-23
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 4
  completed_plans: 3
  percent: 75
---

# Project State

## Project Reference

See [PROJECT.md](PROJECT.md), [ROADMAP.md](ROADMAP.md) and the
[candidate audit](v1.3-MILESTONE-AUDIT.md).

Core value: correct virtual trade and valuation money.
Current focus: publish the tested CI corrections for redesign PR #41 after approval.

## Current Position

Phase: 17 — Verify Full-Stack Behavior and Prepare Release
Plan: 17-02 required CI
Status: PR #41 is open into develop at approved head 5993ae44f7243758b564a38682e258fcbab9cfd5. Initial CI was blocked. The browser focus setup and bounded ops setup corrections pass their local checks and await publication.
Last activity: 2026-11-23 — Validated the corrections for [PR #41](https://github.com/YokAI-open/Birja/pull/41).

## Evidence

- Same application tree at ef60a64 and abe4976. Follow-up changes affect
  browser test locators and navigation in three specs.
- Frontend lint, format, typecheck, build and 1,332 tests pass with 97.56%
  line coverage. Backend lint, format and mypy pass. Use the complete
  3,703-test/100%-critical release receipt for checked identical backend
  inputs. A separate fresh run passed 1,374 before intentional interruption
  and owned cleanup.
- The complete browser run returned 85 passes, eight test failures and one
  expected deployed-only skip. The targeted rerun passed 16 including all
  eight failed cases. The evidence covers 93 distinct runnable scenarios.
- Owner integrated UI and native 200% passed. See [UAT](phases/16-adopt-the-approved-interface/16-HUMAN-UAT.md).
- v1.2 is archived and production is v0.6.2. Phase 7 owner acceptance is
  closed. Live stock activation and other follow-ups stay in [DEFERRED.md](DEFERRED.md).

Hosted CI: [run 45160029262](https://github.com/YokAI-open/Birja/actions/runs/45160029262).

See [CI diagnosis and local proof](debug/pr41-hosted-qualification.md).
