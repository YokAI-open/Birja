---
phase: 23-show-historical-market-prices
plan: "01"
subsystem: market-history
tags: [kraken, alpaca, decimal, exchange-calendar, fixtures]
requires:
  - phase: 20
    provides: "Exact listing identity, exchange calendar admission, and stock provider mapping"
provides:
  - "Strict instrument selector, range, history series and response contracts"
  - "Bounded fixed-host IEX and Kraken history adapters"
  - "Admitted equity session windows, UTC crypto windows, and comparable close changes"
  - "Dated source qualification evidence with live activation still gated"
affects: [23-02, 23-03, 23-04]
tech-stack:
  added: []
  patterns: [bounded-stream-parsing, fixture-provider-transport, separate-coverage-and-timeliness]
key-files:
  created:
    - backend/app/schemas/market_history.py
    - backend/app/services/market_history.py
    - backend/app/services/market_history_providers.py
    - backend/tests/test_market_history.py
    - backend/tests/test_market_history_providers.py
    - .planning/phases/23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md
  modified: []
key-decisions:
  - "Require applicable historical scope evidence separately from live quote evidence."
  - "Keep source coverage and regular-session timeliness independent in the response."
  - "Use full validated intervals and verified identity boundaries for historical comparisons."
requirements-addressed: [CHART-01, CHART-02, CHART-04]
requirements-completed: []
duration: 7min
completed: 2026-11-26
---

# Phase 23 Plan 01 Summary

Kraken USD OHLC and split-adjusted IEX bars now have provider adapters and a
shared history contract with decimal closes, verified interval windows,
explicit gaps, and independently measured coverage and timeliness.

## Implementation

- The typed query selects a crypto symbol, featured stock symbol, or exact
  catalog identifier and listing version for one of three supported ranges.
- Equity windows use the supplied admission generation and listing effective
  boundary. The normalizer excludes unclosed, off-session, and prior-identity
  observations, including around early closes and daylight saving changes.
- Both adapters use fixed endpoints and one requested instrument. Responses
  have a 256 KiB bound, IEX stops after two pages, and the normalizer rejects
  contradictory closes and caps output at 512 points.
- The 60-second publication grace applies to the source interval grid.
  Regular closures and genuinely missing intervals have separate gap values.
  Comparable changes use Decimal and half-even rounding.

## Tasks and verification

| Task | Commit | Result |
|---|---|---|
| Record source qualification | `bab6227` | Receipt present and diff checks passed |
| Implement adapters and normalization | `4f51d6e` | 36 targeted pytest tests passed with fixture HTTP transport. Ruff format and lint passed on all five Python files. Mypy passed on all three production files. |

The fixtures cover strict selectors, pagination, body limits, exact response
identity, split requests, precision, incomplete intervals, ticker reuse,
market closures, and sources that are delayed, partial, or both.

## Open source qualification

The public documentation review establishes candidate technical capabilities.
There were zero live calls. The applicable history collection, display,
derived-use and retention scopes, measured free-tier ceilings, and
representative live coverage remain unverified for both providers. The
live part of CHART-04 stays open. Plan 23-02 can use the deterministic fixture
path with its activated-source guards. [Source qualification receipt](23-SOURCE-QUALIFICATION.md)

## Deviations from plan

None. The plan expressly allows fixture execution when historical use or
access is unconfirmed.

## Self-Check: PASSED
