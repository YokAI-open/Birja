---
phase: 20-trade-and-value-stocks-from-search
plan: "04"
subsystem: pricing
tags: [catalog, iex, market-halts, scheduler]
requires:
  - phase: 20-03
    provides: Restricted 0026 runtime roles and scoped market evidence
provides:
  - One bounded quote worker for selected and held stocks
  - Redis-independent latest permitted closed-market marks
  - Scoped projection of report and issue-specific halts
affects: [20-06, 20-07, 20-08, 20-09]
requirements-addressed: [SL-01, SL-02, SL-04]
requirements-completed: []
---

# Phase 20 Plan 04 Summary

The quote worker combines exact listing selections and a bounded cursor over distinct current owned holdings. The lanes share the existing rolling account budget. The worker rechecks the active issue, version, session, units and rights before persisting normalized quote values. A held stock with no returned quote does not keep the page from advancing.

`read_catalog_financial_mark` reads the permitted mark directly from PostgreSQL. The shared listing and provider checks in `stock_catalog_promotion.py` permit an authorized display mark after the execution lease ends. The read follows the verified latest closed session, the applicable unit epoch and the effective mark and calendar deadlines.

The halt loop shares one report download across the curated lane and bounded catalog projections. It can project the current report for a newly selected issue. A newer report expires superseded catalog records under the report fence before replacements are written. Projection checks an exact venue and dated ticker or alias. A notice that could match but lacks enough identity evidence blocks trading on that issue until its status can be verified. The coverage limits remain as approved in Phase 18. [Nasdaq report cadence](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) · [Nasdaq field definitions](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes)

## Verification

- All 25 distinct quote-scheduler and halt cases passed across the combined run and focused continuation. The final four modified quote cases passed in 29.03 seconds. The report-rollover fixture passed after using a monotonically later observation for the new synthetic report. No live provider call was made.
- The cases covered one shared report fetch, venue and dated alias ambiguity, market-wide notices, stale prior status, the selected/held queue, a missing first quote, expired and revoked scope, distinct current units, and an authorized prior-session price with empty Redis.
- Ruff, formatting, targeted mypy and diff checks passed. The integrated user-facing price and ticket responses are tracked in Plan 06.
