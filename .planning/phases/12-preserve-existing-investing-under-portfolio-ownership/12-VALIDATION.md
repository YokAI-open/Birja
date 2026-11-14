---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-11-14
---

# Phase12 Validation Strategy

28 plans,56 tasks,18 waves. Final independent planning verification passed with zero blockers/warnings; see12-PLAN-CHECK-03.md. All commands below are planned execution, not passed evidence. No runtime/provider/production/install work occurred in planning. ASVS level1, high block; preserve80% overall and100% critical branch coverage, strict dependency audits and all five actual image scans.

## Sampling and Infrastructure

Existing locked pytest with real isolated PostgreSQL roles/TLS, Vitest, Playwright and retained ops runners. Run focused task command after each implementation, then family regression before plan close. Focused target120s is unmeasured. Full coverage, builds/scans and serial real cold recovery may exceed target and are explicit exceptions.12-27 performs full source-bound qualification; drift invalidates it.

## Exact Per-Task Verification Map

T-12-NN-01 and02 map the actual control/negative proof to task01 and02 respectively; the plan threat register names each boundary and exact command.03 explicitly accepts categories without a new mechanism; SC is accepted where no package boundary exists and concretely mitigated in26/27. Collection/static/metadata precursor commands establish only their stated contract; actual SQL assertions become green in07 after Alembic0017.

