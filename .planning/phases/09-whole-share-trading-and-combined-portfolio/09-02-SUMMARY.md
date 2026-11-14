---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "02"
subsystem: payments
tags: [stocks, decimal, whole-shares, money, shortcuts, tdd]
requires:
  - phase: 09-01
    provides: fixed whole-share, monetary and execution contracts
provides:
  - Exact ask-buy/bid-sell plans with zero fees and proportional basis
  - Bounded conservative Buy max and verified Sell all draft quantities
affects: [09-03, 09-06, 09-08]
tech-stack:
  added: []
  patterns: [64-place Decimal arithmetic, immutable money plans, bounded quantity search]
key-files:
  created:
    - backend/app/services/stock_trade_math.py
    - backend/tests/test_stock_trade_math.py
  modified: []
key-decisions:
  - Pure shortcut results are whole Decimal quantities; ContextOut Money serializes them as plain strings.
  - Preserve exact ninth-place midpoint separately from half-even eight-place Trade metadata.
  - Basis-capacity search is bounded to forty iterations and cannot exceed floor(cash/ask).
patterns-established:
  - All positive shortcuts pass the same exact planner before becoming drafts.
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-02, STKTR-03, STKTR-06]
duration: 7min
completed: 2026-11-11
---

# Phase 9 Plan 02: Exact Stock Money and Draft Quantities Summary

**Fee-free whole-share stock plans preserve exact source midpoints, cent cash and
proportional basis, with safely capped server-only quantity shortcuts.**

## Performance

- Started: approximately 2026-11-11T20:00:00Z (executor dispatch; no precise start recorded).
- Completed: 2026-11-11T20:06:29Z (final verification clock).
- Duration: approximately 7 minutes including scoped initial reads and gates.
- Tasks: 2/2.
- Files created: 2 source/test artifacts plus this summary.

## Accomplishments

- Positive integral twelve-digit quantities, finite positive NUMERIC(20,8)
  bid/ask and crossed-quote rejection precede planning. Inputs are never
  coerced from float, boolean or string. Cash/basis snapshots preserve the
  existing exact-cent accounting convention; invalid or overflowing states
  fail closed with fixed contract codes.
- Buy uses ask and sell uses bid, with zero commission and added spread.
  Multiply before one explicit half-even cent rounding. No crypto minimum
  notional or minimum fee is imported. Zero-cash buys cannot mint shares;
  legitimate tiny sells may produce zero cents without a new minimum policy.
- Preserve exact midpoint through nine decimal places; separately quantize
  legacy Trade midpoint metadata to eight places. Partial sells reuse the
  existing keyword-only cost_basis_after policy; full sale resets basis.
  Frozen plans contain cash/held/basis before-after; no database state changes.
- Buy max starts from conservative floor(cash/ask), caps quantity/held room and
  searches rounded notional against cash/basis capacity in at most forty
  steps. Every positive result passes plan_stock_trade. Sell all returns the
  entire verified holding or zero when absent/unrepresentable; no partial
  liquidation is mislabelled Sell all. Results only populate drafts.

## Task Commits

1. Task1 RED: `a0be558` — Reject fractional stock planning.
2. Task1 GREEN: `9df1773` — Plan exact whole-share stock trades.
3. Task2 RED: `b327fdd` — Bound stock shortcut holding capacity.
4. Task2 GREEN: `16b6c55` — Bound conservative stock quantity shortcuts.

Both RED gates demonstrated behavioral failure, not missing imports. The
zero-cost legacy baseline accepted fractional1.5; the naive shortcut returned
100 shares when remaining holding capacity was2. Their GREEN commits replace
those baselines with actual stock policies.

## Verification

All pytest commands used existing locked Python through
`uv run --no-sync --no-cache`, with guarded existing isolated test resources.
No fixture stack was started/stopped and no dev/production/provider access ran.

| Selector / command | Actual result | Measured time |
| --- | --- | --- |
| Task1 stock test RED | 1failed: fractional quantity accepted | 0.18s |
| stock math + existing trading schema Task1 GREEN | 77passed | 0.99s |
| Task2 stock math RED | 1failed/59passed: shortcut100 instead of2 | 0.38s |
| stock math + crypto math + both trading schemas, final scoped branch coverage | 186passed;72statements/24branches100% | 1.78s |
| Ruff format/check on both files; mypy on source | PASS;1sourcefile types | 0.482s combined wall |
| git diff --check, deletion and source stub scan | PASS; no deletions/TODO/FIXME/placeholders | <1s |

Acceptance assertions cover both sides, complete/partial basis, full-position
sales, immediate reuse of sale cash, exact cent ties, low ambient precision,
numeric boundaries/overflow, NaN/Infinity/fractional/non-Decimal rejection,
zero-cost buys, tiny asks, cash100/ask33.335 shortcut2 versus manual3,
capacity-limited drafts and input immutability. Final regression suite also
preserves all existing crypto arithmetic/schema expectations.

## Interfaces for Downstream Plans

- `plan_stock_trade(*, side, quantity, bid, ask, cash, held, cost_basis)` returns
  frozen `StockTradePlan`; invalid plans raise existing `TradeRefused` with
  invalid_quantity, insufficient_cash, insufficient_holding or numeric_range.
- Plan fields: side, quantity, bid, ask, exact_mid, mid (eight-place metadata),
  exec_price, notional, fee, cash_delta, cash_before/after, held_before/after,
  cost_basis_before/after and whole_position.
- `buy_max_quantity(*, bid, ask, cash, held, cost_basis)` and
  `sell_all_quantity(...)` return Decimal whole quantities, serialized as plain
  strings by the fixed ContextOut Money contract. Zero means disabled draft,
  not a valid order; malformed snapshots still raise numeric_range.

## Decisions Made

Follow the frozen contract and existing basis helper without changing crypto.
No new library API, package, schema, endpoint, network or privileged authority
is introduced. Monetary/quantity limits and midpoint metadata are distinct from
the exact saved stock source facts expected by later service/schema plans.

## Deviations from Plan

No feature-scope deviation. Parent owns shared STATE/ROADMAP/REQUIREMENTS;
these remain untouched by this executor. Assigned requirements are supported
pure arithmetic only and are not prematurely marked end-to-end complete.

## Issues Encountered

The first sandboxed test attempt could not open the isolated Redis socket;
scoped escalation allowed the existing guarded test fixture. It was not
counted as a behavioral RED gate. A Task2 test accidentally expected a nonzero
quantity for an otherwise correct zero-cost rejection; its assertion was
corrected before the final full affected suite. No unresolved issues or auth
gates remain.

## User Setup Required

None for isolated pure arithmetic. Actual provider/product rights, status
bootstrap/continuity, source freshness and Phase7/8 activation remain deferred.

## Next Phase Readiness

Ready for09-03 schema and09-06 financial transaction consumers. This plan
does not execute trades, write journals or demonstrate mixed-asset concurrency;
those remain downstream. No publication, private calls or live activation
authority is inferred.

## Self-Check: PASSED

Both created implementation/test files and all four task commits exist. All
final scoped behavioral/static/coverage gates pass. No stubs or new threat
surfaces remain; pure math performs no I/O or mutation. Unrelated `.claude/`
content is preserved.
