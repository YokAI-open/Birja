---
phase: 08-corporate-action-safe-ownership
plan: "09"
subsystem: api
tags: [postgresql, stock-quotes, corporate-actions, authorization, concurrency]
requires:
  - phase: 08-08
    provides: Exact immutable-history reconciliation and restricted action authority
provides:
  - Final committed action-safe stock discovery with fixed public reasons
  - Gate-bound local quote units and exact post-split source provenance
  - Deterministic single-instrument scheduler transactions after provider I/O
affects: [08-10, 08-11, 08-12, 09-stock-trading]
tech-stack:
  added: []
  patterns: [bounded-final-authority-projection, single-instrument-quote-transactions, generic-permission-redaction]
key-files:
  created: []
  modified: [backend/app/schemas/stocks.py, backend/app/services/stocks.py, backend/app/services/stock_quotes.py, backend/app/services/corporate_actions.py, backend/app/tasks/stock_scheduler.py, backend/tests/test_stocks_api.py, backend/tests/test_stock_quotes.py, backend/tests/test_corporate_actions.py]
key-decisions:
  - Final public action facts require matching current action admission and current calendar authority; denial returns generic epoch0 with null times.
  - A local unit epoch is assigned only under the shared instrument gate, with exact applied split evidence and a strictly later source event.
  - The scheduler partitions provider batches into sorted one-instrument transactions; quote persistence never commits the caller transaction.
requirements-completed: []
requirements-addressed: [ACT-01, ACT-02, ACT-03]
duration: 20min
completed: 2026-11-11
---

# Phase 8 Plan 09: Action-Safe Discovery and Quote Units Summary

**Stock discovery suppresses unsafe amounts using final committed action authority, while current-unit quotes acquire local provenance under the same gate as splits.**

## Scope and behavior

Two tasks, eight source/test files, approximately20minutes, starting around
2026-11-11T15:20Z. All database tests used the guarded isolated birja-test stack.
No packages, image versions, migrations, grants, credentials, private provider
HTTP, production, B2, timers, existing Phase7 campaign, publication or deployment
were changed or accessed. Whole-phase requirements and activation remain pending.

The immutable additive response exposes action state current/unknown/reconciling/
suspended, fixed sanitized reasons, a safe integer safety epoch and nullable
check/deadline times. Valuation reason distinguishes available, unavailable
actions, missing post-split quotes and unavailable quotes. Twenty catalogue
identities, IEX attribution, independent unknown halt status, authenticated
no-store routing and execution_enabled=false remain intact.

The final READ COMMITTED statement projects at most20 fixed-size action facts.
It independently checks unresolved immutable revisions, exact applicable reviewed
resolutions, newer material uncertainty, changed applied revisions and pending
current-event boundaries. Resolution history is aggregated in PostgreSQL with a
129-ID bound against the reviewed128-ID maximum; no growing event or operator
JSON is transferred. Original quote/session rights still apply. A fresh UTC clock
follows the final await, and projection performs no subsequent asynchronous I/O.
Action validity is bounded by monitor, action permission, calendar review and
known unresolved boundaries; disclosed quotes additionally bound their action
deadline by current quote permission and retained-observation expiry.

Missing, malformed, revoked, expired or mismatched authority hides prices and
source times. Unavailable action/calendar permission returns generic epoch0 and
null action times, even if an older persisted monitor had a larger epoch. An
otherwise permitted dated monitor can remain truthfully unknown/reconciling.

Quote inputs remain provider-only data. Explicit insert columns assign local
unit_epoch after acquiring the existing single-instrument transaction gate and
reloading committed permission/units. Epoch-zero collection compatibility stays
available without inventing action readiness. Nonzero units require current
action collection/derived/retention authority, healthy coverage, exact current
applied boundary, no persistent holds or changed applied revision, and a source
event strictly after quote_not_before. Equal/older source events never renew
receipt or relabel a retained observation. Source age is checked again after
blocking gate and authority reads. Current database wall time guards final writes.

The scheduler finishes HTTP first, then sorts quotes by coin ID and owns one
short transaction per instrument. Each transaction retains current permission,
calendar and lease checks before commit. The persistence service never commits
its caller transaction and refuses multiple valid instruments in one transaction.
Unrelated safety-epoch changes do not change financial units.

## Task commits and TDD evidence

1. Task08-09-01: behavioral RED `c648dad` exposed a quote without action monitor
   authority; GREEN `3833fc5` added the final action envelope and shared hold SQL.
2. Task08-09-02: behavioral RED `f473382` refused a genuine post-split observation;
   GREEN `f6e9d0a` adds gate-bound provenance and scheduler partitioning.
3. Independent CR01: calendar RED `e5a2838` and entire-envelope generation RED
   `4592e23` reproduced disclosure of obsolete derived times/epoch. Explicit
   authority-first generic redaction is included in `f6e9d0a`.