| Task | Wave | Requirements | Threats | Automated command | Proof creation/dependency owner | Status |
|---|---:|---|---|---|---|---|
| 12-01-01 | 1 | PFUND-03, PFIN-03, PSAFE-03 | T-12-01-01; T-12-01-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'migrator_connection' && uv run pytest tests/test_portfolio_migrations.py --collect-only -q` | This task creates independent proof fixtures; prior none | Not executed |
| 12-01-02 | 1 | PFUND-03, PFIN-03, PSAFE-03 | T-12-01-02; T-12-01-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_ownership.py tests/test_portfolio_authority.py --collect-only -q` | This task creates independent proof fixtures; prior none | Not executed |
| 12-02-01 | 2 | PFUND-03, PSAFE-03 | T-12-02-01; T-12-02-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'model_metadata'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01 | Not executed |
| 12-02-02 | 2 | PFUND-03, PSAFE-03 | T-12-02-02; T-12-02-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'model_metadata'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01 | Not executed |
| 12-03-01 | 3 | PFUND-03, PSAFE-03 | T-12-03-01; T-12-03-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'model_metadata'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-02 | Not executed |
| 12-03-02 | 3 | PFUND-03, PSAFE-03 | T-12-03-02; T-12-03-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_authority.py -q -k 'model_metadata'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-02 | Not executed |
| 12-04-01 | 4 | PFUND-03, PSAFE-03 | T-12-04-01; T-12-04-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'expansion or association_guard'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-03 | Not executed |
| 12-04-02 | 4 | PFUND-03, PSAFE-03 | T-12-04-02; T-12-04-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'backfill or preserved or resume or downgrade'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-03 | Not executed |
| 12-05-01 | 5 | PFIN-02, PFIN-03, PSAFE-03 | T-12-05-01; T-12-05-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_stock_authority.py --collect-only -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-04 | Not executed |
| 12-05-02 | 5 | PFIN-02, PFIN-03, PSAFE-03 | T-12-05-02; T-12-05-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_stock_authority.py -q -k 'asset_contract'` | Task creates named missing tests before consumer; shared fixture01; prior 12-04 | Not executed |
| 12-06-01 | 5 | PFUND-03, PSAFE-03 | T-12-06-01; T-12-06-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_dividend_authority.py --collect-only -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-04 | Not executed |
| 12-06-02 | 5 | PFUND-03, PSAFE-03 | T-12-06-02; T-12-06-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_dividend_authority.py -q -k 'asset_contract'` | Task creates named missing tests before consumer; shared fixture01; prior 12-04 | Not executed |
| 12-07-01 | 6 | PFUND-03, PSAFE-02, PSAFE-03 | T-12-07-01; T-12-07-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_migrations.py -q -k 'final or inventory or immutability' && uv run pytest tests/test_portfolio_ownership.py tests/test_portfolio_authority.py tests/test_portfolio_stock_authority.py tests/test_portfolio_dividend_authority.py -q -k 'final_sql'` | Actual Alembic0017; first green final SQL from02/03/05/06; prior 12-01, 12-04, 12-05, 12-06 | Not executed |
| 12-07-02 | 6 | PFUND-03, PSAFE-02, PSAFE-03 | T-12-07-02; T-12-07-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_schema_admission.py -q` | Actual Alembic0017; first green final SQL from02/03/05/06; prior 12-01, 12-04, 12-05, 12-06 | Not executed |
| 12-08-01 | 7 | PSAFE-02, PFIN-02, PFUND-03 | T-12-08-01; T-12-08-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_ownership.py -q -k 'resolver or identity_contract or malformed'` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-02, 12-03, 12-07 | Not executed |
| 12-08-02 | 7 | PSAFE-02, PFIN-02, PFUND-03 | T-12-08-02; T-12-08-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_identity.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-01, 12-02, 12-03, 12-07 | Not executed |
| 12-09-01 | 8 | PSAFE-02, PCTX-01 | T-12-09-01; T-12-09-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_identity_api.py -q -k 'versioned or cookie or refresh'` | Task creates named missing tests before consumer; shared fixture01; prior 12-08 | Not executed |
| 12-09-02 | 8 | PSAFE-02, PCTX-01 | T-12-09-02; T-12-09-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_identity_api.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-08 | Not executed |
| 12-10-01 | 8 | PFIN-02, PFIN-03 | T-12-10-01; T-12-10-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_crypto.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-08 | Not executed |
| 12-10-02 | 8 | PFIN-02, PFIN-03 | T-12-10-02; T-12-10-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_crypto_api.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-08 | Not executed |
| 12-11-01 | 9 | PFIN-02, PFIN-03, PSAFE-03 | T-12-11-01; T-12-11-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_stock_trading.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-08, 12-10, 12-12 | Not executed |
| 12-11-02 | 9 | PFIN-02, PFIN-03, PSAFE-03 | T-12-11-02; T-12-11-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_stock_api.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-08, 12-10, 12-12 | Not executed |
| 12-12-01 | 8 | PFUND-03, PFIN-02, PSAFE-03 | T-12-12-01; T-12-12-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_stock_ownership.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-08 | Not executed |
| 12-12-02 | 8 | PFUND-03, PFIN-02, PSAFE-03 | T-12-12-02; T-12-12-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_splits.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-08 | Not executed |
| 12-13-01 | 9 | PFUND-03, PSAFE-03 | T-12-13-01; T-12-13-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_entitlements.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-06, 12-12 | Not executed |
| 12-13-02 | 9 | PFUND-03, PSAFE-03 | T-12-13-02; T-12-13-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_dividends.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-06, 12-12 | Not executed |
| 12-14-01 | 10 | PVIEW-03, PCTX-01, PFUND-03 | T-12-14-01; T-12-14-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_valuation.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-10, 12-11, 12-13 | Not executed |
| 12-14-02 | 10 | PVIEW-03, PCTX-01, PFUND-03 | T-12-14-02; T-12-14-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_scoped_history.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-10, 12-11, 12-13 | Not executed |
| 12-15-01 | 11 | PSAFE-02, PVIEW-03, PFIN-02, PCTX-01 | T-12-15-01; T-12-15-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_routes.py -q -k 'metadata or history or valuation'` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-09, 12-10, 12-11, 12-14 | Not executed |
| 12-15-02 | 11 | PSAFE-02, PVIEW-03, PFIN-02, PCTX-01 | T-12-15-02; T-12-15-SC (accept) | `cd backend && uv run pytest tests/test_portfolio_routes.py tests/test_portfolio_identity_api.py tests/test_portfolio_crypto_api.py tests/test_portfolio_stock_api.py -q` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-09, 12-10, 12-11, 12-14 | Not executed |
| 12-16-01 | 10 | PSAFE-03, PFUND-03 | T-12-16-01; T-12-16-SC (accept) | `python3 deploy/tests/test-dev-bootstrap.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-13 | Not executed |
| 12-16-02 | 10 | PSAFE-03, PFUND-03 | T-12-16-02; T-12-16-SC (accept) | `python3 deploy/tests/test-portfolio-migration-runner.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-07, 12-13 | Not executed |
| 12-17-01 | 12 | PFUND-03, PSAFE-03 | T-12-17-01; T-12-17-SC (accept) | `python3 deploy/tests/test-portfolio-recovery-contracts.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-15, 12-16 | Not executed |
| 12-17-02 | 12 | PFUND-03, PSAFE-03 | T-12-17-02; T-12-17-SC (accept) | `python3 deploy/tests/test-portfolio-recovery-contracts.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-15, 12-16 | Not executed |
| 12-18-01 | 13 | PFUND-03, PSAFE-03 | T-12-18-01; T-12-18-SC (accept) | `python3 deploy/tests/test-portfolio-fixture-contracts.py` | 18-01 fixture/behavioral tests;18-02 source lock and real smoke; prior 12-17 | Not executed |
| 12-18-02 | 13 | PFUND-03, PSAFE-03 | T-12-18-02; T-12-18-SC (accept) | `python3 deploy/tests/test-ci-ops.py && python3 deploy/tests/test-portfolio-fixture-contracts.py && python3 deploy/tests/ops-fixtures.py --portfolio-fixture-smoke` | 18-01 fixture/behavioral tests;18-02 source lock and real smoke; prior 12-17 | Not executed |
| 12-19-01 | 12 | PSAFE-02, PCTX-01 | T-12-19-01; T-12-19-SC (accept) | `cd frontend && npm run test -- --run src/api/auth.test.ts` | Task creates named missing tests before consumer; shared fixture01; prior 12-15 | Not executed |
| 12-19-02 | 12 | PSAFE-02, PCTX-01 | T-12-19-02; T-12-19-SC (accept) | `cd frontend && npm run test -- --run src/hooks/usePortfolioTarget.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-15 | Not executed |
| 12-20-01 | 13 | PFIN-02, PFIN-03, PVIEW-03 | T-12-20-01; T-12-20-SC (accept) | `cd frontend && npm run test -- --run src/api/portfolioTrades.test.ts` | Task creates named missing tests before consumer; shared fixture01; prior 12-15, 12-19 | Not executed |
| 12-20-02 | 13 | PFIN-02, PFIN-03, PVIEW-03 | T-12-20-02; T-12-20-SC (accept) | `cd frontend && npm run test -- --run src/api/portfolioReads.test.ts` | Task creates named missing tests before consumer; shared fixture01; prior 12-15, 12-19 | Not executed |
| 12-21-01 | 14 | PFIN-02, PFIN-03 | T-12-21-01; T-12-21-SC (accept) | `cd frontend && npm run test -- --run src/hooks/portfolioCrypto.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-20 | Not executed |
| 12-21-02 | 14 | PFIN-02, PFIN-03 | T-12-21-02; T-12-21-SC (accept) | `cd frontend && npm run test -- --run src/hooks/portfolioStock.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-20 | Not executed |
| 12-22-01 | 14 | PVIEW-03, PCTX-01, PSAFE-02 | T-12-22-01; T-12-22-SC (accept) | `cd frontend && npm run test -- --run src/hooks/portfolioValuation.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-20 | Not executed |
| 12-22-02 | 14 | PVIEW-03, PCTX-01, PSAFE-02 | T-12-22-02; T-12-22-SC (accept) | `cd frontend && npm run test -- --run src/hooks/portfolioHistory.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-20 | Not executed |
| 12-23-01 | 14 | PCTX-01, PSAFE-02 | T-12-23-01; T-12-23-SC (accept) | `cd frontend && npm run test -- --run src/components/PortfolioTargetBoundary.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-19, 12-20 | Not executed |
| 12-23-02 | 14 | PCTX-01, PSAFE-02 | T-12-23-02; T-12-23-SC (accept) | `cd frontend && npm run test -- --run src/App.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-19, 12-20 | Not executed |
| 12-24-01 | 15 | PCTX-01, PFIN-03 | T-12-24-01; T-12-24-SC (accept) | `cd frontend && npm run test -- --run src/pages/TradePage.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-21, 12-23 | Not executed |
| 12-24-02 | 15 | PCTX-01, PFIN-03 | T-12-24-02; T-12-24-SC (accept) | `cd frontend && npm run test -- --run src/pages/StockTradePage.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-21, 12-23 | Not executed |
| 12-25-01 | 15 | PCTX-01, PVIEW-03 | T-12-25-01; T-12-25-SC (accept) | `cd frontend && npm run test -- --run src/pages/PortfolioPage.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-22, 12-23 | Not executed |
| 12-25-02 | 15 | PCTX-01, PVIEW-03 | T-12-25-02; T-12-25-SC (accept) | `cd frontend && npm run test -- --run src/pages/HistoryPage.test.tsx` | Task creates named missing tests before consumer; shared fixture01; prior 12-22, 12-23 | Not executed |
| 12-26-01 | 16 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-26-01; T-12-26-SC (mitigate) | `python3 deploy/tests/test-portfolio-browser-contracts.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-18, 12-24, 12-25 | Not executed |
| 12-26-02 | 16 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-26-02; T-12-26-SC (mitigate) | `python3 deploy/tests/test-ci-ops.py && python3 deploy/tests/test-image-contracts.py` | Task creates named missing tests before consumer; shared fixture01; prior 12-18, 12-24, 12-25 | Not executed |
| 12-27-01 | 17 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-27-01; T-12-27-SC (mitigate) | `python3 deploy/tests/run-portfolio-validation.py --suite all-security` | 26 runner; actual evidence/owner response required; prior 12-26 | Not executed |
| 12-27-02 | 17 | PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03 | T-12-27-02; T-12-27-SC (mitigate) | `python3 deploy/tests/run-portfolio-validation.py --suite recovery --archive /tmp/birja-phase12-proof/recovery.tar.gz` | 26 runner; actual evidence/owner response required; prior 12-26 | Not executed |
| 12-28-01 | 18 | PCTX-01, PVIEW-03, PSAFE-02 | T-12-28-01; T-12-28-SC (accept) | `python3 deploy/tests/test-portfolio-browser-contracts.py` | 26 runner; actual evidence/owner response required; prior 12-27 | Blocking owner review pending |
| 12-28-02 | 18 | PCTX-01, PVIEW-03, PSAFE-02 | T-12-28-02; T-12-28-SC (accept) | `python3 deploy/tests/test-portfolio-browser-contracts.py` | 26 runner; actual evidence/owner response required; prior 12-27 | Blocking owner review pending |

