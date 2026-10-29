---
phase: 04-trading
plan: 02
subsystem: trading
tags: [decimal, money-math, tdd, settings]
requires: [04-01]
provides:
  - "backend/app/services/trade_math.py: plan_trade, cost_basis_after, TradeCosts, Plan, TradeRefused, q2/q8/floor8, MAX_VALUE"
  - "Settings: trade_spread, trade_fee_rate, trade_min_fee_usd, trade_min_order_usd"
affects: [04-06]
key-files:
  created:
    - backend/app/services/trade_math.py
    - backend/tests/test_trade_math.py
    - backend/tests/test_config_trading.py
  modified:
    - backend/app/core/config.py
decisions:
  - "D-04 interpretation: buy by $ compares the typed amount A (fee-inclusive, D-02) to the minimum order; quantity orders compare the $ notional at execution price"
metrics:
  tasks: 2
  completed: 2026-10-28
---

# Phase 4 Plan 02: Trade money math Summary

Pure `plan_trade` / `cost_basis_after` implementing D-01..D-07 (incl. D-06 minimum fee and sell fee cap) with explicit rounding at R1-R5 only, 100% line+branch coverage, plus validated trade settings.

## Commits
- 84b9705 `test(04-02)`: failing trade math and settings tests (RED)
- 7e14f35 `feat(04-02)`: trade money math and settings (GREEN)

## Results
- 45 trade-math tests (all plan worked examples asserted exactly; all passed against the plan's numbers on the first run), seeded invariants (seeds 4 and 2026: 5000 buy-by-$ cases each, 3000 buy-by-qty/sell cases each), 16 settings tests.
- `trade_math.py`: 100% line and branch coverage (94 stmts, 26 branches). Full backend suite 393 passed; ruff, ruff format, mypy clean.

## D-04 interpretation (recorded)
For a buy by $ amount, the minimum order applies to the typed amount A (the order size chosen, fee-inclusive per D-02), because D-06 needs a $1.00 buy to succeed with a $0.01 fee although its coin notional is $0.99. Quantity orders compare the $ notional; selling the exact whole position is allowed below the minimum.

## Deviations from Plan
Rule 2 (defensive additions, all tested):
- `invalid_order` when the execution price rounds to zero (avoids division by zero).
- Early `order_too_large` guard when the input value exceeds MAX_VALUE, before any quantize (avoids `InvalidOperation` on absurd input).
- Sells with quantity <= 0 are `below_minimum` (otherwise 0 of 0 held would pass as a "whole position").
- Note: the plan's `grep` acceptance for `Decimal\(...\)` is satisfied via the `D` alias with string literals only. Tests use `# noqa: S311` for the seeded `random.Random`.

## Known Stubs
None.

## Self-Check: PASSED
Files exist; commits 84b9705 and 7e14f35 present. STATE.md, ROADMAP.md, REQUIREMENTS.md untouched as instructed.
