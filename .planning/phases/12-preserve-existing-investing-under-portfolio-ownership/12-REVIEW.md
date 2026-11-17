---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: standard
coverage: complete_changed_file_scope
reviewed_head: 328fe2d8ac28fc35b879e480dc4e1df692ebdbeb
diff_base: e14fa20753a008bab52afbe04c8f735faf5f9fd2
files_reviewed: 232
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/sql/0017_dividend_portfolio.sql
  - backend/alembic/sql/0017_stock_portfolio.sql
  - backend/alembic/versions/0015_portfolio_expansion.py
  - backend/alembic/versions/0016_portfolio_association.py
  - backend/alembic/versions/0017_portfolio_ownership.py
  - backend/app/api/v1/auth.py
  - backend/app/api/v1/event_history.py
  - backend/app/api/v1/history.py
  - backend/app/api/v1/legacy_finance.py
  - backend/app/api/v1/me.py
  - backend/app/api/v1/portfolio.py
  - backend/app/api/v1/router.py
  - backend/app/api/v1/stock_trades.py
  - backend/app/api/v1/trades.py
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
  - backend/app/models/corporate_action.py
  - backend/app/models/dividend.py
  - backend/app/models/stock_execution.py
  - backend/app/models/trade.py
  - backend/app/models/user.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/portfolio.py
  - backend/app/schemas/portfolios.py
  - backend/app/schemas/stock_trades.py
  - backend/app/schemas/trades.py
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
  - backend/tests/test_portfolio_dividend_first_buy.py
  - backend/tests/test_portfolio_dividends.py
  - backend/tests/test_portfolio_entitlements.py
  - backend/tests/test_portfolio_identity.py
  - backend/tests/test_portfolio_identity_api.py
  - backend/tests/test_portfolio_migrate.py
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
  - deploy/backup-snapshot.py
  - deploy/backup.sh
  - deploy/configure-db.sh
  - deploy/db/bootstrap-roles.sql
  - deploy/deploy.sh
  - deploy/recovery-bundle.sh
  - deploy/restore-check.sh
  - deploy/tests/dividend-execution-fixture.py
  - deploy/tests/fixtures/portfolio-recovery-0017.json
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/portfolio-sources.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-portfolio-browser-contracts.py
  - deploy/tests/test-portfolio-fixture-contracts.py
  - deploy/tests/test-portfolio-migration-runner.py
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-portfolio-smoke-image.py
  - deploy/tests/test-selected-cutover-contracts.py
  - deploy/verify-restore.py
  - docker-compose.yml
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
  - frontend/src/App.tsx
  - frontend/src/api/auth.test.ts
  - frontend/src/api/auth.ts
  - frontend/src/api/client.ts
  - frontend/src/api/eventHistory.test.ts
  - frontend/src/api/eventHistory.ts
  - frontend/src/api/history.test.ts
  - frontend/src/api/history.ts
  - frontend/src/api/portfolio.test.ts
  - frontend/src/api/portfolio.ts
  - frontend/src/api/portfolioReads.test.ts
  - frontend/src/api/portfolioTrades.test.ts
  - frontend/src/api/portfolios.ts
  - frontend/src/api/stockTrades.test.ts
  - frontend/src/api/stockTrades.ts
  - frontend/src/api/trades.test.ts
  - frontend/src/api/trades.ts
  - frontend/src/components/HistoryEventDetails.test.tsx
  - frontend/src/components/HistoryEventDetails.tsx
  - frontend/src/components/PortfolioContext.tsx
  - frontend/src/components/PortfolioHoldings.tsx
  - frontend/src/components/PortfolioTargetBoundary.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/components/StockSection.test.tsx
  - frontend/src/components/StockSection.tsx
  - frontend/src/components/StockTradeReceipt.test.tsx
  - frontend/src/components/StockTradeReceipt.tsx
  - frontend/src/hooks/portfolioCrypto.test.tsx
  - frontend/src/hooks/portfolioHistory.test.tsx
  - frontend/src/hooks/portfolioStock.test.tsx
  - frontend/src/hooks/portfolioValuation.test.tsx
  - frontend/src/hooks/useAuthMutations.test.tsx
  - frontend/src/hooks/useEventHistory.test.tsx
  - frontend/src/hooks/useEventHistory.ts
  - frontend/src/hooks/useHistory.test.tsx
  - frontend/src/hooks/useHistory.ts
  - frontend/src/hooks/useHolding.ts
  - frontend/src/hooks/useMe.ts
  - frontend/src/hooks/usePortfolio.test.tsx
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/usePortfolioTarget.test.tsx
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/hooks/useQuote.ts
  - frontend/src/hooks/useStockTrade.test.tsx
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/useTrade.test.tsx
  - frontend/src/hooks/useTrade.ts
  - frontend/src/pages/AccountPage.tsx
  - frontend/src/pages/HistoryPage.test.tsx
  - frontend/src/pages/HistoryPage.tsx
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/SignInPage.test.tsx
  - frontend/src/pages/StockTradePage.test.tsx
  - frontend/src/pages/StockTradePage.tsx
  - frontend/src/pages/TradePage.test.tsx
  - frontend/src/pages/TradePage.tsx
  - frontend/src/test/portfolioFixtures.ts
  - frontend/src/test/portfolioTargetFixture.ts
  - frontend/src/test/stockTradeFixtures.ts