## Wave0 and Missing Tests

12-01 creates shared financial/economic-byte oracles and genuine two-user legacy global split, and reconciles conftest/test_migrations/test_stock_migrations to guarded restricted LOGIN migrator with child-only authenticated Alembic helper. Actual session_user/role/guard/unchanged parent tests pass there on existing0014;04 proves association/refusal/resume;07 proves fresh/populated0017 startup.12-05-01 and06-01 create direct-SQL authority tests before SQL assets;07-02 creates schema-admission tests.08–15 create targeted identity/service/API/history tests before implementation within each task.16-02 creates migration-runner contracts;17-01 creates exact producer/consumer recovery contracts;18-01 creates current0017 mixed-root fixture plus behavioral command/oracle contract tests;18-02 creates authenticated retained-source lock/dispatcher and runs actual isolated0017 smoke.27 owns the full encrypted same-archive cold restore.02/03 metadata cases and05/06 static SQL cases do not require final database constraints;07-01 is their concrete first SQL-green owner after actual Alembic0017.19–25 create named browser/client/hook/UI tests first within their task;26 creates browser journeys/runner contracts and full validation runner before27 consumes them. Every exact new test path is listed in its owning plan. Shared test edits depend on first owner. No skipped/always-green stubs; independent expected economics and denied SQL required. Collection-only precursor tasks must record expected feature failures and cannot claim feature completion.

