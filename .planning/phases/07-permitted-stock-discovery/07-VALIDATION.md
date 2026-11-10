---
phase: 7
slug: permitted-stock-discovery
status: planned
nyquist_compliant: false
nyquist_planning_contract: true
wave_0_complete: false
created: 2026-11-10
---

# Phase 7 — Validation Strategy

Planning contract, not execution evidence. No new test/source exists merely because named below. Independent plan checker approved the contract after revision2 on2026-11-10; execution evidence remains pending. New tasks create their behavior tests first; missing import/file failure alone is not meaningful RED.

## Infrastructure and sampling

Reuse pytest/respx against real isolated PostgreSQL/Redis; Vitest/RTL and Playwright. Backend uses docker-compose.test.yml/conftest guards only. Ops use fixed birja-ops-test fixtures with finally cleanup, never production/dev URLs or original volumes. All destructive fixtures are serial. Every task has automated feedback or a documented legitimate external/human gate. Per wave run affected tests/lint/types; expand only for changed scope or failures. Full final tests follow once settled.

## Exact per-task map

Durations are estimates to measure. Q=pure/HTTP/component target<30s; D=DB/API/migration30–120s; O=ops1–10min; B=browser1–5min; G=fullbuild/scans/suites minutes; H=human wait unbounded. No claimed result.

| Task | Requirements | Automated command | Class | Human gate |
|---|---|---|---|---|
| 07-01-01 | STOCK-01,SAFE-01 | `cd backend && uv run pytest tests/test_stock_migrations.py -q` | D | None |
| 07-01-02 | STOCK-01,SAFE-01 | `cd backend && uv run pytest tests/test_stock_catalog.py tests/test_stock_migrations.py -q` | D | None |
| 07-02-01 | SAFE-01,STOCK-01 | `cd backend && uv run pytest tests/test_prices_service.py tests/test_stock_isolation.py -q` | D | None |
| 07-02-02 | SAFE-01,STOCK-01 | `cd backend && uv run pytest tests/test_stock_isolation.py tests/test_trading_service.py tests/test_trades_api.py -q` | D | None |
| 07-03-01 | SAFE-01 | `python3 deploy/tests/test-stock-recovery-contracts.py` | Q | None |
| 07-03-02 | SAFE-01 | `bash deploy/tests/test-backup.sh && bash deploy/tests/test-restore-safety.sh` | O | None |
| 07-04-01 | SAFE-01 | `bash deploy/tests/test-db-operations.sh --roles && bash deploy/tests/test-db-operations.sh --tls` | O | None |
| 07-04-02 | SAFE-01 | `bash deploy/tests/test-db-operations.sh --all` | O | None |
| 07-05-01 | DATA-01 | `cd backend && uv run pytest tests/test_stock_admission.py -q` | Q | None |
| 07-05-02 | DATA-01 | `cd backend && uv run pytest tests/test_stock_admission.py tests/test_config_scheduler.py tests/test_config_prices.py -q` | Q | None |
| 07-06-01 | STOCK-03,DATA-01 | `cd backend && uv run pytest tests/test_alpaca.py tests/test_stock_quote_rules.py -q` | Q | None |
| 07-06-02 | STOCK-03,DATA-01 | `cd backend && uv run pytest tests/test_stock_quotes.py -q` | D | None |
| 07-07-01 | MKT-01 | `git diff --check` | H | None |
| 07-07-02 | MKT-01 | `git diff --check` | H | Explicit approval; tests are no substitute |
| 07-08-01 | MKT-01,STOCK-03 | `cd backend && uv run pytest tests/test_stock_calendar_runtime.py -q` | Q | None |
| 07-08-02 | MKT-01,STOCK-03 | `cd backend && uv run pytest tests/test_stock_sessions.py tests/test_stock_quote_rules.py -q` | Q | None |
| 07-09-01 | DATA-01,STOCK-03,MKT-01,SAFE-01 | `cd backend && uv run pytest tests/test_stock_scheduler.py -q` | Q | None |
| 07-09-02 | DATA-01,STOCK-03,MKT-01,SAFE-01 | `cd backend && uv run pytest tests/test_scheduler_loop.py tests/test_scheduler.py tests/test_config_scheduler.py -q` | Q | None |
| 07-10-01 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01 | `cd backend && uv run pytest tests/test_stocks_api.py -q` | D | None |
| 07-10-02 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01 | `cd backend && uv run pytest tests/test_stocks_api.py tests/test_prices_api.py tests/test_stock_isolation.py -q` | D | None |
| 07-11-01 | STOCK-01,STOCK-02,STOCK-03,DATA-01 | `cd frontend && npm run test -- src/api/stocks.test.ts src/hooks/useStocks.test.tsx` | Q | None |
| 07-11-02 | STOCK-01,STOCK-02,STOCK-03,DATA-01 | `cd frontend && npm run test -- src/components/StockAttribution.test.tsx` | Q | None |
| 07-12-01 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01 | `cd frontend && npm run test -- src/components/StockSection.test.tsx src/pages/MarketsPage.test.tsx` | Q | None |
| 07-12-02 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01 | `cd frontend && npx playwright test e2e/markets.spec.ts e2e/stocks.spec.ts` | B | None |
| 07-13-01 | SAFE-01,STOCK-03,DATA-01,MKT-01 | `python3 deploy/tests/test-ci-ops.py && cd backend && uv run pytest tests/test_critical_coverage_config.py -q` | G | None |
| 07-13-02 | SAFE-01,STOCK-03,DATA-01,MKT-01 | `cd backend && uv run pytest --cov=app --cov-fail-under=80` | G | None |
| 07-14-01 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01,SAFE-01 | `git diff --check` | H | Explicit approval; tests are no substitute |
| 07-14-02 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01,SAFE-01 | `cd backend && uv run pytest tests/test_stock_admission.py tests/test_stocks_api.py -q` | H | None |
| 07-14-03 | STOCK-01,STOCK-02,STOCK-03,DATA-01,MKT-01,SAFE-01 | `git diff --check` | H | Explicit approval; tests are no substitute |

