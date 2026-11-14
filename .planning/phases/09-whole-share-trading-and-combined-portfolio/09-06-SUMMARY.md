---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "06"
subsystem: trading
tags: [idempotency, money, postgresql, stock-receipts]
requires:
  - phase: 09-05
    provides: current independent execution authority
provides:
  - Global user-scoped economic order lookup shared with crypto
  - Read-only whole-share preview and draft context
  - Atomic shared-cash stock fill, immutable receipt and journal projection
  - Final invoker authority guard after every write and deferred constraint
affects: [09-07, 09-08, 09-10, 09-14]
tech-stack:
  added: []
  patterns: [instrument-account-holder lock order, original receipt replay]
key-files:
  created:
    - backend/app/services/trade_idempotency.py
    - backend/app/services/stock_trading.py
    - backend/tests/test_trade_idempotency.py
    - backend/tests/test_stock_trading_service.py
  modified:
    - backend/app/services/trading.py
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, MKT-02]
duration: 18min
completed: 2026-11-12
---

# Plan09-06: Atomic stock execution and original receipts

Global economic keys now conflict across assets before current market checks.
Stocks buy at ask/sell at bid with zero fees, and share the original Account.

## Task commits and evidence

- Task1 RED f04b90a: crypto returned stale_price for an existing stock key.
  GREEN354b349: global lookup; 33 tests passed1.83s with unchanged crypto math.
- Task2 RED d26c35c: actual admitted preview refused instead of producing exact
  read-only economics. GREENdc397cf: real buys, partial sales, sold-out basis,
  immutable replay, current refusals and late-failure rollback.
- Review REDc0037e4: halted context disclosed a future quote. FIXe7e3a47 uses
  independent historical valuation and its purge deadline before display.

Final required service/idempotency/crypto/ownership gate: **153passed20.76s**.
stock_trading163statements/38branches and trade_idempotency11statements/2branches
are **100% covered**, no partial branches. Scoped Ruff/format/Mypy pass.
No new packages, provider calls or production writes.

## Contracts

`stock_trading.quote(db,*,user_id,order:QuoteIn,settings)->QuoteOut`,
`context(db,*,user_id,symbol,settings)->ContextOut`,
`execute(db,*,user_id,order:TradeIn,settings)->(FillOut,created)`.
`PriceChanged.detail` is the frozen PriceChangedOut, with old/new price and cash
movement differences. API mapping remains08. Confirmation price is excluded
from economic key identity. Server max is only a draft.

NEW execution takes instrument gate then the same Account row, checks the key
again, and uses append_stock_movement for deterministic all-holder locking and
the ONLY holding/basis mutation. Cash changes once. Original receipt fields
come from Trade, StockFillFacts and the immutable movement economic timestamp;
replay joins no current catalogue/rights/holding. It survives sale, rename,
inactive catalogue and revoked rights; changed economic payload conflicts.
Missing/malformed historical facts refuse rather than fabricate a receipt.

After actual helper reads/writes, semantic evidence is loaded again. All effects
flush; deferred integrity runs; assert_stock_execution_current is LAST business
SQL, followed only by commit. Actual same-generation authority changes at that
boundary, DB/constraint errors, ownership refusal and cancellation leave exact
pre-state finances. Unique-conflict recovery rolls back before original replay.

## Review and remaining work

See09-06-REVIEW.md for distinct inline review provenance and resolved finding.
Real multi-session waits, opposing-side quote update behavior, action cutoff and
mixed contention are Plan07; current conservative post-helper metadata change
refuses safely until its planned concurrency refinement. API/frontend/portfolio,
actual restored service proof and full release gates remain08–15. Whole phase
requirements remain pending. Existing external activation deferrals persist.
No provider, production, B2, timer, publication or deployment action occurred.
