---
phase: 14-end-strategies-safely
plan: "08"
subsystem: frozen-event-accounting
tags: [postgresql, dividends, lifecycle, concurrency, portfolio-closure]
requires:
  - phase: 14-07
    provides: Private public DELETE over complete same-transaction closure proof
provides:
  - Deterministic internal retained-effect disposition without new financial rows
  - Closed-target service refusal with unchanged post-lock SQL authority
  - Actual public-DELETE credit/correction lock-order and frozen-causal-state proof
  - Active sibling split and foreign-owner uncertainty continuity
affects: [14-09, 14-15, 14-16, 14-18, critical-coverage]
tech-stack:
  added: []
  patterns:
    - Read-only causal interpretation is never authority to perform a financial write
    - Actual blocked PostgreSQL PIDs establish credit/correction versus closure ordering
key-files:
  created:
    - backend/app/services/portfolio_lifecycle.py
    - backend/tests/test_portfolio_closure_events.py
  modified:
    - backend/app/services/dividends.py
    - backend/app/tasks/dividends.py
    - backend/tests/test_portfolio_strategy_events.py
    - backend/tests/portfolio_closure_fixtures.py
key-decisions:
  - Preserve existing instrument/root SQL fences; active discovery alone is not the write boundary.
  - Classify one retained entitlement or payment and source revision from immutable evidence, without a future-event-by-closed-root job or skip ledger.
  - Already recorded originals and held decisions remain recorded_before_closure; excluded unpaid or future revision work is not_applied_portfolio_closed.
requirements-completed: []
requirements-progress: [PMGT-04, PFIN-05, PFIN-06]
duration: 14.5min measured first-RED-to-cleanup-receipt interval
completed: 2026-11-19
---

# Phase 14 Plan 08: Frozen Financial Event Boundaries

**Actual confirmed deletion preserves unpaid/held causal evidence and financial
History while independent active strategies continue once-only dividends,
corrections and splits.**

## Task commits and measured scope

| Task | Commit | Actual evidence |
|---|---|---|
|1 RED|20444e4|Missing lifecycle helper after valid current public-created stock setup;7.40s|
|1 GREEN|0648694|Four real public-DELETE disposition/worker/refusal cases pass26.29s; scoped static checks pass|
|2 test-only completion|9543d9c|Final40-case affected run passes250.12s; actual lock barriers, held negative/split/foreign owner and corruption proofs|

First RED was2026-11-19T12:10:33UTC; cleanup/evidence receipt was recorded at
12:25:03UTC. This14.5-minute interval includes implementation and diagnostics,
not a task-feedback latency promise. Parent owns STATE/ROADMAP; no whole
requirement completion is claimed.

## Implemented behavior

- `lifecycle_effect_disposition` is a bounded, read-only, single-statement
  interpretation of an exact retained entitlement/payment, its event/revision,
  root and immutable closure policy/provenance. It rejects unknown/cross-root
  causes and inconsistent lifecycle evidence with a fixed private error. Its
  `active` result never authorizes a payment: runtime SQL still decides after
  obtaining its instrument and root locks.
- Valid recorded originals/decisions, including held decisions, remain
  `recorded_before_closure`. Earned-but-unpaid causes and unrecorded later
  revisions/holds on a closed book are `not_applied_portfolio_closed`. New
  global announcements create no closed-book work or association; the universal
  closure policy explains exclusion without enumerating future events.
- The dividend service validates the discovered cause/root and, if already
  closed, derives the internal disposition before refusing. The existing fixed
  `portfolio_unavailable` refusal and worker rejection behavior stay compatible.
  Inconsistent retained evidence refuses as `authority_unavailable`. No new
  public retained-finance read or normal History row is introduced.
- A target closing after discovery still reaches the existing SQL active-root
  recheck after waits. No financial routine, migration, fingerprint or SQL
  authority was changed. There is no post-final-validator business read.
- The independent root-only oracle covers account/baseline, holdings, fills,
  facts, creation grants, ownership movements, entitlements, payments,
  decisions and lifecycle/intent boundaries. Shared global source evidence and
  shared sequence tails may advance for active siblings; the oracle deliberately
  does not incorrectly freeze those global objects.

## Financial entrypoint inventory

| Entrypoint | Closure boundary / evidence |
|---|---|
|`derive_dividend_entitlements`|Existing active-root reconstruction preserves old closed snapshots; later revisions derive only active siblings.|
|Original credit / positive or negative correction via `process_dividend`|Existing `apply_stock_dividend` instrument lock, locked active root and final authority remain unchanged; both commit orders tested.|
|Held correction and original/decision replay|Immutable originals/held decisions survive close; duplicate calls cannot apply or append closed effects.|
|Uncertainty anchor via `record_dividend_hold`|Closed anchor is refused with causal disposition; active same-stock and foreign-owner anchors continue once each.|
|Worker VERIFIED / ANCHORS pages|Active discovery remains bounded; a captured page closing before dispatch is rejected without skip rows while siblings continue.|
|Already-selected SQL work|Actual PostgreSQL lock wait proves SQL rechecks the root after closure; no preselection authorization shortcut.|
|Global revision/reconciliation and split processing|Global evidence may evolve; closed financial causes stay byte-identical. Active sibling split doubles quantity, conserves basis and replays once.|

