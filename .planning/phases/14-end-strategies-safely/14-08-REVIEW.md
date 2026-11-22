---
phase: 14-end-strategies-safely
plan: "08"
reviewed: 2026-11-19
depth: standard
source_commit: 96e0714e2f98c8554192f546fbb7ea063bf1c3e1
diff_base: d812114
files_reviewed: 6
files_reviewed_list:
  - backend/app/services/portfolio_lifecycle.py
  - backend/app/services/dividends.py
  - backend/app/tasks/dividends.py
  - backend/tests/portfolio_closure_fixtures.py
  - backend/tests/test_portfolio_closure_events.py
  - backend/tests/test_portfolio_strategy_events.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 08 — Independent Code Review

## Narrative Findings (AI reviewer)

No proven BLOCKER or WARNING identified in the submitted Plan08 changes.
Reviewed all six scoped files and the d812114→96e0714 diff, with the called
dividend SQL, worker discovery/dispatch, existing public closure contract and
terminal lifecycle invariants traced where relevant. No structural pre-pass
was supplied.

This review assesses the new retained-effect interpretation, refusal branch
and meaningful accounting/race tests. It does not certify the unfinished
whole phase, execute tests again or complete any requirement.

## Assessed boundaries

- The lifecycle helper validates bounded integer identities, exactly one
  entitlement/payment cause and a canonical revision fingerprint. Its single
  bound-parameter statement ties the retained cause to the requested portfolio
  and event/revision, with matching owner lineage. Missing or cross-root causes
  refuse without a financial write.
- Closed interpretation requires matching account/lifecycle timestamps, the
  fixed closure policy and coherent retained provenance. Owner-confirmation
  evidence checks the frozen account name and matching closed intent owner,
  portfolio, policy, name and recorded boundary. A ghost lifecycle on an active
  account and missing/inconsistent closed evidence are refused.
- Original payment/decision evidence recorded by closure remains
  `recorded_before_closure`, including a previously held decision. Earned but
  unpaid work and unrecorded later revisions are excluded through the retained
  terminal policy. The helper appends no payment, decision, History or skip
  ledger and does not enumerate future events against deleted portfolios.
  Its `active` result is explicitly not permission to apply a financial effect.
- The service's closed-target branch derives that internal disposition and
  raises the existing fixed private refusal. It does not invoke economic SQL
  or expose retained data through a new public endpoint. Inconsistent lifecycle
  evidence maps to the fixed operational refusal, not a repair or payment.
- An account can close after service discovery. The implementation retains
  `apply_stock_dividend` and `record_stock_dividend_hold` instrument-gate/root
  locking and locked active-state checks; an early read is not substituted for
  this authoritative boundary. SQL replay also remains behind the active-root
  fence. The advancing validator remains the final business statement before
  commit. Historical SQL and the one-instrument financial guard are unchanged.
- Worker pages remain bounded and active-only, and a captured page that becomes
  stale is processed through the same service/SQL refusal. Rejected work needs
  no financial or per-event closed-book row; an independent active sibling is
  still visited. No provider call or new global mutable scheduling state is
  introduced.

## Test reliability and evidence reviewed

The new acceptance fixtures close portfolios through the actual public DELETE,
not privileged `closed_at` mutation. Privileged corruption is limited to named
negative-test setup with triggers restored before the assertion.

Both original-credit and correction races cover financial-first and
closure-first ordering. Actual `pg_blocking_pids` observations establish the
waits; sleeps alone are not treated as ordering proof. Tasks are bounded and
cancelled/awaited during cleanup. The selected-page test explicitly holds a
captured worker page until after public closure.

The independent frozen-root oracle compares original account/baseline,
holdings, trades/fill facts, creation records, ownership movements, dividend
causes/outcomes and closure/intent evidence. It correctly permits shared global
source evidence and identity tails to advance for active siblings. Assertions
include exact before/after snapshots, explicit sibling cash/quantity/basis,
duplicate effects, held-negative evidence, split continuation and foreign-owner
independence. The owned retained strategy fixture now uses the exact current
restricted API fixture and required stock gate; no historical runtime admission
profile was broadened.

Executor-recorded evidence is40 affected PostgreSQL cases in250.12s, scoped
helper coverage of22 statements/10 branches at100%, scoped Ruff/format and
three-module mypy, unchanged historical authority bytes and removed owned
resources. This reviewer inspected the test assertions and recorded receipts
but did not rerun tests, Docker or database operations.

## Required downstream work

Plan16 must add `app/services/portfolio_lifecycle.py` to the critical100%
coverage list while preserving every existing critical module. Plan09 still
owns additional multi-stock/successive-split and management concurrency proof.
The separately recorded retained0020 creation-fixture mismatch remains Plan15
work; this review does not waive it. Whole security/recovery, browser and new
owner UI/native200 acceptance remain the later required execution gates.

No source files were modified, no tests/runtime/provider operations were run,
and no commit was created. Plan11 may proceed.
