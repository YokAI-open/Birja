---
phase: 08-corporate-action-safe-ownership
plan: "06"
subsystem: accounting
tags: [postgresql, corporate-actions, split, dividend, historical-ownership]
requires:
  - phase: 08-04
    provides: Bounded immutable provider observations without financial authority
  - phase: 08-05
    provides: Instrument gate, exact causal journal and exclusive historical units
provides:
  - Immutable local economic revisions and persistent blocking observation audit
  - Exact once-only all-owner forward splits with conserved basis
  - Revision-linked historical entitlement snapshots without cash publication
affects: [08-07, 08-08, 08-09, 09-stock-trading, 10-dividend-payments]
tech-stack:
  added: []
  patterns: [instrument-serialized-actions, final-sql-authority-guard, immutable-superseding-entitlements]
key-files:
  created: [backend/app/services/corporate_actions.py, backend/tests/test_corporate_actions.py]
  modified: []
key-decisions:
  - A caller transaction handles exactly one instrument; multi-stock adapter batches must be partitioned by the scheduler.
  - Missing identities and suspected aliases remain auditable holds, never inferred cancellations or economic aliases.
  - Final SQL checks exact action/calendar evidence, current mapping, monitoring deadline/generation and expected units/epoch.
  - The first unresolved due split stops later economic effects.
  - Immutable entitlement versions include lineage; a held replacement cannot expose older eligible snapshots as current.
requirements-completed: []
requirements-addressed: [DIV-01, DIV-02, ACT-01, ACT-02, ACT-03]
duration: 24min
completed: 2026-11-11
---

# Phase 8 Plan 06: Transactional Corporate Actions Summary

**Instrument-serialized observations preserve economic revisions, exact forward splits commit once with unchanged basis, and historical dividend eligibility survives later trades through immutable revision-linked snapshots.**

## Performance and scope

Approximately24minutes,2026-11-11, ending12:51UTC. Three tasks and two source/test
files; existing dependencies, schema, roles and canonical recovery contracts are
unchanged. Every financial fixture uses the isolated guarded birja-test stack.
The app remains runnable with stock execution OFF. No cash/payment/History
publication, private provider request, environment/key read, production access,
B2/timer/process change, installation, publication or deployment occurred.

## Implemented interfaces

All writes use caller-owned READ COMMITTED transactions and the existing fixed
instrument advisory gate. Any raised exception requires rollback of the whole
business operation. No external I/O occurs while holding financial locks.

- `persist_action_batch(db,batch,authority,*,account="birja",server="birja")`
  accepts one instrument's observations/missing-ID evidence and returns frozen
  `PersistedAction` records. Plan07 must partition multi-instrument batches before
  separate transactions. Identical terms append observations without another
  economic revision; changed terms receive immutable local ordinals. Source,
  economic and observation instants remain distinct. Suspected replacement IDs
  create separate held candidates; reappearing historical terms cannot rewind
  safe state. Explicit known-ID absence retains the prior revision and appends
  `missing_or_uncertain` audit. Applied split changes/cancellations and effective
  events older than affected ownership create holds without inverse effects.
- `apply_due_actions(db,coin_id,now=None,*,account,server)` derives actual time
  from the database after waits; caller `now` grants no authority. The gate,
  sorted holders, complete journal and exact `plan_forward_split` validation
  protect every owner. One application marker, unit transition and all positive
  owner deltas commit together. Zero-owner and zero-quantity holders work;
  fractional/overflow/late cases hold without effects. The first unresolved
  boundary stops later due splits. Total basis, cash and Trade rows are never
  assigned. Quote units advance and `quote_not_before` invalidates older marks.
- `derive_dividend_entitlements(db,event_id,*,account,server)` returns frozen
  `EntitlementSnapshot` records. Genuine reviewed-calendar exclusive cutoffs and
  journal replay include departed/zero owners and exclude later purchases.
  Verified pre/post units are explicit at equal split boundaries. Revised terms
  append `supersedes_id` lineage instead of overwriting prior quantities. Unknown
  cutoffs use an explicit unverified rule and zero held eligibility, not guessed
  economic entitlement. No payable-date holdings lookup or cash credit exists.
- `latest_verified_entitlements` chooses each owner's newest snapshot and only
  returns eligible snapshots matching the current event revision; a later held
  or cancelled version cannot reveal an older eligible record as current. This
  historical selection is not payment authority; Phase10 still rechecks its
  current payment/correction gates.
- `persistent_action_holds` reads unresolved historical uncertain/cancelled
  revisions and missing observations. Healthy monitoring cannot clear them;
  only matching reviewed resolution evidence can do so. Plan07 owns complete
  catch-up/cursor/health derivation; adapter completeness never grants health.

Final guarded SQL compares the entire action-admission snapshot and catalogue
mapping, actual database time, and—when producing financial effects—monitor
generation/deadline plus expected unit/epoch. Eligible calendar-dependent results
also compare the full calendar evidence and its earlier review deadline. Trusted
configured account/server keywords propagate through all action/calendar checks;
provider payloads cannot supply deployment authority.

## TDD and commits

1. Task08-06-01 RED `a878aed`: real persistence expected one event but the
   importable scaffold returned none. GREEN `d132574`: immutable revisions,
   audit observations, missing/late/alias/cancellation and current permissions.
