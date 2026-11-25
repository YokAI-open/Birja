---
phase: 20-trade-and-value-stocks-from-search
plan: "06"
subsystem: trading
tags: [catalog, portfolio, stock-orders, idempotency]
requires:
  - phase: 20-04
    provides: Scoped executable quotes, permitted closed marks and reported halts
  - phase: 20-05
    provides: Exact issue action readiness
provides:
  - Owned catalog preview, confirmation and original receipt replay
  - One closed-market mark in the selected and owned quote routes
affects: [20-07, 20-08, 20-09]
requirements-addressed: [SL-01, SL-02, SL-04]
requirements-completed: []
---

# Phase 20 Plan 06 Summary

The owned catalog ticket previews and posts whole-share market orders under the exact stable issue, listing version and portfolio. It reuses the curated stock accounting and movement journal. A buy uses the ask, a sell uses the bid and the existing half-even rule rounds cash. Confirmation rechecks scope, current session, units, report and action evidence under database locks. Repricing returns a replacement preview for a new confirmation.

Receipt replay reads the original immutable trade and its catalog facts before market data. A retry must match the original owner, portfolio, catalog ID, listing, side, quantity and expected price. Provider identifiers and evidence stay on the server.

Both selected and owned price views use the newest permitted price and retain the last eligible mark from PostgreSQL when Redis is empty at market close. A closed view carries the verified reopening time and does not request a refresh. An eligible initial selection can request its first scoped quote while it awaits status. Confirmation still requires a current applicable report.

## Verification

- Twelve catalog context cases passed across the existing tests and three focused cold-cache cases. Both closed routes retained the displayed mark and next open while authority was current. Expired scope, a changed unit and a different session removed the mark without scheduling quote work.
- Nine real backend service and HTTP cases passed in 78.34 seconds. They covered ownership and CSRF, buy/sell, replacement preview, original receipt replay after a rename, stable-ID conflicts, shared cash competition with crypto, expiry while waiting for the account lock, known halt and first selection without status. App responses use private no-store.
- Three targeted cases passed in 23.06 seconds after the preview acquired its owned portfolio read lock before reading the market clock. The run included the restricted-role preview, the complete HTTP order and replay, and the existing curated replay after market denial.
- The open HTTP fixture uses a syntactically valid synthetic address. The closed fixture restores ordinary current grants before starting the app. Ruff, formatting, mypy and diff checks passed. The market inputs were synthetic.
