---
phase: 9
slug: whole-share-trading-and-combined-portfolio
status: in_progress
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-11
---

# Phase9 — Validation Strategy

Execution contract: plans01–14 have actual local automated evidence;15 owner UI/nativezoom answers remain pending. Source creation and behavioral RED/GREEN are recorded in plan summaries. Existing guarded PG+Redis, Vitest/RTL and Playwright run against owned fixtures, never dev/prod. HTTP external inputs are finite transport fakes; no provider keys/calls. See09-LOCAL-PROOF for final evidence and exact archive/source hashes.

## Exact per-task wave/requirement/threat map

| Task | Wave | Requirements | Threat IDs | Automated verification | Creation dependency |
| --- | --- | --- | --- | --- | --- |
| 09-01.1 | 1 | STKTR-01, STKTR-03, STKTR-05, PORT-06, PORT-07, MKT-02 | T-09-01-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trading_schema.py -q -x` | Existing isolated test framework; test target created in this task |
| 09-01.2 | 1 | STKTR-01, STKTR-03, STKTR-05, PORT-06, PORT-07, MKT-02 | T-09-01-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trading_rules.py -q -x` | Existing isolated test framework; test target created in this task |
| 09-02.1 | 2 | STKTR-01, STKTR-02, STKTR-03, STKTR-06 | T-09-02-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trade_math.py tests/test_trading_schema.py -q -x` | 09-01; test target created in this task |
| 09-02.2 | 2 | STKTR-01, STKTR-02, STKTR-03, STKTR-06 | T-09-02-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trade_math.py -q -x` | 09-01; test target created in this task |
| 09-03.1 | 3 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, MKT-02 | T-09-03-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_execution_migrations.py -q -x` | 09-01, 09-02; test target created in this task |
| 09-03.2 | 3 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, MKT-02 | T-09-03-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_execution_migrations.py tests/test_stock_execution_authority.py -q -x` | 09-01, 09-02; test target created in this task |
| 09-04.1 | 4 | STKTR-03, STKTR-05, PORT-06, MKT-02 | T-09-04-{V,A,I,D,R}; T-09-SC | `python3 deploy/tests/test-stock-recovery-contracts.py` | 09-03; test target created in this task |
| 09-04.2 | 4 | STKTR-03, STKTR-05, PORT-06, MKT-02 | T-09-04-{V,A,I,D,R}; T-09-SC | `bash deploy/tests/test-db-operations.sh --all` | 09-03; test target created in this task |
| 09-05.1 | 5 | MKT-02, STKTR-03, PORT-07 | T-09-05-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_status.py tests/test_stock_trading_rules.py -q -x` | 09-04; test target created in this task |
| 09-05.2 | 5 | MKT-02, STKTR-03, PORT-07 | T-09-05-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_status.py tests/test_stocks_api.py -q -x` | 09-04; test target created in this task |
| 09-06.1 | 6 | STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, MKT-02 | T-09-06-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_trade_idempotency.py tests/test_trading_service.py -q -x` | 09-02, 09-04, 09-05; test target created in this task |
| 09-06.2 | 6 | STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, MKT-02 | T-09-06-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trading_service.py tests/test_stock_ownership.py -q -x` | 09-02, 09-04, 09-05; test target created in this task |
| 09-07.1 | 7 | MKT-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06 | T-09-07-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trading_concurrency.py -q -x` | 09-06; test target created in this task |
| 09-07.2 | 7 | MKT-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06 | T-09-07-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trading_waits.py -q -x` | 09-06; test target created in this task |
| 09-08.1 | 8 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02 | T-09-08-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trades_api.py -q -x` | 09-07; test target created in this task |
| 09-08.2 | 8 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02 | T-09-08-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_trades_api.py tests/test_trading_schema.py -q -x` | 09-07; test target created in this task |
| 09-09.1 | 8 | PORT-06, PORT-07 | T-09-09-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_api.py -q -x` | 09-07; test target created in this task |
| 09-09.2 | 8 | PORT-06, PORT-07 | T-09-09-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_stock_valuation.py tests/test_portfolio_snapshot.py tests/test_portfolio_service.py -q -x` | 09-07; test target created in this task |
| 09-10.1 | 9 | STKTR-01, STKTR-03, STKTR-05, MKT-02 | T-09-10-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/api/stockTrades.test.ts src/api/stocks.test.ts` | 09-08; test target created in this task |
| 09-10.2 | 9 | STKTR-01, STKTR-03, STKTR-05, MKT-02 | T-09-10-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/hooks/useStockTrade.test.tsx src/hooks/useStocks.test.tsx` | 09-08; test target created in this task |
| 09-11.1 | 10 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02 | T-09-11-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/pages/StockTradePage.test.tsx src/components/StockTradeReceipt.test.tsx` | 09-10; test target created in this task |
| 09-11.2 | 10 | STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02 | T-09-11-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/components/StockSection.test.tsx src/pages/StockTradePage.test.tsx` | 09-10; test target created in this task |
| 09-12.1 | 9 | PORT-06, PORT-07 | T-09-12-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/api/portfolio.test.ts src/hooks/usePortfolio.test.tsx` | 09-09; test target created in this task |
| 09-12.2 | 9 | PORT-06, PORT-07 | T-09-12-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run test -- src/pages/PortfolioPage.test.tsx src/api/portfolio.test.ts src/hooks/usePortfolio.test.tsx` | 09-09; test target created in this task |
| 09-13.1 | 11 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-13-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run e2e -- e2e/stock-trades.spec.ts e2e/portfolio-history.spec.ts e2e/stock-actions.spec.ts e2e/trade.spec.ts` | 09-11, 09-12; test target created in this task |
| 09-13.2 | 11 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-13-{V,A,I,D,R}; T-09-SC | `cd frontend && npm run e2e -- e2e/stock-trades.spec.ts e2e/portfolio-history.spec.ts` | 09-11, 09-12; test target created in this task |
| 09-14.1 | 12 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-14-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest tests/test_critical_coverage_config.py -q -x` | 09-13; test target created in this task |
| 09-14.2 | 12 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-14-{V,A,I,D,R}; T-09-SC | `cd backend && uv run pytest --cov=app --cov-fail-under=80` | 09-13; test target created in this task |
| 09-15.1 | 13 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-15-{V,A,I,D,R}; T-09-SC | `git diff --check` + actual owner answer | 09-14; test target created in this task |
| 09-15.2 | 13 | MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07 | T-09-15-{V,A,I,D,R}; T-09-SC | `git diff --check` + actual owner answer | 09-14; test target created in this task |

