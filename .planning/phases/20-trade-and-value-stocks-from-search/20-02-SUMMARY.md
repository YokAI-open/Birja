---
phase: 20-trade-and-value-stocks-from-search
plan: "02"
subsystem: database
tags: [alembic, postgresql, stock-catalog, execution, corporate-actions]
requires:
  - phase: 20-01
    provides: Stable financial coin IDs and revision 0026 catalog evidence tables
provides:
  - Final PostgreSQL authority and immutable listing evidence for catalog fills
  - Scoped catalog corporate-action authority alongside the existing routines
affects: [20-03, 20-04, 20-05, 20-06, 20-07, 20-08]
tech-stack:
  added: []
  patterns: [SQL final authorization under transaction fences, pinned migration sources]
key-files:
  created:
    - backend/alembic/sql/0026_stock_catalog_execution.sql
    - backend/alembic/sql/0026_stock_catalog_actions.sql
    - backend/tests/test_stock_catalog_sql_authority.py
    - backend/tests/test_stock_catalog_sql_actions.py
  modified:
    - backend/alembic/versions/0026_stock_catalog_finance.py
key-decisions:
  - Keep the original curated finalizer byte-for-byte identical.
  - Bind every new catalog fill to the exact retained receipt evidence and current listing.
requirements-addressed: [SL-01, SL-03, SL-04]
requirements-completed: []
---

# Phase 20 Plan 02 Summary

PostgreSQL checks the scope and effective market evidence at the end of a catalog stock order and preserves the exact listing and evidence on its receipt.

## Execution handoff

- `public.assert_catalog_stock_execution_current(trade_id, user_id, expected)` compares the supplied metadata with `stock_fill_facts.authority`. Both JSON objects require the string fields `portfolio_id`, `coin_id`, `catalog_id`, `listing_id` and `provider_asset_id`. The database independently looks up the booked trade, portfolio, movement, quote, action coverage, halt report, permissions and calendar. Persist `stock_fill_facts.observed_at` from `stock_catalog_financial_quotes.observed_at`. The source quote must be strictly younger than 120 seconds. The existing deferred fill guard enforces whole shares, ask or bid, and half-even cash and basis arithmetic.
- After the trade and receipt are flushed, insert `stock_catalog_fill_evidence` with the exact durable listing, admissions, report and unit evidence. The new deferred checks require the adjunct on new catalog trades and reject an unrelated adjunct. Existing receipts can replay from persisted evidence under their original owned portfolio conditions after a renewal or listing change.
- Take shared catalog advisory lock `1026019025` before the per-instrument transaction lock, then the portfolio root. Before the final statement, flush writes, run deferred constraints and take the shared report lock `(1326459824, 1)`. Catalog proof and identity publishers use an exclusive catalog fence. The report publisher must avoid taking earlier catalog or instrument locks while it holds the exclusive report fence.
- Scoped financial admissions use exact account, server, issue, listing, provider asset and feed. For `catalog_execution` on `iex`, the normalized `bid`, `ask`, `event_at` and `collected_at` each require `collection`, `execution`, `storage` and `backup`. For `catalog_halt` on `nasdaq-rss`, the same purposes apply to `report_digest`, `event_at`, `valid_until` and `state`. For `catalog_actions` on `alpaca-corporate-actions`, `provider_event_id`, `symbol`, `event_type`, `process_date` and `terms` each need `collection`, `derivation`, `storage` and `backup`.
- The catalog action coverage row and the shared action state must match on scoped admission, journal origin, coverage window, cursor, observation and lease. A hold, a changed applied split revision or a pending action at its cutoff refuses the order. The existing empty pre-cutoff portfolio rule still permits a first purchase with no historical dividend obligation.
- Plan 20-03 grants the app execution of the final statement and its invoker scope helper, read access to the referenced financial tables, and insert/read access to the fill adjunct. The existing admission column projection suffices. The admission's private `reference` column stays inaccessible to runtime roles. The scheduler will need read access to the scoped financial tables, narrowly assigned publication writes and scope-helper execution only where its existing call path needs it.

## Migration and verification

Revision `0026` pins its data, execution and action SQL companions by SHA-256. The wrapper passes verified SQL through directly so JSON in a routine body stays intact. Empty downgrade restores the five patched functions from the pinned existing revisions while retaining their object identities and grants. The revision refuses downgrade when catalog financial rows, reserved stock coins or expanded scope records are retained.

The catalog action branch ties each revision to its original issue and label. Its dividend recheck compares the scoped calendar and action evidence, and its deferred split check compares the posted movements with final holding quantities and basis. The operator path retains the established resolution entry point.

Six unchanged refusal cases passed before the final SQL changes. Those checks covered stale quotes, changed halt reports, revoked scope, listing and unit changes, and the calendar account mismatch. The final pinned SQL passed nine affected cases in 85 seconds of test execution, including the exact half-even fill, immutable receipt, action generation, cash and missing-evidence refusals, legacy routine round trip, dividends, corrections and exact split holdings. The operator test passed in 9.95 seconds after adding the normal schema-usage grant to its isolated fixture. Together the runs covered all 16 cases. Ruff lint and formatting and `git diff --check` passed. Runtime admission remained at `0025` during these migration tests.