## Requirement Proof Matrix

| Requirement | Focused proof | Independent full proof |
|---|---|---|
| PFUND-03 |01–07 preserved actual economics;08 no regrant;12–14 journal/effects/baseline |17–18 exact inventories;27 one-archive cold recovery |
| PFIN-02 |08 resolver;10–13 active writers/locks;15 refusal |21/24 intent;26 browser;27 real SQL races |
| PFIN-03 |10–11 global key+root+payload and original active replay |21/24 unknown attempts;26–27 |
| PCTX-01 |19/23–25 explicit named financial surfaces |26 synthetic packet;28 owner UI/native zoom |
| PVIEW-03 |14 union/hydration/original/cursor scope |20/22/25 stale pages/details;26–28 |
| PSAFE-02 |08–09 zero/one/many and before-OTP refusal;15 unscoped gate |19/23/26 browser;27 complete regressions |
| PSAFE-03 |01 authenticated prerequisite;03–07 owned lineage/global split immutable marker;05–06 static assets/SQL collection,07 actual authority/freeze;16 restricted roles |17–18 exact inventory;27 verified TLS/source-bound cold proof |

## Manual Execution Checkpoints

12-28-01 blocks on owner acceptance of changed named tickets/confirmations/receipts/holdings/mixed History/original details/unavailable states after automated evidence.12-28-02 independently blocks on actual desktop browser Zoom menu200%, readable/reachable controls and no obscuring overlap/horizontal page overflow. Emulation and silence cannot satisfy either.

