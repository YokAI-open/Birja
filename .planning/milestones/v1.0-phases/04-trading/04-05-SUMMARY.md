---
phase: 04-trading
plan: 05
subsystem: deploy
tags: [smoke, runbook, shell]
requires: [04-01]
provides: [trading_requires_auth smoke check, RUNBOOK Trading section]
affects: [deploy/smoke-prod.sh, deploy/RUNBOOK.md]
key-files:
  created: [deploy/tests/test-smoke-trading.sh]
  modified: [deploy/smoke-prod.sh, deploy/RUNBOOK.md]
requirements: [TRADE-03, TRADE-08]
duration: 10min
completed: 2026-10-28
---

# Phase 4 Plan 05: Prod smoke trading check + RUNBOOK Summary

smoke-prod.sh now asserts GET /api/v1/holdings/BTC is 401 and POST /api/v1/trades/quote is 401/403 signed out (local and --public), with an offline stubbed-curl test and a RUNBOOK "Trading (release 0.3)" section.

## Tasks

1. trading_requires_auth check + offline test (commit "feat(04-05): Smoke-check that trade endpoints need a session"). 404/2xx/5xx all fail.
2. RUNBOOK section: migrations 0006/0007, no new services/ports/env, pre-deploy cents count (must print 0), rollback behavior, count-only activity query (commit "docs(04-05): Add Trading (release 0.3) section to the RUNBOOK").

## Verification

- bash -n on all deploy scripts and tests: clean.
- test-smoke-trading.sh 7/7, test-smoke-ports.sh 11/11.
- Read-only `smoke-prod.sh --public` against live prod (0.2.x): the two new checks FAIL with 404, as expected before 0.3 is deployed; all other checks passed.

## Deviations from Plan

- `trading_requires_auth` is defined above the source guard (not next to `prices_requires_auth`) so the test can source and call it.
- Test has 7 cases (added quote 401 and both-404).
- The activity count query in the RUNBOOK reuses the earlier docker exec wording rather than repeating a placeholder container.

## Known Stubs

None.

## Self-Check: PASSED
