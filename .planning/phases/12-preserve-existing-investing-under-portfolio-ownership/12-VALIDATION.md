---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: planning
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-14
---

# Phase12 Validation Strategy

28 plans,56 tasks,18 waves. Independent checker pending. All commands below are planned execution, not passed evidence. No runtime/provider/production/install work occurred in planning. ASVS level1, high block; preserve80% overall and100% critical branch coverage, strict dependency audits and all five actual image scans.

## Sampling and Infrastructure

Existing locked pytest with real isolated PostgreSQL roles/TLS, Vitest, Playwright and retained ops runners. Run focused task command after each implementation, then family regression before plan close. Focused target120s is unmeasured. Full coverage, builds/scans and serial real cold recovery may exceed target and are explicit exceptions.12-27 performs full source-bound qualification; drift invalidates it.

## Exact Per-Task Verification Map

T-12-NN-01/02/03 identify each plan's owner/disclosure, integrity/privilege and once-only/refusal risks; SC enforces no dependency change with final27 strict proof. Each plan contains concrete mitigation ownership and commands.

| Task | Wave | Requirements | Threats | Automated command | Proof creation/dependency owner | Status |
|---|---:|---|---|---|---|---|
| 12-01-01 | 1 | PFUND-03, PFIN-03, PSAFE-03 | T-12-01-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_migrations.py --collect-only -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans none | Not executed |
| 12-01-02 | 1 | PFUND-03, PFIN-03, PSAFE-03 | T-12-01-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_ownership.py tests/test_portfolio_authority.py --collect-only -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans none | Not executed |
| 12-02-01 | 2 | PFUND-03, PSAFE-03 | T-12-02-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'root or metadata'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1 | Not executed |
| 12-02-02 | 2 | PFUND-03, PSAFE-03 | T-12-02-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'holding or trade or retry'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1 | Not executed |
| 12-03-01 | 3 | PFUND-03, PSAFE-03 | T-12-03-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'stock or closure or entitlement'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,2 | Not executed |
| 12-03-02 | 3 | PFUND-03, PSAFE-03 | T-12-03-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_authority.py -q -k 'lineage or entitlement or payment'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,2 | Not executed |
| 12-04-01 | 4 | PFUND-03, PSAFE-03 | T-12-04-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'expansion or association_guard'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,3 | Not executed |
| 12-04-02 | 4 | PFUND-03, PSAFE-03 | T-12-04-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'backfill or preserved or resume or downgrade'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,3 | Not executed |
| 12-05-01 | 5 | PFIN-02, PFIN-03, PSAFE-03 | T-12-05-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_stock_authority.py --collect-only -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 4 | Not executed |
| 12-05-02 | 5 | PFIN-02, PFIN-03, PSAFE-03 | T-12-05-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_stock_authority.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 4 | Not executed |
| 12-06-01 | 5 | PFUND-03, PSAFE-03 | T-12-06-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_dividend_authority.py --collect-only -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 4 | Not executed |
| 12-06-02 | 5 | PFUND-03, PSAFE-03 | T-12-06-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_dividend_authority.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 4 | Not executed |
| 12-07-01 | 6 | PFUND-03, PSAFE-02, PSAFE-03 | T-12-07-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'final or inventory or immutability'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,4,5,6 | Not executed |
| 12-07-02 | 6 | PFUND-03, PSAFE-02, PSAFE-03 | T-12-07-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_schema_admission.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,4,5,6 | Not executed |
| 12-08-01 | 7 | PSAFE-02, PFIN-02, PFUND-03 | T-12-08-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'resolver or identity_contract or malformed'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,2,3,7 | Not executed |
| 12-08-02 | 7 | PSAFE-02, PFIN-02, PFUND-03 | T-12-08-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_identity.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 1,2,3,7 | Not executed |
| 12-09-01 | 8 | PSAFE-02, PCTX-01 | T-12-09-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_identity_api.py -q -k 'versioned or cookie or refresh'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8 | Not executed |
| 12-09-02 | 8 | PSAFE-02, PCTX-01 | T-12-09-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_identity_api.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8 | Not executed |
| 12-10-01 | 8 | PFIN-02, PFIN-03 | T-12-10-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_crypto.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8 | Not executed |
| 12-10-02 | 8 | PFIN-02, PFIN-03 | T-12-10-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_crypto_api.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8 | Not executed |
| 12-11-01 | 9 | PFIN-02, PFIN-03, PSAFE-03 | T-12-11-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_stock_trading.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8,10,12 | Not executed |
| 12-11-02 | 9 | PFIN-02, PFIN-03, PSAFE-03 | T-12-11-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_stock_api.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 8,10,12 | Not executed |
| 12-12-01 | 8 | PFUND-03, PFIN-02, PSAFE-03 | T-12-12-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_stock_ownership.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,8 | Not executed |
| 12-12-02 | 8 | PFUND-03, PFIN-02, PSAFE-03 | T-12-12-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_splits.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,8 | Not executed |
| 12-13-01 | 9 | PFUND-03, PSAFE-03 | T-12-13-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_entitlements.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 6,12 | Not executed |
| 12-13-02 | 9 | PFUND-03, PSAFE-03 | T-12-13-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_dividends.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 6,12 | Not executed |
| 12-14-01 | 10 | PVIEW-03, PCTX-01, PFUND-03 | T-12-14-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_valuation.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 10,11,13 | Not executed |
| 12-14-02 | 10 | PVIEW-03, PCTX-01, PFUND-03 | T-12-14-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_scoped_history.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 10,11,13 | Not executed |
| 12-15-01 | 11 | PSAFE-02, PVIEW-03, PFIN-02, PCTX-01 | T-12-15-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_routes.py -q -k 'metadata or history or valuation'` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,9,10,11,14 | Not executed |
| 12-15-02 | 11 | PSAFE-02, PVIEW-03, PFIN-02, PCTX-01 | T-12-15-01/02/03/SC | `cd backend && uv run pytest tests/test_portfolio_routes.py tests/test_portfolio_identity_api.py tests/test_portfolio_crypto_api.py tests/test_portfolio_stock_api.py -q` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,9,10,11,14 | Not executed |
| 12-16-01 | 10 | PSAFE-03, PFUND-03 | T-12-16-01/02/03/SC | `python3 deploy/tests/test-dev-bootstrap.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,13 | Not executed |
| 12-16-02 | 10 | PSAFE-03, PFUND-03 | T-12-16-01/02/03/SC | `python3 deploy/tests/test-portfolio-migration-runner.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 7,13 | Not executed |
| 12-17-01 | 12 | PFUND-03, PSAFE-03 | T-12-17-01/02/03/SC | `python3 deploy/tests/test-portfolio-recovery-contracts.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15,16 | Not executed |
| 12-17-02 | 12 | PFUND-03, PSAFE-03 | T-12-17-01/02/03/SC | `python3 deploy/tests/test-portfolio-recovery-contracts.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15,16 | Not executed |
| 12-18-01 | 13 | PFUND-03, PSAFE-03 | T-12-18-01/02/03/SC | `python3 deploy/tests/portfolio-execution-fixture.py --help` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 17 | Not executed |
| 12-18-02 | 13 | PFUND-03, PSAFE-03 | T-12-18-01/02/03/SC | `python3 deploy/tests/test-ci-ops.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 17 | Not executed |
| 12-19-01 | 12 | PSAFE-02, PCTX-01 | T-12-19-01/02/03/SC | `cd frontend && npm run test -- --run src/api/auth.test.ts` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15 | Not executed |
| 12-19-02 | 12 | PSAFE-02, PCTX-01 | T-12-19-01/02/03/SC | `cd frontend && npm run test -- --run src/hooks/usePortfolioTarget.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15 | Not executed |
| 12-20-01 | 13 | PFIN-02, PFIN-03, PVIEW-03 | T-12-20-01/02/03/SC | `cd frontend && npm run test -- --run src/api/portfolioTrades.test.ts` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15,19 | Not executed |
| 12-20-02 | 13 | PFIN-02, PFIN-03, PVIEW-03 | T-12-20-01/02/03/SC | `cd frontend && npm run test -- --run src/api/portfolioReads.test.ts` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 15,19 | Not executed |
| 12-21-01 | 14 | PFIN-02, PFIN-03 | T-12-21-01/02/03/SC | `cd frontend && npm run test -- --run src/hooks/portfolioCrypto.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 20 | Not executed |
| 12-21-02 | 14 | PFIN-02, PFIN-03 | T-12-21-01/02/03/SC | `cd frontend && npm run test -- --run src/hooks/portfolioStock.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 20 | Not executed |
| 12-22-01 | 14 | PVIEW-03, PCTX-01, PSAFE-02 | T-12-22-01/02/03/SC | `cd frontend && npm run test -- --run src/hooks/portfolioValuation.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 20 | Not executed |
| 12-22-02 | 14 | PVIEW-03, PCTX-01, PSAFE-02 | T-12-22-01/02/03/SC | `cd frontend && npm run test -- --run src/hooks/portfolioHistory.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 20 | Not executed |
| 12-23-01 | 14 | PCTX-01, PSAFE-02 | T-12-23-01/02/03/SC | `cd frontend && npm run test -- --run src/components/PortfolioTargetBoundary.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 19,20 | Not executed |
| 12-23-02 | 14 | PCTX-01, PSAFE-02 | T-12-23-01/02/03/SC | `cd frontend && npm run test -- --run src/App.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 19,20 | Not executed |
| 12-24-01 | 15 | PCTX-01, PFIN-03 | T-12-24-01/02/03/SC | `cd frontend && npm run test -- --run src/pages/TradePage.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 21,23 | Not executed |
| 12-24-02 | 15 | PCTX-01, PFIN-03 | T-12-24-01/02/03/SC | `cd frontend && npm run test -- --run src/pages/StockTradePage.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 21,23 | Not executed |
| 12-25-01 | 15 | PCTX-01, PVIEW-03 | T-12-25-01/02/03/SC | `cd frontend && npm run test -- --run src/pages/PortfolioPage.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 22,23 | Not executed |
| 12-25-02 | 15 | PCTX-01, PVIEW-03 | T-12-25-01/02/03/SC | `cd frontend && npm run test -- --run src/pages/HistoryPage.test.tsx` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 22,23 | Not executed |
| 12-26-01 | 16 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-26-01/02/03/SC | `python3 deploy/tests/test-portfolio-browser-contracts.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 18,24,25 | Not executed |
| 12-26-02 | 16 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-26-01/02/03/SC | `python3 deploy/tests/test-ci-ops.py && python3 deploy/tests/test-image-contracts.py` | First missing proof created by this task before consumer edits; shared fixtures01; prior plans 18,24,25 | Not executed |
| 12-27-01 | 17 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-27-01/02/03/SC | `python3 deploy/tests/run-portfolio-validation.py --suite all-security` | Runner26; actual evidence this task | Not executed |
| 12-27-02 | 17 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-27-01/02/03/SC | `python3 deploy/tests/run-portfolio-validation.py --suite recovery --archive /tmp/birja-phase12-proof/recovery.tar.gz` | Runner26; actual evidence this task | Not executed |
| 12-28-01 | 18 | PCTX-01, PVIEW-03, PSAFE-02 | T-12-28-01/02/03/SC | `python3 deploy/tests/test-portfolio-browser-contracts.py` | Runner26; actual evidence this task | Blocking owner review pending |
| 12-28-02 | 18 | PCTX-01, PVIEW-03, PSAFE-02 | T-12-28-01/02/03/SC | `python3 deploy/tests/test-portfolio-browser-contracts.py` | Runner26; actual evidence this task | Blocking owner review pending |

## Wave0 and Missing Tests

12-01 creates shared financial/economic-byte oracles and migration/ownership/authority test matrix.12-05-01 and06-01 create direct-SQL authority tests before SQL assets;07-02 creates schema-admission tests.08–15 create targeted identity/service/API/history tests before implementation within each task.16-02 creates migration-runner contracts;17-01 creates exact producer/consumer recovery contracts;18-01 creates mixed-root ops fixture before27 actual cold run.19–25 create named browser/client/hook/UI tests first within their task;26 creates browser journeys/runner contracts and full validation runner before27 consumes them. Every exact new test path is listed in its owning plan. Shared test edits depend on first owner. No skipped/always-green stubs; independent expected economics and denied SQL required. Collection-only precursor tasks must record expected feature failures and cannot claim feature completion.

## Requirement Proof Matrix

| Requirement | Focused proof | Independent full proof |
|---|---|---|
| PFUND-03 |01–07 preserved actual economics;08 no regrant;12–14 journal/effects/baseline |17–18 exact inventories;27 one-archive cold recovery |
| PFIN-02 |08 resolver;10–13 active writers/locks;15 refusal |21/24 intent;26 browser;27 real SQL races |
| PFIN-03 |10–11 global key+root+payload and original active replay |21/24 unknown attempts;26–27 |
| PCTX-01 |19/23–25 explicit named financial surfaces |26 synthetic packet;28 owner UI/native zoom |
| PVIEW-03 |14 union/hydration/original/cursor scope |20/22/25 stale pages/details;26–28 |
| PSAFE-02 |08–09 zero/one/many and before-OTP refusal;15 unscoped gate |19/23/26 browser;27 complete regressions |
| PSAFE-03 |03–07 compound lineage/finite closure;05–06 SQL;16 restricted roles |17–18 exact inventory;27 verified TLS/source-bound cold proof |

## Manual Execution Checkpoints

12-28-01 blocks on owner acceptance of changed named tickets/confirmations/receipts/holdings/mixed History/original details/unavailable states after automated evidence.12-28-02 independently blocks on actual desktop browser Zoom menu200%, readable/reachable controls and no obscuring overlap/horizontal page overflow. Emulation and silence cannot satisfy either.

## Sign-Off and Scope

- [x] All56 task IDs mapped to exact plan/wave/requirement/threat/command.
- [x] Missing test creation owners and earlier runner dependencies specified.
- [x] Full strict audits/five images and serial cold-recovery proof scheduled.
- [ ] Independent checker approval.
- [ ] Actual Wave0 execution complete.
- [ ] Focused latency measured; actual automated and owner proofs passed.

Keep both compliance/execution flags false pending corresponding independent review/execution. Phase7 six live IDs remain deferred with stock admissions gated off; no provider,production,publishing or package changes. Phase13 owns create/name/rename/optional empty description/overview;Phase14 public deletion. Terminal root/no-regrant prerequisites are included here.