08-01 also requires actual locked3.14amd64 hardened-image import/build/strict scan.13-02's backend command is one sampling slice; every final gate below is mandatory.14-02 additionally performs only the bounded private measurement authorized by14-01; pytest cannot satisfy positive live evidence.

## Wave0 task ownership

| Infrastructure gap | Creating tasks | Status |
|---|---|---|
| Stock-aware reset/seed and populated0008 exact-preservation fixture | 07-01-01/02 | Not executed |
| Symbol/ID/collision legacy refusal | 07-02-01/02 | Not executed |
| Revisioned exact manifest/producer/consumer/payload | 07-03-01/02 | Not executed |
| Revision0009-owned conditional grants and session identity USAGE; actual upgrade without grant repair plus fresh-bootstrap parity; scheduler cannot create/renew calendar review/overrides in admissions or inject session authority, but can refresh derived generation-bound sessions; TLS allow/deny and exact restore of authoritative calendar fields | 07-01-01,07-04-01/02 | Not executed |
| Admission scope/generation/expiry races | 07-05-01 | Not executed |
| Raw exact number/event/condition HTTP fixtures and realPG monotonic races | 07-06-01/02 | Not executed |
| Official dated DST/holiday/earlyclose/exception fixtures and actualruntime; current authoritative calendar evidence/overrides versus derived session generation, expired-review fresh-row and forged-generation refusal | 07-08-01/02 | Not executed |
| Actual restricted-TLS persisted-state generation/expiry evaluation using genuine session_at in both upgrade-without-grant-repair and fresh-bootstrap lanes | 07-13-01/02 | Not executed |
| Hanging/revoked stock collection with independent crypto/cancellation | 07-09-01/02 | Not executed |
| Authenticated no-store leftjoin/API redaction; final committed evidence/clock after awaits and same-request blocked-DB revoke/expiry/age120/close/review-expiry tests | 07-10-01/02 | Not executed |
| Client validator/late-response/auth purge; full request RTT and conservative server-time boundary intervals at first render; shared attribution | 07-11-01/02 | Not executed |
| UI state matrix, responsive realbrowser coexistence | 07-12-01/02 | Not executed |

## Execution ordering correction — 2026-11-10

07-04 executes actual SQL ACL/sequence/authority-write denials, verified TLS and independent exact restore before any calendar runtime exists. Its former genuine session predicate assertion depended on07-08, which transitively depends on07-04. Required evaluator generation/expiry cases remain in07-08-02; actual persisted cross-role integration belongs to07-13-01 (ops-fixtures.py/test-db-operations.sh) after the genuine evaluator exists. Both --roles and --all then execute it without a fixture-only substitute or silent skip, and07-13-02 must record passing evidence before activation/completion. No security/coverage gate or architecture changes.

## Complete final gate (07-13-02)

### Required regression semantics from checker revision 1

