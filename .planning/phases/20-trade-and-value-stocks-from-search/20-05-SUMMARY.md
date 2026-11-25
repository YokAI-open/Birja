---
phase: 20-trade-and-value-stocks-from-search
plan: "05"
subsystem: corporate-actions
tags: [stocks, catalog, dividends, splits, recovery-cursor]
requires:
  - phase: 20-03
    provides: Exact scoped action SQL and restricted scheduler and operator grants
provides:
  - Scoped action history and readiness under the original issue identity
  - Dividend and split effects with retained labels and once-only reconciliation
affects: [20-06, 20-07, 20-09]
requirements-addressed: [SL-03, SL-04]
requirements-completed: []
---

# Phase 20 Plan 05 Summary

The worker checks each promoted issue against its own reviewed action scope. The scope defines bounded REST symbol, history and future windows, a mutation start, known-ID rechecks, quota, and separate all-US replay ingress. Its custody and identity decisions remain valid independently of execution permission. An interrupted page keeps its original scope and resume point. A missing or ambiguous input keeps the issue held.

The catalog parser verifies dated terms against the reviewed issue and calendar. It uses the same event and ownership journal as the curated path. An action first seen under an earlier listing retains the original label, entitlement and portfolio. Supported whole-share forward splits preserve basis and move the unit epoch. Unaffordable corrections and fractional splits are held. The existing operator entry point still records identity-checked reconciliation and returns the original decision on replay.

The shared binding selector gained a specific action scope, and the existing action classifier gained a catalog identity supplied by the scoped caller. The curated action worker restricts known-ID queries to its existing instruments. No migration source or grant changes were needed.

## Verification

- Four restricted PostgreSQL role tests passed in 34.83 seconds. They covered exact entitlement, dividend and correction replay, unaffordable correction, whole and fractional split outcomes, and verified operator cancellation after a rename.
- The monitoring selector passed three cases in 22.63 seconds. It covered the legacy curated snapshot, exact page resumption and coverage, and absent replay ingress refusing collection. The scoped worker ran with its execution grant revoked. One targeted parser test passed in 9.73 seconds after explicitly checking dated terms and holding incomplete inputs.
- The existing curated dividend and split regressions passed in 22.36 seconds, covering independent sibling credits and a single basis-preserving split application.
- Ruff, formatting, mypy, compilation and diff checks passed. Provider responses were synthetic. The planned live terms, permission and coverage proof remains in Phase 21.