2. Task08-06-02 RED `1bb2407`: actual4:1 split expected an application/quantity
   change but returned none. GREEN `0245c0a`: all-owner split application and
   journal effects, unchanged basis, concurrency and injected rollback.
3. Task08-06-03 RED `ce692ca`: verified historical dividend expected one eligible
   snapshot but returned none. Additional regression commit `5370ee4` records
   independently reviewed failures. GREEN `89b6ae8`: historical immutable
   entitlements and all reviewed final-write/ordering/scope corrections.

Both earlier tasks passed their actual scoped tests before their GREEN commits;
the complete final proof below supersedes those smaller intermediate runs.

## Actual verification

- `cd backend && .venv/bin/python -m pytest tests/test_corporate_actions.py tests/test_stock_ownership.py tests/test_corporate_action_rules.py --cov=app.services.corporate_actions --cov-branch --cov-report=term-missing --cov-fail-under=100 -q -x`:
  **234passed,20existing upstream calendar warnings,22.43s**. The new service
  has **312statements/116branches,100%**. Receipt:`/tmp/phase08-06-final.log`.
- New action suite alone: **76passed,4upstream warnings,11.50s**,100%critical
  coverage. Receipt:`/tmp/phase08-06-final-coverage.log`; the expanded final run
  above additionally proves the frozen SQL expected-unit/epoch conjuncts.
- Scoped Ruff check/format and mypy pass; `git diff --check` passes. No new
  dependencies, privilege changes, source stubs, TODO/FIXME or tracked deletions.
- Two actual independent-session races observe PostgreSQL blocking through
  `pg_blocking_pids`: freezer-first refuses the waiting fill; fill-first commits
  before the waiting freeze. No sleep is treated as proof of gate acquisition.
- Concurrent split processors create one economic application. Real4:1/integral
  3:2/zero-owner/fractional/overflow cases preserve exact basis and quantities;
  failure after the first holding delta rolls back every marker/movement/epoch.
- Real committed admission changes immediately before final SQL roll back whole
  ingestion, split and entitlement operations. Actual database waits cross
  monitor expiry independently for split and entitlement, and cross the earlier
  calendar-review deadline; no eligible/economic effect commits afterward.
- Historical late buyers/departed sellers, exact before/after/same-boundary unit
  ordering, revised rates, cancellation, missing baseline, orphan ownership and
  repeated monitor loss/recovery preserve deterministic immutable lineage.
- Runtime SHA256:
  `649d9e35416315ae2268264142b97059105ef3530b14310fb3f41142ef435317`.
  Parent independent re-review confirms **0active findings**, all three reviewed
  blockers closed at this frozen SHA. Parent separately reports full Wave4:
  **1398passed,73warnings,75.35s,99.80%overall**;26critical modules2407statements/
  804branches100%,compileallpass. These are parent-owned executed results.

## Deviations and review corrections

**[Rule1—correctness] Final deadlines.** Independent review found initial final
SQL omitted monitor expiry and the calendar's earlier reviewed deadline. Actual
PostgreSQL regressions failed before the correction, including two monitor paths
and one reviewed-calendar path. Final guards now check those deadlines and
generation/unit expectations after awaited reconstruction/writes.

**[Rule1—correctness] Ordered holds.** An earlier fractional/late split originally
continued to a later due split. A real two-event regression failed; processing
now stops at the first unresolved boundary, tested for both fractional and late
history. Recovered monitoring cannot make a later action bypass that event.

**[Rule2—authority] Configured scope.** The initial service used default account/
server values internally. Trusted keyword arguments now propagate throughout
action/calendar evaluation. Nondefault matching scopes work and mismatches are
refused for all three accounting entrypoints. No admission privilege expanded.

Review failure receipts:`/tmp/phase08-06-review-red.log` (2failed) and
`/tmp/phase08-06-review-extra-red.log` (5failed). No architectural deviation or
package change was required. Synthetic test setup briefly reused one source ID
for two different economic events; the correct identity-conflict hold exposed
that fixture mistake, which was corrected with separate source IDs.

The new surface is confined to planned durable accounting service functions.
T-08-06-01/02/03 are covered by unique causal/economic schema, actual transactions,
immutable revisions, exact unit/basis rules and fixed authority checks. No new
HTTP/auth/file/network boundary or schema/ACL change was introduced; existing
role/recovery proofs remain prior evidence, not falsely claimed reruns.

## Remaining gates

Ready for Plan07 monitoring after clean independent re-review and parent Wave4
integration. Phase7 live
verification stays owner-deferred and its fixed process remains untouched.
Whole-phase DIV/ACT requirements remain unchecked; no end-to-end acceptance is
inferred from this accounting foundation. Future Phase9 fills, Phase10 payments/
History, Phase8 privileged reconciliation/UI and external activation remain
their planned responsibilities. No required implementation stub remains here.

## Self-Check: PASSED

Both source/test artifacts exist; all seven listed task/regression commits exist.
Final actual financial critical coverage and scoped static checks pass. Fixtures
cleaned their action/observation/entitlement/holding/admission state; the isolated
test stack remains available for parent integration. DB test lane released.
