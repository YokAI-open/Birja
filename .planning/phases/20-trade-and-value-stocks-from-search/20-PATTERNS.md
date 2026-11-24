# Phase 20 implementation patterns

The [research](20-RESEARCH.md) records exact constraints and existing code
entry points. Carry forward these patterns when writing new modules.

| Phase 20 responsibility | Closest existing code |
|---|---|
| Stable issue binding and reviewed promotion | `backend/app/models/stock_catalog.py`, `backend/app/services/stock_catalog_publish.py` for advisory lock, current generation, scope validation and idempotent writes |
| Exact schema and retained compatibility | `backend/alembic/versions/0025_stock_catalog.py`, `backend/app/db/{schema_contract,portfolio_bootstrap,portfolio_migrate}.py`, `deploy/db/bootstrap-roles.sql` for immutable migration, exact ACLs and explicit retained revision |
| Scoped quote scheduler and report authority | `backend/app/services/stock_catalog_quote_demand.py`, `backend/app/tasks/{stock_catalog_quotes,stock_scheduler,stock_halts}.py` for token coalescing, fixed batch, current report lease and shared quota |
| Owned preview, confirmation and retry | `backend/app/api/v2/{stock_catalog,stock_trades}.py`, `backend/app/services/{stock_trading,trade_idempotency}.py`, `backend/alembic/sql/0024_stock_halt_snapshot.sql` for owned targets, short waits and final SQL authority |
| Action coverage, posting and receipts | `backend/app/tasks/stock_actions.py`, `backend/app/services/{corporate_actions,stock_action_reconciliation,dividends}.py`, `backend/alembic/sql/0017_dividend_portfolio.sql` for repeated event ingestion and protected durable effects |
| Valuation and historical labels | `backend/app/services/{portfolio,stock_valuation,event_history}.py` for two coherent reads, incomplete totals and immutable receipt fields |
| Trade UI and stack proof | `frontend/src/pages/{StockTradePage,StockCatalogTradePage}.tsx`, `frontend/src/hooks/{useStockTrade,useStockCatalog}.ts`, `frontend/e2e/stock-catalog.spec.ts`, `deploy/tests/test-stock-catalog-recovery.sh` for session scoping, responsive flows and retained encrypted recovery |