files_unreviewed: 0
resolved_findings: 2
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
integrated_qualification: pending
---

# Phase 12 — Aggregated Code Review

## Narrative Findings (AI reviewers)

The original230 changed-file scope is fully accounted for, plus two new
regression files from the independently reviewed repairs. No source finding
remains open. Combined-source qualification and final goal verification remain
pending; earlier passing results are not relabelled as tests of this source.

## Exact Coverage and Method

| Receipt | Scope | Method |
|---|---|---|
| Initial review atd3c603e |73|Direct runtime/authority/migration/frontend content or relevant changed sections with surrounding call-chain context |
|12-REVIEW-BACKEND-REMAINING.md|93|Full remaining backend files and independent retained-schema/economic assertions |
|12-REVIEW-FRONTEND-OPS-REMAINING.md|63|Full remaining executable frontend/operations/test files |
|12-REVIEW-CATALOGUE.md|1|Complete structured SQL/catalogue/privilege data comparison |
|12-REVIEW-CR01.md|8repair paths|Complete amended authority/regression and independently reconstructed source/catalogue pins |
|12-REVIEW-CR02.md|3repair paths|Complete immutable runtime factory, CI loader and provenance tests |

The original four sets are disjoint and their union equals the requested230
paths. Repair scopes add two new regressions; the unique total is232. This
records changed-file scope and each receipt's actual method, not an exhaustive
re-read of every unchanged source line. The initial partial report and original
finding text remain at05426f7 in this same path. Component reports are retained.

## Resolved Findings

**CR-01 — BLOCKER, source-resolved.** Historical dividends prevented a never-
owner's first stock buy. Independently reviewed4c16a30 is integrated asac0f64f.
The dividend-only zero-obligation exemption requires complete cutoff coverage,
no earlier root/instrument trade or movement and exact prior journal quantity/
basis. Historical/unknown owners, incomplete history, closed roots and pending
splits remain guarded. No zero payment/History, new lock or grant is introduced.
Actual restricted-role RED, six regressions/106 affected cases and logical
recovery pass at the repair source.12-REVIEW-CR01.md reproduces all exact pins.

**CR-02 — BLOCKER, source-resolved.** Cold recovery used a workstation-only cached
image. Independently reviewed2ef1f58 is integrated as328fe2d. The factory now
builds the actual committed backend's declared Dockerfile runtime target with
source/HEAD/context checks and immutable ID/Config/RootFS authentication. No
cached fallback or application overlay remains. Six new regressions/37 CI cases
and an actual nonroot build/package-identity proof pass at the repair source.
Integrated actual cold restoration remains required, not inferred from build.

## Remaining Qualification

Security112/112 and targeted11/11 controls are source-closed; UI24/24 and both
owner UI/native200% responses are recorded. See12-SECURITY-RECHECK.md and UAT.
All28 execution plans are complete, but repaired combined-source security,
image and same-archive recovery qualification plus final goal verification are
pending. Phase12 and requirements are not complete. Phase7's six live gaps/OFF
admissions remain separate. No new dependency, provider, production or
publication action is included; keep work local.
