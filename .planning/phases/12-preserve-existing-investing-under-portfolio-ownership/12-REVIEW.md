---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17T00:00:00Z
depth: standard
diff_base: e14fa20753a008bab52afbe04c8f735faf5f9fd2
reviewed_head: d3c603e5a6584d6bba76c16a59496be0b6f4e6d2
requested_files: 230
files_reviewed: 73
files_reviewed_list:
  - backend/alembic/sql/0017_stock_portfolio.sql
  - backend/alembic/versions/0015_portfolio_expansion.py
  - backend/alembic/versions/0016_portfolio_association.py
  - backend/alembic/versions/0017_portfolio_ownership.py
  - backend/app/api/v1/legacy_finance.py
  - backend/app/api/v1/stock_trades.py
  - backend/app/api/v2/auth.py
  - backend/app/api/v2/history.py
  - backend/app/api/v2/me.py
  - backend/app/api/v2/portfolios.py
  - backend/app/api/v2/router.py
  - backend/app/api/v2/stock_trades.py
  - backend/app/api/v2/trades.py
  - backend/app/core/deps.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/schema_contract.py
  - backend/app/main.py
  - backend/app/models/trade.py
  - backend/app/models/user.py
  - backend/app/schemas/portfolios.py
  - backend/app/services/accounts.py
  - backend/app/services/auth.py
  - backend/app/services/corporate_actions.py
  - backend/app/services/dividends.py
  - backend/app/services/event_history.py
  - backend/app/services/history.py
  - backend/app/services/portfolio.py
  - backend/app/services/portfolios.py
  - backend/app/services/stock_ownership.py
  - backend/app/services/stock_trading.py
  - backend/app/services/trade_idempotency.py
  - backend/app/services/trading.py
  - backend/app/tasks/dividends.py
  - backend/tests/test_portfolio_migrate.py
  - deploy/backup-snapshot.py
  - deploy/backup.sh
  - deploy/configure-db.sh
  - deploy/deploy.sh
  - deploy/recovery-bundle.sh
  - deploy/restore-check.sh
  - deploy/tests/portfolio-sources.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/test-portfolio-browser-contracts.py
  - docker-compose.yml
  - frontend/src/App.tsx
  - frontend/src/api/auth.ts
  - frontend/src/api/client.ts
  - frontend/src/api/eventHistory.ts
  - frontend/src/api/history.ts
  - frontend/src/api/portfolio.ts
  - frontend/src/api/portfolios.ts
  - frontend/src/api/stockTrades.ts
  - frontend/src/api/trades.ts
  - frontend/src/components/HistoryEventDetails.tsx
  - frontend/src/components/PortfolioContext.tsx
  - frontend/src/components/PortfolioHoldings.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/components/StockSection.tsx
  - frontend/src/components/StockTradeReceipt.tsx
  - frontend/src/hooks/useEventHistory.ts
  - frontend/src/hooks/useHistory.ts
  - frontend/src/hooks/useHolding.ts
  - frontend/src/hooks/useMe.ts
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/hooks/useQuote.ts
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/useTrade.ts
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/StockTradePage.tsx
  - frontend/src/pages/TradePage.tsx
