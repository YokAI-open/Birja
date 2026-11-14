---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "05"
subsystem: market-data
tags: [status, authority, postgresql, scheduler, eligibility, retention]
requires:
  - phase: 09-04
    provides: exact0013 recovery and restricted verified-TLS authority
provides:
  - Bounded finite status normalization and independently admitted real persistence
  - Default startup/loss invalidation without a live transport
  - One materialized authority snapshot with exact monetary strings and DB time
  - Conservative execution eligibility and independent discovery status/action display
affects: [09-06, 09-07, 09-08, 09-09, 09-10, 09-14]
tech-stack:
  added: []
  patterns: [explicit continuity leases, full-row authority hashes, materialized evidence snapshots]
key-files:
  created:
    - backend/app/services/stock_status_rules.py
    - backend/app/services/stock_status.py
    - backend/app/services/stock_eligibility.py
    - backend/app/tasks/stock_status.py
    - backend/tests/stock_trade_fixtures.py
    - backend/tests/test_stock_status.py
  modified:
    - backend/app/services/stocks.py
    - backend/app/schemas/stocks.py
    - backend/app/tasks/stock_scheduler.py
    - backend/tests/test_stocks_api.py
key-decisions:
  - Only explicit complete baseline/contiguous finite observations can renew a maximum60-second status lease.
  - Current display permission cannot authorize permanent receipts and retained recovery copies.
  - Raw admission/status snapshots stay exact; data-use deadlines conservatively narrow session_valid_until.
  - Compatible post-split display may remain available while a cached action boundary still blocks execution.
requirements-completed: []
requirements-supported: [MKT-02, STKTR-03, PORT-07]
duration: 115min
completed: 2026-11-12
---

# Plan09-05: Independent status and conservative eligibility

**Verified finite status is persisted after real post-wait authority checks,
and discovery enables execution only from independent current permissions,
status, calendar, actions, compatible units and sufficiently recent quotes.**

## Task commits

1. Task1 RED `ecfd047`: a complete verified baseline was still unknown (actual
   assertion failure, not an import error).
2. Pure rules GREEN `21c70fb`; real persistence/fixtures `105e20e`.
3. Task2 RED `98b36eb`: the existing disabled stock cycle retained a saved
   pre-restart normal state (actual PostgreSQL assertion failure).
4. Task2 GREEN `732af2c`: finite cycle, shared snapshot, conservative discovery
   contract and complete failure/expiry/rights coverage.

## Behavior and proof

- Unknown defaults; maximum20 instruments/1000events/1MiB entire UTF8 envelope.
  Baseline, continuity, complete segment and end marker are explicit. Missing/
  ambiguous frames, loss, reconnect, older normal after a halt and exhausted
  generations cannot mint normal. Exact retries preserve the old deadline.
- Actual scheduler-owned SQL persists one gated instrument per caller transaction.
  Full current status/reference admission hashes and mapping are reread after
  awaited writes/flush; semantic validity and advancing DB time are rechecked.
  Real row-lock barriers prove complete rollback after same-generation rights
  changes, mapping changes, permission expiry and status lease expiry. Financial
  rows/counts/cash/holdings/basis remain unchanged.
- Default status source is None and clears saved continuity. Nonnull finite
  injection requires explicit test settings. There is no socket/REST adapter,
  configurable production fake, credential path or outbound attempt. Future
  actual transport still needs independently verified rights/suitability and
  the existing shared account attempt quota.
- A materialized bounded SQL snapshot precedes database time sampling. Quote
  numbers are text before JSON decoding; no monetary floats or stale ORM
  identity objects authorize execution. Repeatable-read and unsupported universe
  growth fail closed. Discovery uses current final-statement quotes.
- All five execution products require existing semantic rights plus explicit
  durable_accounting/backup_restore/durable-accounting retention scope. Short-term
  halt display remains independent. Quotes/status beyond data-use retention are
  rejected even if still fresh; deadlines also bind the final invoker guard.
- Real calendar construction/validation runs over an explicitly synthetic
  external dataset for deterministic open/closed financial fixtures. Its cache
  is cleared on success/setup failure; the DB clock/readers are never mocked.
  Official holiday/DST/early-close tests still use the real package dataset.
- Halted/frozen/unknown, closed sessions, uncertain actions, unsafe units, stale
  quotes and missing permissions remain independent refusal conditions. A verified
  halt does not override action uncertainty. No actual new fill is implemented yet.

## Verification

| Command / selector | Actual result | Measured time |
| --- | --- | --- |
| Initial pure baseline RED |1failed |0.23s |
| Pure normalization + existing rules |112passed |0.54s |
| Persistence/real expiry/rights/fixture integration |121passed |5.36s |
| Scheduler default RED |1failed |1.38s |
| Status/discovery/collection integration |157passed |29.64s |
| Retention RED |1failed: expired but executable quote |1.84s |
| Settled affected integration |250passed |30.63s |
| Affected six critical modules |268passed plus2post-split cases;593statements/182branches100% |34.96s +2.49s |
| Final full backend `pytest --cov=app --cov-fail-under=80` |1889passed/77warnings;99.85%overall |202.08s |
| All35 critical modules, including four new modules |3534statements/1154branches100% |<1s coverage report |
| Whole backend Ruff + format |PASS;158files |<1s |
| Whole backend Mypy |PASS;76sources |1.13s |

Final logs: `/tmp/birja-phase09-05-backend-final.log` and
`/tmp/birja-phase09-05-critical-all.log`. Focused coverage includes discovery,
collection and status failure handling. No gate was waived; warnings are the
existing calendar/pandas deprecations. Formal CI critical-list expansion and
browser/image/full recovered-service proof remain Plan14 obligations.

## Review and deviations

Review found and fixed source-reference bounds, whole-envelope size before
partitioning, retention use beyond freshness, durable receipt permissions and
terminal generation invalidation. Six affected critical modules now have no
missing line/branch. See09-05-REVIEW.md for separate inline review provenance and
no remaining blocker/high finding. Agents were unavailable for file/tool work;
no independent review is claimed.

Shared SQL helpers moved from discovery into the new eligibility module, retaining
one source of truth. Existing discovery test expectation now names the real missing
permission instead of phase_disabled. No package, schema, function or role-grant
change was needed. No source/runtime stub remains.

## Next obligations

Continue09-06 actual stock preview/context/fill and global cross-asset idempotency,
then07 real financial races. Use the interfaces added to09-CONTRACTS.md; candidate
evidence is not authorization. Portfolio09 must preserve one financial snapshot.
Frontend decoder integration is planned in10, new screens11–13 and owner acceptance15.
Whole requirements remain pending end-to-end phase verification.

Phase7 live quote evidence and Phase8 action activation remain owner-deferred.
No provider, production, B2, timer, push/PR/merge or deployment change occurred.

## Self-Check: PASSED

All ten implementation/test artifacts exist; four cited task commits resolve.
Final full backend/static checks and all35 critical modules pass. Plan remains
a local status/eligibility foundation, with no claim of working new stock fills
or completed phase/UI/live acceptance.