07-01-01 creates the migration grant implementation, not merely a bootstrap expectation.07-04-01 must bootstrap actual0008 once before the migrator upgrade and perform no post-upgrade bootstrap or grant-repair SQL. Actual app reads and scheduler quote/session writes, generated session identity insertion/USAGE, forbidden admission-sequence use and table/financial/DDL denials prove the upgrade's privileges. A separate new-schema bootstrap lane must agree. Role-absent isolated migration remains supported.

07-10-01/02 must pause a current admitted request in actual awaited DB work, commit a restrictive generation change from another connection, and assert that same response's final projection is redacted. Additional injected-clock transitions cover permission expiry, quote119.999→120, regular close and calendar-review expiry. Final evidence is read from current committed state, followed by fresh UTC and synchronous projection without another application await. Earlier-request revocation tests alone do not satisfy this proof; changes after the final evidence snapshot/network delivery are not promised to be predicted.

07-11-01 measures monotonic start-to-receipt RTT across retries/server waits and spends it conservatively before first render: subtract it from admission/review/close lifetimes and add it to quote age. Use a conservative server-time interval for opening boundaries; browser wall-clock skew cannot establish permission/session truth. Delay transport across expiry/age120/close and assert immediate redaction/reclassification, not a fresh lifetime starting at receipt. All these are planned tests, with no executed result claimed.

Use test-only configuration and existing CI isolation; do not rerun unchanged expensive proofs gratuitously, but all actual changed-source gates must have final evidence.

- Backend lint/types: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app`.
- Backend full: `cd backend && uv run pytest --cov=app --cov-fail-under=80`; audit: `cd backend && uv run pip-audit`.
- Critical100%: `cd backend && uv run coverage report --include=app/services/otp.py,app/services/auth.py,app/services/accounts.py,app/services/ratelimit.py,app/services/email.py,app/core/security.py,app/core/deps.py,app/services/price_rules.py,app/services/prices.py,app/services/trade_math.py,app/services/trading.py,app/services/portfolio_math.py,app/services/portfolio.py,app/services/history.py,app/api/v1/history.py,app/services/stock_admission.py,app/services/stock_quote_rules.py,app/services/stock_quotes.py,app/services/stock_sessions.py,app/services/stocks.py,app/api/v1/stocks.py --fail-under=100`.
- Frontend lint/types/format: `cd frontend && npm run lint && npm run typecheck && npx prettier --check .`; coverage: `cd frontend && npm run test -- --coverage`; audit: `cd frontend && npm audit --audit-level=high`.
- Browser: existing dedicated CI fake-provider/console-email stack; `cd frontend && npx playwright test`.
- Serial ops: `bash deploy/tests/test-backup.sh`; `bash deploy/tests/test-db-config.sh`; `bash deploy/tests/test-restore-safety.sh`; `bash deploy/tests/test-db-operations.sh --all`; `python3 deploy/tests/test-image-contracts.py`; `python3 deploy/tests/test-ci-ops.py`.
- Actual five-image builds/runtime/nonroot and strict HIGH/CRITICAL including unfixed scans: run existing exact `.github/workflows/ci.yml` image-security commands, record source/lock/image digests and actualscanner results. Static contract tests are not actual scans. Calendar import must run in that actualPython3.14image. Preserve all existing gates and originalcritical paths.
- Independent skill-required code/security/UI review, affected corrections and focused reruns; no source waiver or hidden pending critical findings.

## Manual/external and completion honesty

07-07-02 approves package legitimacy before installation.07-14-01 separately approves actual product evidence and bounded private calls after concrete reviewed local proof.07-14-03 accepts the finished UI after automation. Formatting/regression commands never grant rights, package approval or visual acceptance. No automatic/yolo checkpoint approval. Verify reference/quotes/actions/status products and access/display/derived/retention/scope/attribution/quota separately. Actual20symbol identity/freshness evidence needs explicit authorization. Missing rights/access/coverage leaves stocks disabled and liveSC pending; no completion SUMMARY/phase-complete claim. Owner UI acceptance cannot waive external criteria.

## Sign-off

- [x] All29tasks mapped; no three implementation tasks lack automated feedback.
- [x] Wave0 has numbered owners and no claimed executed tests.
- [x] No watch commands; slow gates distinguished from quick slices.
- [x] Current-schema exact recovery/TLS comes early; oldlanes supported.
- [x] Original+new critical100%paths retained.
- [ ] Independent plan checker approval.
- [ ] Wave0 implemented; actual full local proofs.
- [ ] Actual permitted-data and owner UI acceptance.


Final planning approval: independent checker passed after revision2,0blockers/0active warnings. Planning sampling/ownership is verified; nyquist_compliant and wave_0_complete remain false until actual execution evidence supports them. Backup/restore suites are classified O, not quick checks.
