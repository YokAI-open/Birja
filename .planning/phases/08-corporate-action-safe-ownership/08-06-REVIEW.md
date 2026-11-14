---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T12:50:35Z
depth: deep
runtime_source_sha256: 649d9e35416315ae2268264142b97059105ef3530b14310fb3f41142ef435317
files_reviewed: 2
files_reviewed_list:
  - backend/app/services/corporate_actions.py
  - backend/tests/test_corporate_actions.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-06: Focused Transactional Accounting Review

Reviewed the frozen runtime source identified above, current test source and
stable schema/ownership/rule/adapter contracts. Executor was still adding
coverage tests; this report is not a claim that final tests or phase acceptance
have passed. No tests, database operations, provider calls, keys, source edits
or commits were performed.

## Narrative Findings (AI reviewer)

### Targeted correction re-review

**Zero active BLOCKER/WARNING findings in the corrected scope.** Independently
read the frozen runtime hash above and inspected associated regression source.
The expanded combined database proof was still running separately; no tests or
runtime operations were performed by this reviewer.

CR-01 is resolved: final SQL checks the reviewed calendar deadline, action
snapshot, applicable monitor deadline/generation and expected unit/epoch values.
Ingestion/held results do not require current financial monitoring; verified
entitlements and changed split effects do. The source includes final-boundary
monitor expiry and calendar-review expiry rollback regressions.

CR-02 is resolved: fractional/late earlier due actions establish the hold and
break processing. Later economic effects are not applied past that unresolved
boundary; prior successfully ordered effects may remain in the same atomic
operation. Dedicated earlier-fractional/later-integral and earlier-late/later
split regression source was inspected.

CR-03 is resolved: persistence, split and entitlement entrypoints accept trusted
account/server keyword arguments, every `_authority` call propagates them, and
nested dividend-calendar derivation receives the same scope. Nondefault-scope
success and mismatch refusal regression source was inspected. The final SQL
compares the entire previously scoped admission snapshot.

## Historical Findings

### CR-01 — BLOCKER, RESOLVED: Final guard omits monitor and reviewed-calendar deadlines

**File:** `/home/YokaiExchange/backend/app/services/corporate_actions.py:138`

**Also affected:** final state UPDATE near line 148, split eligibility near line
513, entitlement verification near line 775 and final guard near line 884.

**Issue:** The final guard checks current action admission and optional calendar
`valid_until`, but does not check the calendar's earlier `review_valid_until` or
the monitoring state's `valid_until`. A dividend can pass initial cutoff/current
checks, cross either deadline during awaited reconstruction/flush, and still
commit an eligible entitlement. Similarly a split can cross monitoring expiry
after its initial health check and commit its application/holding effects. The
earlier Python checks do not prevent elapsed-time expiry at the final write;
calendar admission may remain valid for hours beyond its reviewed-calendar
deadline.

**Fix:** Include the applicable current monitor/generation/unit expectations and
monitor deadline in the final SQL authorization for financial effects. For a
verified calendar-dependent result, enforce its reviewed deadline using fresh
database wall time as well as its exact evidence snapshot. Keep ingestion's
ability to record held observations separate from current financial authority.
Add real PostgreSQL barriers crossing monitor/calendar-review expiry immediately
before the final write; no eligible snapshot or split effects may commit.

### CR-02 — BLOCKER, RESOLVED: A held earlier split does not stop later split processing

**File:** `/home/YokaiExchange/backend/app/services/corporate_actions.py:570`

**Also affected:** late-history hold branch near line 561.

**Issue:** When a due split is fractional/unsupported for current owners, or too
late for safe historical application, the processor calls `_hold` then continues
the due-event loop. It does not recheck the newly reconciling state before the
next event. For an owner with one share, an earlier 3:2 split is held, but a later
2:1 split can still apply to the old quantity and acquire an immutable application
marker. This violates chronological action processing and can make the previously
fractional split look integral on a subsequent run. Persistent safety must stop
economic effects past an unresolved earlier boundary.

**Fix:** Stop processing later economic effects once an earlier due event is
held; preserve the held state without applying later splits. Ensure retry/healthy
monitoring cannot bypass the unresolved earlier event. Add two ordered due-split
fixtures covering a fractional first event and a late first event; assert no
later application, unit epoch or holding change occurs.

### CR-03 — BLOCKER, RESOLVED: Accounting authority hardcodes the default account/server scope

**File:** `/home/YokaiExchange/backend/app/services/corporate_actions.py:90`

**Also affected:** public persistence/split/entitlement entrypoints and
`dividend_cutoff` call near line 735.

**Issue:** All admission evaluations and the nested calendar cutoff use default
account/server `birja`. The public services accept no trusted configured scope.
Consequently legitimate nondefault scoped admissions are rejected, while a
default-scope row can be accepted by a caller operating under a different
configured account/server. The adapter and existing stock boundaries explicitly
propagate these values; this new financial boundary cannot establish which
deployment/account it is authorizing.

**Fix:** Accept trusted account/server keyword arguments (or an equivalent typed
configured scope) on all accounting entrypoints and propagate them through every
action/calendar admission check and nested cutoff derivation. Preserve default
call compatibility if needed. Add successful nondefault-scope tests and mismatched
account/server refusals for persistence, split application and entitlement
derivation, including calendar scope.
