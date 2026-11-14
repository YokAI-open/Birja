---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "09"
subsystem: portfolio
tags: [mixed-assets, exact-money, snapshots, historical-rights]
requires:
  - phase: 09-07
    provides: actual shared-cash stock execution and accounting history
provides:
  - Exact known subtotal, unvalued count and Cash/Stocks/Crypto classes
  - One financial SQL statement plus suppress-only current stock authority
  - Independently dated fresh/closed/halted marks with original permission bounds
  - Explicit null totals/allocations and unsafe unit-derived cost suppression
affects: [09-10, 09-12, 09-13, 09-14]
tech-stack:
  added: []
  patterns: [coherent scalar financial snapshot, original-rights proof, conservative suppression]
key-files:
  created:
    - backend/app/services/stock_valuation.py
    - backend/tests/test_stock_valuation.py
  modified:
    - backend/app/services/portfolio_math.py
    - backend/app/services/portfolio.py
    - backend/app/schemas/portfolio.py
    - backend/tests/test_portfolio_math.py
    - backend/tests/test_portfolio_api.py
    - backend/tests/test_portfolio_snapshot.py
requirements-completed: []
requirements-supported: [PORT-06, PORT-07]
duration: 24min
completed: 2026-11-12
---

# Plan09-09: Honest mixed portfolio and dated original-rights marks

Task1 RED9c72830: no known subtotal/class contract. Pure GREEN844f957 gives exact
64-digit math, midpoint9 support, alphabetical ticker/numeric-ID ordering,
nullable class amounts and ALL unavailable allocations when incomplete. Existing
crypto basis/fee/dust/large-value tests remain unchanged. Zero denominators stay
null; credited dividend cash enters once only through Account.cash.

Task2 RED72dbda3: actual stock fill was unpriced. GREEN64c8611 reads own cash/start,
all positive positions, crypto prices, stock source/session/status/action/units
and original quote permission proof in ONE statement snapshot. A second stock-
only authority query may suppress original values, never substitute new cash,
quantities or prices. Crypto-only reads still use exactly one statement.

Review RED689567b: pure math could keep a supplied midpoint with units_safe=false.
64c8611 also suppresses that mark, timestamp, derived return and average cost;
independent stored basis remains. Separate inline review is09-09-REVIEW.md.

## Rights and snapshot decisions

StockQuote retains a generation but no historical terms row. To avoid inventing
retention rights without a schema change, the oldest immutable fill authority
for that instrument/quote generation supplies its original full-row quote hash
and validity bounds. They must match CURRENT approved terms and cover source
collection. Missing proof or same-generation changed terms suppresses valuation.
A properly refreshed new quote generation can acquire its own proof through an
actually permitted new fill; renewal cannot launder an old generation/deadline.
This conservative behavior is explicit, not a claim of provider approval. No
schema, grant or retained recovery identity changed.

Fresh marks use exact bid/ask midpoint. Closed/verified halt retain their original
source date beyond120s only within original/current rights, source retention,
current independent status/calendar/action/units and a verified source session.
No weekend extension is assumed. Exact consumed split markers may permit a
compatible dated mark while conservative NEW execution still stays blocked.
Uncertain actions/epochs hide marks and unit-derived cost; missing prices never
mean zero. Current authority cannot revive old-unit financial rows.

Wire additions and bounded38-integer/9-fraction plain decimal parser contract are
in09-CONTRACTS.md. StockMark is nested under HoldingOut.stock_mark; crypto gets
null. Source/bounds/authority are null when unavailable, with fixed reason and
units_safe. Financial values remain strings, IDs strings; no JS arithmetic added.

## Actual verification

Final `/tmp/birja-phase09-09-final.log`: **66passed14.45s**, all three critical
modules **171statements/42branches100%**, no partial branches. Scoped Ruff,
format and Mypy pass. Real controlled commits prove old mixed cash/stock/crypto
prices and quantities remain coherent, with whole new result on the next call.
Post-snapshot unit, safety, mapping, continuity and permission changes suppress;
new quote data cannot replace an old source price. Actual HTTP, strict deadline
equality, missing/revoked rights, closed/halted, split and renewal tests pass.
Read-only tests assert exact unchanged financial state.

Client integration/new UI, full backend/frontend/browser/security/image and
actual restored-service gates remain10–15. Whole requirements remain pending.
No provider/production/B2/timer/installed-tool/publication change occurred.
