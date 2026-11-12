---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "08"
subsystem: api
tags: [authentication, csrf, stock-orders, immutable-receipts]
requires:
  - phase: 09-07
    provides: verified financial service and concurrency
provides:
  - Actual authenticated stock quote, fill and own context HTTP routes
  - No-store success, auth, validation, known refusal and uncertain errors
  - Exact persisted wire receipt on both new fills and replay
affects: [09-10, 09-11, 09-14]
tech-stack:
  added: []
  patterns: [thin routes, private response boundary, original key recovery]
key-files:
  created:
    - backend/app/api/v1/stock_trades.py
    - backend/tests/test_stock_trades_api.py
  modified:
    - backend/app/api/v1/router.py
    - backend/app/services/stock_trading.py
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02]
duration: 8min
completed: 2026-11-12
---

# Plan09-08: Actual private stock HTTP contracts

Task1 RED04067a0: authenticated preview404. GREEN77a4001 wires actual routes
through api/v1/router.py, which main already includes; no redundant main wiring.
Task2 ea2472b exercises actual finance over authenticated HTTP, not substitute
route services. No schema contract or package change was necessary.

HTTP proof also exposed differing decimal scales in new versus replay JSON.
Both now refresh exact persisted Trade/facts after flush, BEFORE constraints and
final guard, so wire receipts match deeply. No new business await follows guard.

Final serial gate `/tmp/birja-phase09-08-final.log`: **224passed58.92s**;
API66statements/8branches, execution176statements/40branches and global keys
11statements/2branches: **100%**, no partial branches. Additional HTTP matched-
split regression passes1test2.08s after that gate; no source change followed.
Scoped Ruff/format/Mypy pass. Earlier HTTP/schema/legacy gate91passed7.75s.

Auth/CSRF precede financial effects; request symbols, quantity, expected price,
UUID and forbidden user/authority/cash inputs validate at the boundary. Private
route wrapper sets no-store and Cookie/Authorization Vary on success and errors,
including validation/auth failures. Known codes preserve409/422 contracts.
Unknown domain or response failures produce a generic uncertain500, never SQL,
provider or credential details and never an assertion that no fill occurred.

Actual HTTP verifies read-only preview/context, exact ask/bid/zero fees,
replacement price/cash difference and explicit confirmation, opposite-side-only
change, immutable replay after sale/rename/inactive/revoked rights and split,
user isolation, cross-asset key conflicts, sale→crypto→stock cash reuse, original
starting_cash and unchanged crypto fees. A fault wrapper calls the REAL service
and only then throws to simulate response loss after commit; same original key
recovers without another effect. No fake financial success is used.

Review09-08-REVIEW.md is a distinct inline pass, not independent. API source uses
frozen01 models; frontend remains10–13, mixed portfolio09 and final gates14–15.
Whole requirements remain pending. No provider, production, B2, installed-tool,
timer, push, merge or deployment operation occurred; live7/8 deferrals persist.
