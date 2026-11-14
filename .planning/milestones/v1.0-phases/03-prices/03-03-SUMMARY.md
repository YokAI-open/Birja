---
phase: 03-prices
plan: 03
subsystem: api
tags: [kraken, httpx, prices, decimal]
requires:
  - phase: 03-prices/02
    provides: coins/prices tables, services/prices.py
provides:
  - services/price_rules.py (parse_price, mid_from_ticker, evaluate_price, Candidate)
  - services/kraken.py (TICKER_URL, KrakenError, TickerSource, fetch_tickers)
  - price_rules.py on the 100% CI critical-path list (ci.yml and CLAUDE.md identical)
affects: [03-05]
key-files:
  created:
    - backend/app/services/price_rules.py
    - backend/app/services/kraken.py
    - backend/tests/test_price_rules.py
    - backend/tests/test_kraken.py
    - backend/tests/fixtures/kraken_ticker_ok.json
  modified:
    - .github/workflows/ci.yml
    - CLAUDE.md
metrics:
  completed: 2026-10-28
---

# Phase 3 Plan 03: Price rules and Kraken client Summary

Pure acceptance rule (invalid/crossed rejected, >25% move held until 3 polls agree within 5%) and a Kraken Ticker client with at most 3 attempts, exponential backoff plus jitter, and 200-with-error handling.

## Commits

- dfc3276 test(03-03): failing tests for the price acceptance rule (RED)
- 6e44087 feat(03-03): price rules + CI/CLAUDE.md critical list (GREEN)
- Task 2 feat(03-03) commit: Kraken client, tests, fixture (see git log)

## Verification

- Full backend suite: 244 passed, coverage 99.79%; `price_rules.py` 100% line+branch.
- ruff check, ruff format --check, mypy clean. ci.yml validated with actionlint 1.7.7 (clean).
- Tests contain no literal Kraken host (respx with assert_all_mocked).
- One-off live read-only GET (A7, comma encoding): `fetch_tickers(client, ["XXBTZUSD","XDGUSD"])` printed `['XDGUSD', 'XXBTZUSD']`. The default httpx `%2C` encoding works; no fallback needed.

## Deviations from Plan

- Task 2 was not split into separate RED/GREEN commits: tests and implementation were committed together (Task 1 has the RED/GREEN pair).
- [Rule 1 - lint] ruff B008/S101 flagged the default `SystemRandom().random` argument and an assert; moved the jitter to a module constant `_JITTER` and initialised `last` instead of asserting.

## Known Stubs

None.

## Self-Check: PASSED
