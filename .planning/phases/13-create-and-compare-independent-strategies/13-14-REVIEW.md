---
phase: 13-create-and-compare-independent-strategies
plan: "14"
reviewed: 2026-11-18T10:56:31Z
initial_reviewed: 2026-11-18T10:52:09Z
depth: standard
diff_base: 4618946
diff_head: 19b5f6f
initial_diff_head: c2d5c24
repair_diff_base: c2d5c24
files_reviewed: 7
files_reviewed_list:
  - backend/tests/test_portfolio_strategy_lifecycle.py
  - backend/tests/test_portfolio_creation.py
  - backend/tests/test_portfolio_metadata.py
  - backend/tests/test_portfolio_strategy_events.py
  - backend/tests/test_portfolio_dividends.py
  - backend/tests/test_portfolio_entitlements.py
  - backend/tests/test_portfolio_splits.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  warning: 1
  total: 1
status: clean
---

# Phase 13 Plan 14: Code Review Report

**Reviewed:** 2026-11-18T10:56:31Z  
**Depth:** standard  
**Files Reviewed:** 7  
**Status:** clean — initial warning resolved

## Summary

Initial review covered the seven test modules changed in `4618946..c2d5c24` and established one concurrency-test reliability warning. Independent re-review of `c2d5c24..19b5f6f` finds it resolved, with no remaining BLOCKER or WARNING. Public-created accounting scenarios and retained assertions remain intact; no production accounting defect was established by this read-only review.

## Narrative Findings (AI reviewer)

## Repair Disposition

**WR-01 — Resolved by `5a951cb`.** The test now records the initializer backend PID and uses an independent disposable-admin observer to require an active `birja_app` backend running the actual `create_portfolio` SQL, waiting on a lock and reporting the initializer PID through `pg_blocking_pids`, before rollback. The observer commits between reads to refresh statistics; a pending HTTP task alone cannot satisfy the check. Observation is bounded to five seconds. Nested cleanup cancels/awaits unfinished request work and rolls back the initializer on every failure path without giving runtime roles new monitoring or write privileges.

The repair summary records two focused passes and a final 21-case affected lifecycle/creation/metadata regression after cleanup was tightened, plus changed-file static checks. These test sources and execution receipts were inspected independently, not rerun. The unrelated 60-case event group was unchanged and correctly retains its earlier execution receipt. No additional concrete issue was established in the repair diff.

## Initial Warning — Resolved History

### WR-01: WARNING — Initializer rollback test can pass without exercising lock contention

**Disposition:** Resolved by `5a951cb`; original severity and initial-source evidence retained below.

**File:** `/home/YokaiExchange/backend/tests/test_portfolio_creation.py:399-403`

**Issue:** The test starts an HTTP creation task, sleeps 100ms, and treats `not pending.done()` as evidence that the second connection is waiting on the initializer's user lock. It never observes that the request reached the SQL authority or is actually blocked by the initializer transaction. A slow session/admission query, Redis operation, connection acquisition or scheduler can keep the task pending for that interval even if it has not attempted creation. Rolling back at that point lets the remaining assertions execute sequentially and pass without testing the claimed contested owner-lock ordering. This can miss a regression in the critical concurrency property the new test is intended to prove.

**Fix:** Replace the fixed sleep with a bounded deterministic observation of the independent database waiter before rolling back. Capture the initializer connection's backend PID and wait until the actual `create_portfolio` request backend reports it as a blocker through `pg_blocking_pids`/`pg_stat_activity`, then assert the HTTP task is still unresolved, roll back and verify the existing economic invariants. Bound the wait and cancel/await the pending task plus roll back the initializer in cleanup on all failure paths. A barrier before the HTTP request or merely before sending SQL is insufficient without proving the requested database contention.

## Review Limits

Both reviews were independent read-only test/source reviews. No tests, database operations, provider calls, dependency changes, source edits or commits were performed; only this report was written. `git diff --check` passed for the repair range. The original and repaired lifecycle/event/static execution receipts were inspected through source and recorded evidence, not rerun.

Review accounted for the explicitly synthetic historical openings and retained 100-cash affordability setup: they do not claim new funding, and the immutable 10000 baselines/journals remain unchanged. Scheduler operations use installed restricted role privileges with role reset before connection return. Public creation/trade/history/overview behavior, original-fill preservation, real split gate contention, duplicate/correction/held event evidence, bounded worker pages, HTTP-boundary shared polling and backup capacity refusal were inspected. Full security/recovery/UI qualification and public deletion/freeze remain outside this report's scope.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
