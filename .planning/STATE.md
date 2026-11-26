---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Market Charts and Workspace Redesign
current_phase: 25
status: awaiting_approval
last_updated: "2026-11-26T21:25:33Z"
last_activity: 2026-11-26 -- Phase 25 repaired all hosted browser failures and passed the full local suite
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 22
  completed_plans: 21
  percent: 50
stopped_at: Phase 25 (6/7) — Awaiting corrected candidate push
---

# Project State

## Project Reference

See [PROJECT.md](PROJECT.md), [ROADMAP.md](ROADMAP.md),
[REQUIREMENTS.md](REQUIREMENTS.md) and [v1.5 research](research/v1.5/SUMMARY.md) and the
[approved design](ui-reviews/v1.5/README.md).

Core value: correct virtual trade and valuation money.
Current focus: Run hosted CI on the corrected Phase 25 candidate.

## Current Position

Phase: 25 of 25 (Finish the trading flows and verify the integrated app)
Plan: 6 of 7 executed
Status: Awaiting corrected candidate push
Last activity: 2026-11-26 -- Phase 25 repaired all hosted browser failures and passed the full local suite

PR #55 passed the first hosted recovery, frontend and image jobs. Browser
CI found 16 failures. The corrected candidate passed all 113 runnable cases
in the full local suite and the frontend gate. The final plan awaits explicit
approval to push the new head for all six hosted jobs and the matching
authenticated recovery receipt.
[Phase 25 validation](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-VALIDATION.md)

Phase 24 completed eight plans and verified all four portfolio trend
requirements. Portfolios show exact current figures and a private 30-day
history from capture enablement. Chromium verified eight journeys and four
matched app and reference pairs. All seven encrypted recovery stages and
the exact receipt verifier passed locally. Hosted recovery timing and
Phase 23's CHART-04 live qualification are recorded release checks.
[Phase 24 verification](phases/24-compare-portfolio-performance/24-VERIFICATION.md)

## Prior phase evidence

The tested runtime `775c435` passed 11 isolated browser cases and 1,409
frontend tests. Four app views were compared with the approved ZIP.
[Phase 23 verification](phases/23-show-historical-market-prices/23-VERIFICATION.md)

CHART-01 through CHART-03 are verified locally. CHART-04 stays open for
Kraken and IEX history rights, representative coverage and measured limits.
Live history is disabled by default. [Source qualification](phases/23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)

Phase 22 passed all four requirements. The final isolated run passed 105
browser tests with the expected deployed-site CSP skip. All 1,376 frontend
tests and the production frontend build passed.
[Phase 22 verification](phases/22-adopt-the-market-workspace/22-VERIFICATION.md)

## Carried context

- v1.3 Phases 16 and 17 are verified. The [v1.3 audit](v1.3-MILESTONE-AUDIT.md)
  and original phase records preserve approval and verification evidence.

- The integration baseline includes v0.8.1. Remaining v1.4 acceptance and
  closeout evidence is tracked in the [Phase 21 handoff](milestones/v1.4-OPEN-HANDOFF.md).

- Phase 7 owner acceptance is closed. The actual stock activation outcome is
  now owned by v1.4. [Deferred work](DEFERRED.md)