coverage: partial
files_unreviewed: 157
files_unreviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/sql/0017_dividend_portfolio.sql
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/event_history.py
  - backend/app/api/v1/history.py
  - backend/app/api/v1/me.py
  - backend/app/api/v1/portfolio.py
  - backend/app/api/v1/router.py
  - backend/app/api/v1/trades.py
  - backend/app/models/corporate_action.py
  - backend/app/models/dividend.py
  - backend/app/models/stock_execution.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/portfolio.py
  - backend/app/schemas/stock_trades.py
  - backend/app/schemas/trades.py
  - backend/tests/conftest.py
  - backend/tests/dividend_fixtures.py
  - backend/tests/fixtures/bootstrap-roles-0013.sql
  - backend/tests/helpers.py
  - backend/tests/portfolio_fixtures.py
  - backend/tests/stock_action_fixtures.py
  - backend/tests/test_accounts.py
  - backend/tests/test_auth_request_code.py
  - backend/tests/test_auth_session.py
  - backend/tests/test_auth_verify.py
  - backend/tests/test_config.py
  - backend/tests/test_config_prices.py
  - backend/tests/test_config_scheduler.py
  - backend/tests/test_corporate_actions.py
  - backend/tests/test_critical_coverage_config.py
  - backend/tests/test_db_connection.py
  - backend/tests/test_dev_bootstrap.py
  - backend/tests/test_dividend_authority.py
  - backend/tests/test_dividend_concurrency.py
  - backend/tests/test_dividend_corrections.py
  - backend/tests/test_dividend_payments.py
  - backend/tests/test_dividend_scheduler.py
  - backend/tests/test_dividend_schema.py
  - backend/tests/test_dividend_waits.py
  - backend/tests/test_email.py
  - backend/tests/test_event_history.py
  - backend/tests/test_event_history_api.py
  - backend/tests/test_event_history_cursor.py
  - backend/tests/test_health.py
  - backend/tests/test_history_api.py
  - backend/tests/test_history_service.py
  - backend/tests/test_migrations.py
  - backend/tests/test_portfolio_api.py
  - backend/tests/test_portfolio_authority.py
  - backend/tests/test_portfolio_crypto.py
  - backend/tests/test_portfolio_crypto_api.py
  - backend/tests/test_portfolio_dividend_authority.py
  - backend/tests/test_portfolio_dividends.py
  - backend/tests/test_portfolio_entitlements.py
  - backend/tests/test_portfolio_identity.py
  - backend/tests/test_portfolio_identity_api.py
  - backend/tests/test_portfolio_migrations.py
  - backend/tests/test_portfolio_ownership.py
  - backend/tests/test_portfolio_routes.py
  - backend/tests/test_portfolio_schema_admission.py
  - backend/tests/test_portfolio_scoped_history.py
  - backend/tests/test_portfolio_service.py
  - backend/tests/test_portfolio_snapshot.py
  - backend/tests/test_portfolio_splits.py
  - backend/tests/test_portfolio_stock_api.py
  - backend/tests/test_portfolio_stock_authority.py
  - backend/tests/test_portfolio_stock_ownership.py
  - backend/tests/test_portfolio_stock_trading.py
  - backend/tests/test_portfolio_valuation.py
  - backend/tests/test_ratelimit.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_action_resolutions.py
  - backend/tests/test_stock_catalog.py
  - backend/tests/test_stock_execution_authority.py
  - backend/tests/test_stock_execution_migrations.py
  - backend/tests/test_stock_isolation.py
  - backend/tests/test_stock_migrations.py
  - backend/tests/test_stock_ownership.py
  - backend/tests/test_stock_quotes.py
  - backend/tests/test_stock_scheduler.py
  - backend/tests/test_stock_sessions.py
  - backend/tests/test_stock_trades_api.py
  - backend/tests/test_stock_trading_concurrency.py
  - backend/tests/test_stock_trading_schema.py
  - backend/tests/test_stock_trading_service.py
  - backend/tests/test_stock_trading_waits.py
  - backend/tests/test_stock_valuation.py
  - backend/tests/test_trade_idempotency.py
  - backend/tests/test_trades_api.py
  - backend/tests/test_trading_concurrency.py
  - backend/tests/test_trading_schema.py
  - backend/tests/test_trading_service.py
  - deploy/backup-manifest.sql
  - deploy/db/bootstrap-roles.sql
  - deploy/tests/dividend-execution-fixture.py
  - deploy/tests/fixtures/portfolio-recovery-0017.json
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-portfolio-fixture-contracts.py
  - deploy/tests/test-portfolio-migration-runner.py
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-selected-cutover-contracts.py
  - deploy/verify-restore.py
  - frontend/e2e/auth.spec.ts
  - frontend/e2e/dividends-history.spec.ts
  - frontend/e2e/helpers.ts
  - frontend/e2e/markets.spec.ts
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/e2e/portfolio-history.spec.ts
  - frontend/e2e/portfolio-ownership.spec.ts
  - frontend/e2e/stock-trade-fixture.py
  - frontend/e2e/stock-trades.spec.ts
  - frontend/e2e/trade.spec.ts
  - frontend/src/App.test.tsx
  - frontend/src/api/auth.test.ts
  - frontend/src/api/eventHistory.test.ts
  - frontend/src/api/history.test.ts
  - frontend/src/api/portfolio.test.ts
  - frontend/src/api/portfolioReads.test.ts
  - frontend/src/api/portfolioTrades.test.ts
  - frontend/src/api/stockTrades.test.ts
  - frontend/src/api/trades.test.ts
  - frontend/src/components/HistoryEventDetails.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.test.tsx
  - frontend/src/components/StockSection.test.tsx
  - frontend/src/components/StockTradeReceipt.test.tsx
  - frontend/src/hooks/portfolioCrypto.test.tsx
  - frontend/src/hooks/portfolioHistory.test.tsx
  - frontend/src/hooks/portfolioStock.test.tsx
  - frontend/src/hooks/portfolioValuation.test.tsx
  - frontend/src/hooks/useAuthMutations.test.tsx
  - frontend/src/hooks/useEventHistory.test.tsx
  - frontend/src/hooks/useHistory.test.tsx
  - frontend/src/hooks/usePortfolio.test.tsx
  - frontend/src/hooks/usePortfolioTarget.test.tsx
  - frontend/src/hooks/useStockTrade.test.tsx
  - frontend/src/hooks/useTrade.test.tsx
  - frontend/src/pages/AccountPage.tsx
  - frontend/src/pages/HistoryPage.test.tsx
  - frontend/src/pages/HistoryPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/SignInPage.test.tsx
  - frontend/src/pages/StockTradePage.test.tsx
  - frontend/src/pages/TradePage.test.tsx
  - frontend/src/test/portfolioFixtures.ts
  - frontend/src/test/portfolioTargetFixture.ts
  - frontend/src/test/stockTradeFixtures.ts
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 12: Code Review Report

