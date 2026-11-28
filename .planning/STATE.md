---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Market Charts and Workspace Redesign
current_phase: 25
status: phase_complete
last_updated: 2026-11-26T22:52:04.321Z
last_activity: 2026-11-26 -- Phase 25 passed hosted CI and independent verification
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 25
  completed_plans: 25
  percent: 100
stopped_at: Phase 23 replacement feeds verified for v0.9.1
---

# Project State

## Project Reference

See [PROJECT.md](PROJECT.md), [ROADMAP.md](ROADMAP.md),
[REQUIREMENTS.md](REQUIREMENTS.md) and [v1.5 research](research/v1.5/SUMMARY.md) and the
[approved design](ui-reviews/v1.5/README.md).

Core value: correct virtual trade and valuation money.
Current focus: v0.9.1 rollout and live chart verification.

## Current Position

Phase: 25 of 25 (Finish the trading flows and verify the integrated app)
Plan: 7 of 7 executed
Status: Phase 25 complete
Last activity: 2026-11-26 -- Phase 25 passed hosted CI and independent verification

Phase 25 independently passed all 13 checks and four FLOW requirements.
PR #55 head `a3b8464` passed all six hosted jobs. The authenticated
seven-stage recovery receipt matches GitHub's actual checkout `da8ded9`.
[Phase 25 verification](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-VERIFICATION.md) ·
[Hosted CI](https://github.com/YokAI-open/Birja/actions/runs/45900726488)

Phase 24 completed eight plans and verified all four portfolio trend
requirements. Portfolios show exact current figures and a private 30-day
history from capture enablement. Chromium verified eight journeys and four
matched app and reference pairs. All seven encrypted recovery stages and
the exact receipt verifier passed locally. Phase 25 verified the same
recovery contract in hosted CI.
[Phase 24 verification](phases/24-compare-portfolio-performance/24-VERIFICATION.md)


Phase 25 and the Kraken scheduling fix merged into develop through
[PR #55](https://github.com/YokAI-open/Birja/pull/55) after all six checks
and source-bound recovery passed for v0.9.0.

## Prior phase evidence

The tested runtime `775c435` passed 11 isolated browser cases and 1,409
frontend tests. Four app views were compared with the approved ZIP.
[Phase 23 verification](phases/23-show-historical-market-prices/23-VERIFICATION.md)

The v0.9.1 replacement charts use Coin Metrics for crypto and TradingView
for stocks. Both sources passed live qualification under CHART-04.
The [v0.9.1 release record](https://github.com/YokAI-open/Birja/releases/tag/v0.9.1)
tracks production activation. [Source qualification](phases/23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)

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


## Quick Tasks Completed

| ID | Task | Date | Status | Details |
| --- | --- | --- | --- | --- |
| 261127-pvp | Private sign-in and personal stock data | 2026-11-27 | Local tests passed. Production pending. | [Quick task](quick/261127-pvp-restrict-birja-access-with-an-editable-e/261127-pvp-SUMMARY.md) |