## Sign-Off and Scope

- [x] All56 task IDs mapped to exact plan/wave/requirement/threat/command.
- [x] Missing test creation owners and earlier runner dependencies specified.
- [x] Full strict audits/five images and serial cold-recovery proof scheduled.
- [x] Independent checker approval (12-PLAN-CHECK-03.md at ce1c75b).
- [ ] Actual Wave0 execution complete.
- [ ] Focused latency measured; actual automated and owner proofs passed.

Planning compliance is approved; wave_0_complete remains false until actual execution. Phase7 six live IDs remain deferred with stock admissions gated off; no provider,production,publishing or package changes. Phase13 owns create/name/rename/optional empty description/overview;Phase14 public deletion. Terminal root/no-regrant prerequisites are included here.

## Revision2 Contract Proof Owners

05/06 completion means static asset-contract PASS plus final_sql collection only. Actual restricted-role economic/forgery/freeze success belongs07-01 after real0017; no duplicate DDL/create_all/skipped proof.01-01 owns guarded authenticated pytest prerequisite and positive session_user before04, whose SQL proves actual association/ordinary and SET ROLE refusal/resume;07 owns fresh/populated final startup.

Global applications never gain root/user columns or association updates.01/04 preserve real two-user legacy split;03 declares nullable SMALLINT marker and owned movement keys;05 defines final insertion guard;07 qualifies shape/ACL/SQL negatives.12 reads persisted NULL-v1/explicit2, writes one global application for same-user siblings and proves mixed reload/freeze.16 inventories authority;17 hashes/projects/restores exact shape/default/check/trigger/ACL/NULL-or2;18 runs oracle mutations and isolated smoke;27 proves cold-restored interpretation on the same archive. All runtime obligations remain unexecuted.