4. Final regression/coverage tests: `530f9f7`.

An exact-text edit initially missed the formatter-expanded generation condition;
the entire-envelope RED reproduced that remaining issue before the explicit
early-return fix. Price-only assertions were strengthened rather than accepted
as evidence that authority metadata was redacted.

## Verification

- Final serial focused command:
  `cd backend && .venv/bin/pytest tests/test_stocks_api.py tests/test_stock_quotes.py tests/test_stock_scheduler.py tests/test_corporate_actions.py tests/test_stock_action_resolutions.py tests/test_stock_action_monitoring.py --cov=app.services.stocks --cov=app.services.stock_quotes --cov=app.services.corporate_actions --cov-report=term-missing --cov-fail-under=100 -q`
- **311passed,28warnings,101.00seconds**; existing pandas deprecation warnings.
- Critical coverage: corporate_actions334statements/118branches, stock_quotes89/
  30 and stocks139/46; **562statements/194branches,100%, zero partial branches**.
- Scoped Ruff and format checks pass for all8 source/test files; mypy passes
  all5 source files; `git diff --check` passes.
- Actual two-session tests observe ungranted advisory locks in pg_locks before
  releasing the holder: quote waits for split, split waits for quote, equality
  at the unit cutoff, committed revocation during the wait and source-age expiry
  at120seconds. Timing alone is never treated as proof of lock serialization.
- Actual apply_due_actions→retained consumed next_blocking marker→new compatible
  quote→API current passes. A separately seeded unresolved current-event boundary
  still bounds validity and suppresses the quote at its cutoff.
- Existing real operator resolution/replay/identical-confirmation/new-uncertainty
  regressions pass with the shared SQL applicability predicate. Malformed or
  oversized final projection data fails closed while retaining20 identities.
- Independent full review and targeted CR01 re-review report **0active findings**
  for frozen runtime `f6e9d0a`; see08-09-REVIEW.md. Root owns the full Wave7 gate.
- Final detailed log: `/tmp/phase08-09-focused-final.log`.

## Deviations from plan

1. **[Rule2 — Missing critical integration] Shared exact hold predicate.**
   The old async persistent_action_holds implementation loaded growing history
   and could not participate in the final single-statement API snapshot. A narrow
   SQL predicate in corporate_actions.py now serves both existing accounting and
   bounded API projection. No schema, privileges or financial effects changed.
   Verified by the actual accounting/operator resolution regressions.
2. **[Rule2 — Missing critical integration] Scheduler caller partition.**
   The previous20-quote caller transaction conflicted with the existing mandatory
   single-instrument gate. stock_scheduler.py now partitions sorted quotes while
   preserving caller-owned commit/rollback and all lease/calendar checks. Real
   scheduler and PostgreSQL regressions pass.
3. **[Rule1 — Integration bug] Consumed cached action boundaries.**
   Existing split processing intentionally retains next_blocking_at. Projection
   ignores a consumed cache marker only with exact current applied unit evidence;
   canonical unresolved current events and historical holds remain independent.
   Verified by actual split/application/quote/API integration and a distinct
   pending-boundary regression, without altering the financial processor.
4. **[Rule1 — Review bug] Obsolete derived metadata after authority loss.**
   CR01 required generic epoch0/null timestamps after revoked calendar or changed
   action admission generation, beyond already-hidden prices. Meaningful RED/
   GREEN and clean independent re-review are recorded above.

## Next plan handoff

Plan08-10 must implement strict additive client validation and local deadline
expiry for the new action/valuation fields. **Permission redaction must dominate
epoch ordering:** accept generic epoch0/null-time authority denial even when a
previous response had a higher action epoch; immediately hide its old prices.
Keep an internal high-water epoch to refuse a later unsafe older response, but
never reject safety-reducing redaction as stale and retain prior amounts.

Plan08-11 owns the corresponding UI. Phase7 UI acceptance remains recorded and
its live review remains owner-deferred; neither is new Phase8 human acceptance.
Stock execution, cash effects and public event History stay disabled/out of this
plan. No image/recovery replay was repeated for these service-only changes;
Plan08-12 retains final complete security/runtime/recovery proof obligations.

## Known stubs and threat flags

No blocking stubs or new unplanned network/authentication/file-access surfaces.
Unknown action/halt facts are intentional truthful availability states, not
fixture-backed live claims. Threat mitigations T-08-09-01/02/03 retain final
authority, sanitized output and actual gate-race regressions.

## Self-Check: PASSED

All8 changed source/test paths exist; RED/GREEN commits c648dad,3833fc5,f473382,
e5a2838,4592e23,f6e9d0a and530f9f7 exist. Final focused tests and critical coverage
pass, independent review is clean, and remaining phase/activation gates stay
explicitly pending.
