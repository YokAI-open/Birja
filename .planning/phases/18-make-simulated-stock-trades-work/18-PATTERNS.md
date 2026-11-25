# Phase 18 implementation patterns

| Planned work | Existing analog | Reuse |
|---|---|---|
| Official halt snapshot polling | `backend/app/tasks/stock_scheduler.py`, `backend/app/tasks/stock_status.py` | Single scheduler process, bounded I/O and timeout, committed authority generations and conservative expiry. Use verified source snapshot semantics. |
| On-demand quote request and persistence | `backend/app/services/alpaca.py`, `backend/app/services/stock_quotes.py`, `reserve_account_attempt` in `backend/app/tasks/stock_scheduler.py` | Existing validated IEX REST client, per-instrument persistence gate, shared Redis quota and batched calls. |
| Immutable fill and final authority | `backend/app/services/stock_trading.py`, `backend/app/services/stock_eligibility.py`, `backend/alembic/sql/0017_stock_portfolio.sql` | Same immutable intent and receipt, lock/retry order, exact SQL evidence comparison and advancing `clock_timestamp()`. |
| Runtime and recovery migration | `backend/app/db/schema_contract.py`, `backend/app/db/portfolio_migrate.py`, revision `0023` and `deploy/backup-snapshot.py` | Pin the new revision, role privileges, exact recovery schema and retained predecessors. |
| Trade feedback | `frontend/src/pages/StockTradePage.tsx`, `frontend/e2e/stock-trades.spec.ts` | Keep existing market countdown, eligible preview, repricing, masked failure and receipt flow. |