## Actual verification

Raw private synthetic receipts: `/tmp/birja-phase14-plan08/`.

| Check | Actual result |
|---|---|
|Task1 RED|Missing `app.services.portfolio_lifecycle`,7.40s; `task1-red.log`|
|Task1 initial GREEN|4passed26.29s; `task1-green.log`|
|Actual credit/correction lock races|4passed26.54s; `task2-races.log`|
|Held-negative/split and foreign-owner uncertainty|2passed14.52s; `task2-held.log`|
|Retained-corruption refusal|3passed19.94s; `task2-corruption.log`|
|Final unchanged-source affected group|40passed250.12s; `final-affected.log`|
|New helper scoped coverage|22statements and10branches,100%; no phase-wide coverage claim|
|Scoped Ruff/check/format|All six touched source/test files pass|
|Scoped mypy|All three touched source modules pass|
|Historical authority guard|All `backend/alembic` bytes equal dispatch base d812114|
|Source drift guard|All six source/test hashes match `frozen-source.json` before/after final run|
|Cleanup|Owned birja-p14-08 PostgreSQL/Redis containers and network removed; final project container query empty|

The final command was:

```
cd backend
UV_NO_SYNC=1 UV_OFFLINE=1 uv run pytest tests/test_portfolio_closure_events.py tests/test_portfolio_strategy_events.py tests/test_portfolio_closure_api.py tests/test_portfolio_closure_identity.py --cov=app.services.portfolio_lifecycle --cov-branch --cov-fail-under=0 -x
```

The scoped coverage observation is not a replacement for unchanged whole-phase
coverage gates. Final source is9543d9c, with receipt and log SHA256s in
`receipt.json`. No source edits occurred during that complete40-case run.

## Meaningful boundary proofs

- Both original-credit and correction cases cover financial-first and
  closure-first order. Actual `pg_blocking_pids` barriers establish the waits,
  with the test administrator observing other-role state. Earlier committed
  deltas are retained exactly; later work refuses without altering the frozen
  financial/causal snapshot. Two actual workers affect only the active sibling.
- A real worker page captured before public DELETE is released afterward:
  the closed target is rejected, its active sibling is processed, and no skip
  or financial History record is appended for the closed book.
- Actual public crypto spending leaves$0.10, creating a genuinely unaffordable
  negative correction. Its held decision freezes at public deletion. Later
  revisions and a genuine split leave that book unchanged while its sibling
  reaches$10,003,8shares and conserved$40basis; split replay is once-only.
- A foreign-owner portfolio was explicitly created through public HTTP with
  declared historical stock opening evidence. After one book closes, active
  sibling/foreign uncertainty holds are processed without touching its original
  payment, entitlement, cash or History.
- Privileged corruption is restricted to negative-test setup. Missing lifecycle,
  a ghost active lifecycle, and jointly corrupted retained confirmation names
  refuse without mutation. Every positive closure uses the actual public DELETE.

## Deviations and encountered issues

1. **[Rule3 — fixture prerequisite]** The owned retained strategy-event module
   imported the old0020 API fixture and seeded stock history without the new
   required gate. It now aliases the existing current0023 restricted fixture and
   takes the existing stock gate for its declared synthetic openings. No
   runtime admission or historical profile was relaxed. The initial setup
   failure is not counted as the qualifying RED.
2. **[Rule1 — SQL parameter typing]** The new read query's nullable cause
   parameters required explicit bigint types with asyncpg. A typed fixed CTE
   supplies them; all names/values remain bound, with no SQL interpolation of
   inputs. This was repaired before GREEN.
3. **[Rule3 — lock observer]** A migrator cannot see other roles' complete
   activity metadata. The first barrier diagnostic timed out; the observed
   blocking checks now use the owned test administrator, not a sleep or a
   fabricated ordering signal. No runtime role gained monitoring privileges.

Task2 strengthens already-existing SQL fences and therefore has a test-only
commit rather than a manufactured RED/GREEN product change. No stub, new
dependency, migration, operational secret, provider call or production action.
No authentication gate was encountered. Existing issue35 remains unchanged.

## Handoff

Independent review is required before Plan11. Plan09 adds the remaining
multi-instrument/successive-stock and management races. Plan15 still owns the
unrelated retained0020 creation-fixture mismatch and other whole-suite adaptation;
this plan corrected only its owned strategy-event module. Plan16 must add
`app/services/portfolio_lifecycle.py` to the100% critical list while retaining
all existing critical modules. Whole security/recovery, browser and actual new
owner UI/native200 outcomes remain18/19; none is inferred here. Keep work local.

## Self-Check: PASSED

All six intended source/test artifacts and the three task commits exist.
40complete affected cases pass at unchanged source, scoped static checks pass,
historical authority bytes are unchanged, and owned cleanup is complete.
No STATE/ROADMAP or requirement checkbox was updated by this executor.
