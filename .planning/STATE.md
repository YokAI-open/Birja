---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Searchable Stock Trading
current_phase: 21
status: executing
last_updated: "2026-11-25T19:37:18Z"
last_activity: 2026-11-25 -- Verified live IEX quote access for out-of-list Oracle in a bounded probe
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 29
  completed_plans: 24
  percent: 50
stopped_at: One-stock Alpaca probe passed; expanded catalog and live activation still pending
---

# Project State

## Project Reference

See [PROJECT.md](PROJECT.md), [ROADMAP.md](ROADMAP.md),
[REQUIREMENTS.md](REQUIREMENTS.md) and [v1.4 research](research/v1.4/SUMMARY.md).

Core value: correct virtual trade and valuation money.
Current focus: Phase 21 release verification, rollout preparation and live
acceptance of searchable stock trading.

## Current Position

Phase: 21
Plan: 4 of 9 executed
Status: v0.8.0 published; ORCL probe passed; catalog and rollout checks pending
Last activity: 2026-11-25 -- Verified live IEX quote access for out-of-list Oracle in a bounded probe

Phase 19 completed all six local plans. SC-02 and SC-04 are verified. SC-01
awaits complete admitted live exchange coverage. SC-03 has fixture evidence
and awaits expanded live quote proof. Phase 20 completed all nine plans and
verified SL-01 through SL-04 on synthetic fixtures. Phase 21 owns the overall
and critical coverage gates, release CI, and the first out-of-list production
buy and sell using live IEX data.
[Phase 19 verification](phases/19-search-the-nyse-and-nasdaq-catalog/19-VERIFICATION.md) ·
[Phase 20 verification](phases/20-trade-and-value-stocks-from-search/20-VERIFICATION.md)

Phase 21 local recovery and catalog checks passed. The exact feature CI
run passed 3,941 backend tests, 94.41% overall coverage, 100% critical
coverage, the full browser run and verified recovery tooling. PR #46
merged into develop as `e1b7956` with the checked feature tree. Release
PR #47 passed all six jobs at `84511f0`, including the seven-stage recovery
rehearsal. It merged into main as `4c839f5` with the checked release tree.
Corrective PR #48 fixed two calendar-dependent test fixtures and passed all
six hosted checks at `1024e95`. It merged into main as `0f4a42f` with the
checked tree. All six main checks passed after a same-commit recovery
retry, and the exact `0026` bundle and seven-stage receipt verified.
GitHub published v0.8.0 on that commit. The back-merge and expanded
live-source evidence are pending. The owner confirmed expanded Alpaca
scope and the approved ORCL probe returned advancing sub-second IEX
quotes. Complete directory and live trading qualification remain open.
A paused-stock rollout is proposed for owner review. [Production proposal](phases/21-verify-release-and-activate-stock-trading/21-PRODUCTION-PREFLIGHT.md)
[Release CI receipt](phases/21-verify-release-and-activate-stock-trading/21-RELEASE-CI.md) ·
[Live-source qualification](phases/21-verify-release-and-activate-stock-trading/21-LIVE-QUALIFICATION.md)

## Carried context

- v1.3 Phases 16 and 17 are verified. The [v1.3 audit](v1.3-MILESTONE-AUDIT.md)
  and original phase records preserve approval and verification evidence.

- Production baseline `07d3aa5` has the redesigned UI and 20-stock catalog.
  Alpaca quotes and corporate actions were verified in isolation. Production
  stock execution is disabled and tracked in the [November 24 verification](quick/20261124-stock-activation/SUMMARY.md).

- Phase 7 owner acceptance is closed. The actual stock activation outcome is
  now owned by v1.4. [Deferred work](DEFERRED.md)
