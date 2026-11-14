---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "01"
subsystem: api
tags: [stocks, decimal, contracts, authority, valuation]
requires:
  - phase: 08-corporate-action-safe-ownership
    provides: independent action and ownership safeguards
provides:
  - Exact whole-share stock request and immutable saved receipt schemas
  - Frozen fail-closed execution/status/valuation evidence and decisions
  - Fixed API, portfolio and successor SQL consumer contracts
affects: [09-02, 09-03, 09-05, 09-06, 09-09, 09-10]
tech-stack:
  added: []
  patterns: [assertion-first contracts, immutable evidence, separate historical marks]
key-files:
  created:
    - backend/app/schemas/stock_trades.py
    - backend/app/services/stock_trading_rules.py
    - backend/tests/test_stock_trading_schema.py
    - backend/tests/test_stock_trading_rules.py
    - .planning/phases/09-whole-share-trading-and-combined-portfolio/09-CONTRACTS.md
  modified: []
key-decisions:
  - Exact admission hashes bind PostgreSQL full-row JSONB text, retained alongside semantic validation.
  - Current status requires verified bootstrap and explicit contiguous transport within a strict60s lease.
  - Historical closed/halted marks retain source dates and independent permission/action/unit/calendar deadlines.
patterns-established:
  - Economic replay excludes expected execution price and precedes current eligibility.
  - Allowed execution decisions preserve exact frozen evidence for the final SQL guard.
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-03, STKTR-05, PORT-06, PORT-07, MKT-02]
duration: 11min
completed: 2026-11-11
---

# Phase 9 Plan 01: Stock financial and authority contracts Summary

**Exact whole-share schemas, immutable receipt facts and default-deny execution
rules distinguish current verified authority from dated historical marks.**

## Performance

- Started: 2026-11-11T19:47:50Z
- Completed: 2026-11-11T19:58:06Z
- Duration: 10m16s (11min rounded)
- Tasks: 2/2
- Files created: 5 implementation/test/contract files, plus this summary.

## Accomplishments

- Reject numeric/boolean/fractional/exponent/overflow stock quantities and
  nonplain confirmation prices without changing crypto coercion. Monetary
  outputs and stable bigint identities preserve string precision.
- Freeze quote, context, refusal, changed-price and versioned receipt fields;
  saved receipts retain historical cash/share-after without renewed deadlines.
- Bind permission hashes, identity, generations, action epochs, independent
  status continuity, session boundaries and source quote age in pure rules.
  Define priority refusals and strict equality expiration; current quotes never
  establish normal status. Reconnect/loss invalidates bootstrap/continuity.
- Preserve exact ninth-place midpoint for separately retained closed/halted
  marks, suppressing unknown/frozen/action/units/calendar-expired evidence.
- Document selected0013 schema/functions, final statement-snapshot boundary,
  keyword-only portfolio API and incomplete-total/class-allocation semantics.

## Task Commits

1. Task1 RED: `b286257` — Define strict stock input assertions.
2. Task1 GREEN: `40c6f48` — Freeze exact stock API contracts.
3. Task2 RED: `59f5d9e` — Assert default-deny stock authority.
4. Task2 GREEN: `3c765db` — Freeze independent stock authority rules.

Both RED gates failed behavioral assertions rather than imports: the legacy
baseline accepted JSON numeric quantity1; the provisional evaluator allowed
empty authority. Both implementations replaced their explicit RED baseline.

## Verification

All commands executed in backend using existing locked project interpreter;
`uv run --no-sync --no-cache` avoids changing packages/cache outside workspace.

| Command after uv prefix | Result | Measured pytest / command wall time |
|---|---|---|
| pytest tests/test_stock_trading_schema.py -q -x (RED) | 1failed/1passed: numeric quantity accepted | 0.30s /1.497s |
| pytest tests/test_stock_trading_schema.py -q -x (GREEN) | 34passed | 0.42s /1.622s |
| pytest tests/test_stock_trading_rules.py -q -x (RED) | 1failed: empty evidence allowed | 0.18s /1.226s |
| pytest tests/test_stock_trading_rules.py -q -x (initial GREEN) | 54passed | 0.30s /1.349s |
| pytest tests/test_stock_trading_schema.py tests/test_stock_trading_rules.py tests/test_stock_quote_rules.py -q (final) | 137passed | 0.67s /1.852s |
| ruff check app/services/stock_trading_rules.py tests/test_stock_trading_rules.py app/schemas/stock_trades.py tests/test_stock_trading_schema.py | PASS | combined static command0.732s |
| mypy app/services/stock_trading_rules.py app/schemas/stock_trades.py | PASS:2sourcefiles | same static command |
| ruff format source/test targets; git diff --check | PASS | formatter finished, no whitespace errors |

Acceptance gates: parser boundary/limits, concrete fields/codes/consumers,
status continuity/age separation, equality expiry, immutable accepted snapshots
and historical mark suppression all pass executable assertions. Source stub
scan found no TODO/FIXME/placeholder/pass. Optional None/unknown defaults are
intentional default-deny evidence, not a usable fake provider or unwired UI.

Isolated existing birja-test containers were inspected narrowly: matching
Compose project/path/service labels and exact pinned images, tmpfs-only storage,
no host/named mounts, only127.0.0.1:55432/56379. They were already healthy and
were neither started nor stopped. Redis autouse cleanup used test-only keys.
No application DB mutation, dev/prod inspection or provider call occurred.

## Decisions Made

Use canonical database-generated full admission-row hashes (SQL expression in
09-CONTRACTS) rather than inventing cross-language JSON formatting. Cap verified
status continuity at60s independently of event age; renew only explicitly trusted
contiguous next-sequence evidence. Keep exact accepted evidence immutable.

## Deviations from Plan

None in feature scope. Parent owns shared STATE/ROADMAP/REQUIREMENTS mutations;
this executor intentionally leaves them unchanged. Requirements are supported
contracts only and remain incomplete until end-to-end downstream proof, despite
the generic summary template's instruction to copy whole requirement completion.

## Issues Encountered

Sandbox initially denied Docker socket access and default uv cache creation.
Approved scoped escalation enabled narrow fixture inspection/test network access;
existing uv interpreter reused with no-sync/no-cache. Initial static findings
(production assert lint and Decimal exponent type union) were fixed before final
verification. Final self-review also added calendar-expiry regression for halted
marks. No unresolved issue or authentication gate remains.

## User Setup Required

None for this local contract plan. Actual permission/status bootstrap/transport
completeness and Phase7/8 data/action activation remain explicitly deferred.

## Next Phase Readiness

Ready for09-02 math and09-03 schema consumers using09-CONTRACTS. These schemas
are not routes or financial writers yet; later plans own runtime wiring, DB
concurrency, final SQL revalidation, recovery/TLS, browser/UI acceptance and full
critical100% coverage. No package, provider, publication or deployment authority
is inferred, and no entire requirement is marked complete by this plan.

## Self-Check: PASSED

All five owned artifact files exist. All four task commits exist and contain
only owned paths; final task commits delete no tracked files. Working-tree
whitespace check passes. Unrelated preexisting untracked .claude/ is preserved.
