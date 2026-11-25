---
phase: 20-trade-and-value-stocks-from-search
plan: "01"
subsystem: database
tags: [alembic, postgresql, stock-catalog, financial-identity]
requires:
  - phase: 19-search-the-nyse-and-nasdaq-catalog
    provides: Versioned listing identity, reviewed provider mapping and independent display scope
provides:
  - Stable financial identity for a reviewed catalog issue
  - Revision 0026 data contracts for scoped quotes, reported status, action coverage and fill evidence
affects: [20-02, 20-03, 20-04, 20-05, 20-06, 20-07, 20-08]
tech-stack:
  added: []
  patterns: [Exact issue and listing foreign keys, restricted migrator promotion]
key-files:
  created:
    - backend/alembic/sql/0026_stock_catalog_finance.sql
    - backend/alembic/versions/0026_stock_catalog_finance.py
    - backend/app/models/stock_catalog_finance.py
    - backend/app/services/stock_catalog_promotion.py
    - backend/tests/test_stock_catalog_finance_migration.py
    - backend/tests/test_stock_catalog_promotion.py
  modified:
    - backend/app/models/price.py
    - backend/app/models/__init__.py
    - backend/app/services/stock_catalog_quotes.py
    - backend/app/tasks/stock_catalog_import.py
key-decisions:
  - A promoted issue uses a stable internal symbol and an independent financial grant tied to the exact listing.
  - The expanded catalog lane uses its own binding and evidence. Its internal coin is inactive in legacy lookups.
requirements-addressed: [SL-01, SL-03, SL-04]
requirements-completed: []
completed: 2026-11-24
---

# Phase 20 Plan 01 Summary

A reviewed catalog issue now has a permanent financial coin ID. Repeating promotion or promoting a verified new listing version preserves that ID and all existing economic records.

## Financial identity and evidence

- Revision `0026` adds `stock_catalog_instruments`, `stock_catalog_financial_quotes`, `stock_catalog_status`, `stock_catalog_action_coverage` and `stock_catalog_fill_evidence`. The binding uses `catalog_id` as primary key, a unique `coin_id`, the current exact `listing_id`, reviewed `admission_id` and original `promoted_at`. Evidence keeps the `(listing_id, catalog_id)` and `(catalog_id, coin_id)` references so a historical fact still identifies its original listing after a rename. Fill evidence references the existing stock receipt by `trade_id`.
- The new coin uses `@<catalog_id>`, where the ID is a canonical positive signed bigint, and `is_active=False` for legacy lookups. User-facing names belong to listings and historical receipts. Promotion initializes action health to `unknown` and leaves reported status absent. It creates no ownership, cash movements or trade receipts.
- `promote-instrument` requires an admitted `0026` connection, an authenticated restricted migrator, explicit `STOCK_DATA_ACCOUNT` and `STOCK_DATA_SERVER`, and canonical `--catalog-id`, `--listing-id` and `--admission-id`. The service uses catalog transaction lock `1026019025` and verifies the active generation, exact listing, current source and provider mapping, one USD share, and provider and symbol ownership before touching the binding.
- The `catalog_execution` scope requires exact `account`, `server`, signed-bigint string `catalog_id` and `listing_id`, `provider_asset_id` and `feed` set to `iex`. Each of `bid`, `ask`, `event_at` and `collected_at` requires `collection`, `execution`, `storage` and `backup`. Source and provider proofs remain independent. `catalog_mark`, `catalog_halt` and `catalog_actions` have separate admission IDs for the later scoped gates. Phase 19 display-cache permission remains independent.
- `load_catalog_financial_binding` returns the current exact binding and its earliest authority expiry. The retained binding and history references allow later receipt replay when authority has expired or a new listing has replaced the original.

## Migration and verification

- The pinned data DDL SHA-256 is `eb4a44fd9a2812aa693607db00d7d53240d8afb4d7e0bd1305035b1e15845a04`. The initial `0026` revision wrapper SHA-256 is `3c4f00db9637826b03b00e20a3a25e8046db911c292af6e497db80016445e070` before the planned companion integration.
- Git comparison confirmed both retained `0025` files are byte-identical. The SQL SHA-256 is `7665f5df6c828f681f6d7db7dda8b4cbf1a19d4f645fa4003fec94c1a5fa32fa`. The revision SHA-256 is `cd1890bfec3b1dc4b638fd3e86c9217d6eb331be3e895f2443b74fd88d078826`.
- Five focused tests passed on disposable PostgreSQL in 43.87 seconds. They confirmed the exact `0025` schema and economic snapshot round trip, refusal to downgrade with retained binding, stock namespace or scope, idempotent promotion, verified rename, stale approval refusal, and crypto and provider identity separation. The final ticker-reuse selector passed in 9.70 seconds after tightening the test fixture's active-listing selection. The tests used staged synthetic inputs without starting the app or contacting a provider.
- Ruff lint and formatting, mypy, compilation, CLI canonical ID smoke checks and `git diff --check` passed. Existing `publish` and `stage-assets` ID parsing was retained.

## Deviation and handoff

The promotion service reuses Phase 19's mapping validation from `stock_catalog_quotes.py` with the same account and server inputs. This small additional edit keeps the identity and unit review in one place.

Plan 20-02 adds SQL execution and action authority, including fill evidence immutability. Plan 20-03 adds runtime privileges and exact `0026` schema admission. The guarded CLI cannot promote through the runtime's current `0025` admission. Production provider access and stock activation remain outside this plan.

## Self-Check: PASSED

The planned source, test files and verification receipt are present. The phase orchestrator owns the Git commits and shared planning updates.