## Narrative Findings (AI reviewer)

### Summary and review boundary

The requested scope is the exact 230-path list in `/tmp/phase12-final-review-scope.json`, against the base and frozen head above. This report is **not a completed standard review of all 230 files**. The 73 paths listed in frontmatter received direct content or changed-section inspection, with cross-file tracing of portfolio ownership, execution, journal/cutoff authority, migration/role closure, frontend target lifetimes and unknown receipts. Large files were inspected incrementally or by relevant changed sections; this does not claim exhaustive full-line inspection of their unchanged contents. Remaining test and recovery-harness families still require review to satisfy the original all-file standard-depth assignment.

One source-confirmed BLOCKER was found. No second actionable finding was established. Passing qualification evidence (3,108 backend tests, critical coverage, frontend/browser checks, strict scans and the seven-stage encrypted recovery rehearsal) informed regression context but does not establish correctness of this missing case. No tests, provider calls, production operations, source edits or commits were performed for this review.

## Critical Issues

### CR-01 — BLOCKER: A historical dividend permanently blocks a portfolio's first purchase of that stock

**File:** `backend/alembic/sql/0017_stock_portfolio.sql:121–127`, rejection at `:157–158`  
**Related producer:** `backend/app/services/corporate_actions.py:931–950`, creation loop at `:1019–1071`

**Trigger:** A supported dividend has passed its verified cutoff and has been processed for an existing owner. Another active portfolio has never held or traded that stock and has no entitlement row for the event. That portfolio attempts its first otherwise admissible stock purchase. This also affects an existing user's original portfolio when buying a stock for the first time; it does not depend on future portfolio-creation UI.

**Issue:** The final execution authority query treats every supported historical dividend without an entitlement for the target portfolio as a pending boundary:

```sql
AND NOT EXISTS (
  SELECT FROM public.stock_dividend_entitlements en
  WHERE en.event_id = ev.id
    AND en.portfolio_id = t.portfolio_id
)
```

Once the cutoff has passed, the final authority function raises SQLSTATE `22023`. However, the entitlement producer only considers portfolios already represented by stock ownership movements, prior entitlements or holdings. A portfolio that has never owned this instrument is absent from that candidate set, so the worker creates no zero-quantity entitlement for it.

The purchase service reaches the final authority check after staging the trade and movement. The authority exception rolls back that transaction and becomes a quote-unavailable refusal. Consequently the tentative first movement never survives to make the portfolio eligible for the worker's candidate discovery. Further worker cycles and retries cannot repair this state: the portfolio remains unable to buy the stock after the historical dividend.

**Evidence:** Direct tracing of the final SQL predicate, its rejection condition, the sole runtime `StockDividendEntitlement` creation loop and stock execution's transactional final-authority call. No database reproduction was run; the parent is preserving this frozen review boundary before an isolated regression repair.

**Fix:** Make entitlement discovery and the final boundary obligation agree for portfolios with provably zero historical ownership. Either materialize legitimate zero-quantity snapshots for every root required by the validator, or explicitly and authoritatively exempt roots with no historical entitlement obligation. Preserve the instrument gate, active-root locking and final execution authority checks; do not merely remove the boundary guard for unresolved historical owners.

**Required regression:** Under the real restricted application role, process a historical dividend for owner A, then allow owner B's previously empty portfolio to execute its first purchase exactly once. Verify an identical replay returns the original result without duplicate financial effects. Cover a same-user sibling portfolio and a portfolio created after cutoff. Retain a negative case proving a genuinely unresolved historical owner is still refused.

## Remaining review coverage

The requested scope must remain open for the unreviewed paths, principally the broad backend test adaptations, frontend test/e2e fixture adaptations and large deployment recovery fixtures/contracts. The complete scope remains available in the named JSON; this report deliberately does not label those files reviewed or infer a clean result from qualification runs.

---
_Reviewer: gsd-code-reviewer; standard-depth partial review._

