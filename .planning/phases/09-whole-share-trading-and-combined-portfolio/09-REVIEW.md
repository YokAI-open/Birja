---
phase: 09-whole-share-trading-and-combined-portfolio
status: clean
review_mode: sequential-inline
reviewed: 2026-11-12
depth: deep
files_reviewed: 51
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
files_reviewed_list:
  - backend/app/schemas/stock_trades.py
  - backend/app/services/stock_trade_math.py
  - backend/app/services/stock_trading_rules.py
  - backend/app/services/stock_status_rules.py
  - backend/app/services/stock_status.py
  - backend/app/services/stock_eligibility.py
  - backend/app/services/stock_trading.py
  - backend/app/services/trade_idempotency.py
  - backend/app/services/stock_valuation.py
  - backend/app/services/stock_quotes.py
  - backend/app/services/stock_ownership.py
  - backend/app/services/corporate_actions.py
  - backend/app/services/portfolio.py
  - backend/app/services/portfolio_math.py
  - backend/app/services/trading.py
  - backend/app/tasks/stock_status.py
  - backend/app/tasks/stock_scheduler.py
  - backend/app/api/v1/stock_trades.py
  - backend/alembic/versions/0013_stock_execution.py
  - frontend/src/api/stockTrades.ts
  - frontend/src/api/portfolio.ts
  - frontend/src/api/stocks.ts
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/useStocks.ts
  - frontend/src/pages/StockTradePage.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/components/StockTradeReceipt.tsx
  - frontend/src/components/PortfolioHoldings.tsx
  - frontend/src/components/PortfolioAllocation.tsx
  - frontend/src/components/StockSection.tsx
  - frontend/src/components/StockAttribution.tsx
  - frontend/e2e/stock-trades.spec.ts
  - frontend/e2e/stock-trade-fixture.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/stock-runtime-fixture.py
  - deploy/tests/stock-execution-fixture.py
  - deploy/tests/ops-fixtures.py
  - deploy/backup-snapshot.py
  - deploy/verify-restore.py
  - deploy/configure-db.sh
  - deploy/scan-images.py
  - deploy/tests/test-backup.sh
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-stock-recovery-contracts.py
  - .github/workflows/ci.yml
  - docker-compose.yml
  - docker-compose.prod.yml
  - docker-compose.test.yml
  - docker-compose.ops-test.yml
---

# Phase 9 source review

The execution agent performed a distinct source-review pass. This is not an
independent-agent review: delegated executors lacked filesystem/shell access.
Earlier independent reviews of plans01–03 remain their own evidence. Scope is
plans01–13 summaries/commits and the final integration changes in14, with focused
cross-file inspection of execution, idempotency, eligibility/status, valuation,
stock routes, browser parsing/cache lifecycle and owned recovery/browser drivers.

## Narrative Findings (AI reviewer)

No open source findings in the reviewed scope. The complete local operational,
coverage and affected browser tail pass. Findings below were corrected during
execution; their earlier REDs remain evidence, not open current-source findings.

## Resolved findings

| Finding | Evidence and correction |
| --- | --- |
| Newly observed halt could leave a cached fresh portfolio mark visible | Behavioral REDd57ca27; FIXd85a3f7 suppresses the old fresh mark until server returns a dated compatible halted mark. Actual halted marks remain usable. Local redaction no longer invents a corporate-action reason. |
| Superseded quote/context could leave preview loading or old financial intent visible | Behavioral RED4332c45 and FIX11bad97; cancellation/auth/query identity and context replacement tests assert the resulting state. |
| A committed response with unavailable receipt must remain unresolved | API regression and explicit UNKNOWN classification; exact original key/body retained for user-initiated result checking. |
| CI browser startup inherited developer-style Compose resources |376b5e2 adds fixed owned project, private dummy env, explicit Compose inputs, tmpfs, loopback port, guarded helper and cleanup assertions. |
| Existing PostgreSQL pin now has one HIGH libxslt advisory | Fresh strict scan failed; official same-major18.7 replacement has zero HIGH/CRITICAL. Registry index/platform/config and recovery Compose hashes move together; installed tooling/services are untouched. |
| Reviewed18.6 source could not take its protected backup before the18.7 upgrade | Real selected-volume rollout failed safely before startup. Behavioral RED6cd3c59 and FIX03a2ec3 permit exactly18.6/18.7 client versions and reject18.70 lookalikes. All26backup contracts, complete exact-archive replay and old/new cutover pass. |
| Complete calendar made a fixed-date identity probe collide |1adc2cf chooses MAX(session_date)+1 while preserving sequence and unique/check assertions. Full retained0007–0013 proof passes. Actual scheduler quarantine denial remains required, never repaired. |

## Source checks

Stock execute looks up user-scoped global keys before market availability,
locks instrument then shared account/holdings, writes immutable ownership/facts,
forces deferred constraints and runs the current-authority invoker guard as its
last business SQL before commit. Only one clean quote-metadata rebuild is allowed;
selected-price changes require another explicit confirmation. Replay derives
original receipt from saved trade/facts/movement, not current catalogue or balance.

Portfolio reads financial inputs in one statement; later authority can suppress,
not replace, those values. Original quote-rights hashes and unit/safety epochs
prevent renewal laundering. Client parsers enforce exact string arithmetic and
identity, cache guards only remove authority, no optimistic cash/holding changes
or automatic mutation retry exists. Unknown attempts survive route changes in
owner-scoped memory and are discarded across auth identity lifecycle changes.

The isolated runtime fixture supplies synthetic external evidence only, calls
actual services with restricted TLS logins, and treats restored financial ACL
quarantine as an expected refusal. Owner-only restored replay/read and actual scheduler quarantine
denial must leave the authenticated manifest and identity state exact.

The final compatible archive5eb886d1 passes retained0007–0013 recovery, both
restricted verified-TLS lanes and actual selected-volume cutover/rollback.
Standalone historical SQL is pinned to its own revisions (e3d49f0), with actual
authority checks unchanged. All13SQL contracts and5nonroot native tests pass.
Backend2086/critical39modules100%, frontend590, full browser45plus expectedCSPskip
and final affected stock14 pass. Source969c301 additionally exports checked
script-free offline UI review pages. Plan15 owner acceptance remains required.

## Resolved finding locations

| Severity when observed | Location | Resolution |
| --- | --- | --- |
| Critical: ambiguous committed receipt | frontend/src/api/stockTrades.ts:581 | Execute receipt_unavailable remains UNKNOWN; frozen original key/body and explicit result check, regression in11. |
| Warning: newly observed halt | frontend/src/hooks/usePortfolio.ts:139 | d85a3f7 suppresses old fresh mark; compatible server dated halt remains permitted. |
| Warning: superseded context | frontend/src/hooks/useStockTrade.ts:206 |11bad97 invalidates retained preview/loading after identity or request replacement. |
| Critical: HIGH image finding | docker-compose.prod.yml:28 | c272b3c pins reviewed18.7; all-five strict scan0HIGH/CRITICAL, no waiver. |
| Warning: old-source dump refused | deploy/backup-snapshot.py:1194 |03a2ec3 exact18.6/18.7 allowlist and26contracts; actual old-source pre-start backup/restore now passes. |
| Warning: moving historical test head | deploy/tests/test-stock-recovery-contracts.py:280 | e3d49f0 exact historical probes, isolated synthetic owner provision in rollback-only transaction;13actual contracts pass. |

Cosmetic UI copy/density observations belong to09-UI-REVIEW; no styling
preference is promoted to a source-code correctness warning. This remains an
inline review, not an independent-agent review or production approval.