## Sampling and mandatory longer gates

Task selectors target<60s; measure actual timings, split parameterized selectors if necessary. Every task has automated feedback; checkpoint15 additionally requires actual owner response. Wave integration reruns only affected suites. New behavioral features use assertion-first RED/GREEN, not missing-import RED. Pure migration/config/proof tasks may use existing harness assertion extensions rather than artificial tests. Do not call a source/whitespace check proof of financial correctness or acceptance.

Long final14 gates: full backend pytest coverage>=80%;100%critical statements+branches (all old and new modules mirrored in CLAUDE/CI/test_critical_coverage_config); Ruff/format/mypy; frontend fullcoverage>=80/lint/typecheck/prettier/build; pip-audit/npm audithigh; full actual isolated browser; current CI native/image contracts; strict five-image HIGH/CRITICAL scans includingunfixed. Actual commands come from current checked-in CI, no invented wrappers or reduced gates.

Schema04 gates and final14 replay are serial: `python3 deploy/tests/test-stock-recovery-contracts.py --postgres` and `bash deploy/tests/test-db-operations.sh --all`. Same retained encrypted archive covers0007–0013, exact rows/next identities/functions/ACLs/corruption, originals unchanged, populated upgrade/fresh restricted verified-TLS parity.04 proves direct synthetic0013 guard transaction compatibility before runtime consumers;14 additionally uses actual new stock service and immutable replay/portfolio/status consumers. Legacy contracts remain exact. Record timings/hash identities, actual skips and owned-resource cleanup; no fake short-budget claim for minutes-long operations.

## Required adversarial assertions

- 03: fractional/nonzero fee/missingfacts/orphan/mismatchedcause stock inserts fail; immutable facts UPDATE/DELETE and wrong role calls denied; unchanged prior crypto rows; function body/owner/search_path/ACL mismatch rejected independently.
- 05: normal requires current verified baseline+continuity+admission;60s ceiling/equality, reconnect/loss/partialbatch/out-of-order halt cannot revive normal. Quotes/actionhealth/heartbeat never mint status.
- 07: actual separate PG sessions and barriers at instrument/account/allholding/helper/flush/constraint waits. Current clock/session/status/admission/action/units/quote at final statement; failed staged effects fully rollback. Mixed and differentstock allholders contention, once-only key acrossasset, firstfill/split/exclusivecutoff/soldout history and known XID limit are asserted.
- 09: mixed financial inputs one statement snapshot, only old-or-new states, current authority can suppress but never mix oldunits/newprices. Unrounded midpoint, retained datedclosed/halt, original generations/retention, knownsubtotal/count/nullglobalPL/allpercentages, cash creditedonce.
- 10/12: exact money/stringbigints, malformed success UNKNOWN, one frozen key/body afterclose, fullRTT/currentidentity/epoch/queryowner/deadline guards in BOTH cache/view. Localexpiry cannot present an outdated knownsubtotal as current; no JS account recalculation.
- 13: real browser/API/PG happy paths and droppedresponse replay,200%nativezoom honesty, keyboard/mobile/desktop/live regions, incomplete/halt/closed/hold/accountswitch; crypto and Phase8 regressions.

## Human-only items

15.1 actual new ticket/reprice/receipt/unavailabledraft acceptance;15.2 actual combined full/incomplete portfolio acceptance and native200%zoom only if automation cannot exercise it. Prior Phase8/UI-contract approvals do not accept these new screens. Actual external product rights/status/bootstrap/continuity/latency/quotas remain owner-deferred/unverified and disabled; no redundant approval/campaign is required to continue isolated work.

## Sign-off after execution

- [ ] All30 tasks have actual automated evidence or actual owner answer, mapped to current source.
- [x] Exact0013/legacy recovery and both restricted verified-TLS lanes pass.
- [x] Financial concurrency/last-wait/current-authority and crypto regressions pass.
- [x]80%overall and100%critical statement/branch coverage, strict audits/scans and fullstatic pass.
- [ ] Actual browser/reflow/keyboard and honest nativezoom evidence pass.
- [x] Required code/security/UI/goal roles run as distinct sequential inline passes; no implementation blockers, all9requirements/16decisions mapped. Independence is not claimed; unavailable delegation fallback follows AGENTS/adapter.
- [ ] Owner accepts new UI; existing live deferrals preserved.
- [ ] Only then set nyquist_compliant and wave_0_complete from actual evidence.
