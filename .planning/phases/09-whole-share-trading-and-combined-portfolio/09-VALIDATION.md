---
phase: 9
slug: whole-share-trading-and-combined-portfolio
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-11
---

# Phase 9 — Validation Strategy

This is a planned execution contract, not proof of implementation or live
activation. The planner must replace the preliminary task map with exact final
plan/task/wave and threat IDs. Existing Phase 7/8 live deferrals stay intact.

## Test Infrastructure

Use the locked pytest/pytest-asyncio/respx and Vitest/RTL/Playwright stack. No new
framework or package installation is required. Backend financial tests use real
guarded isolated PostgreSQL/Redis via docker-compose.test.yml, never dev or
production. External HTTP is mocked only at the transport boundary. Verify test
stack ownership before starting/stopping containers; no provider calls or keys.

| Lane | Command from repository root | Planned feedback budget |
| --- | --- | --- |
| Fast money/rules | `cd backend && uv run pytest tests/test_stock_trade_math.py tests/test_stock_trading_rules.py -q -x` | <30s target, measure actual |
| Execution/retry/concurrency | `cd backend && uv run pytest tests/test_stock_trading_service.py tests/test_stock_trading_concurrency.py -q -x` | Split bounded cases if >30s |
| Portfolio | `cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_snapshot.py tests/test_portfolio_service.py -q -x` | <30s target |
| Client/ticket | `cd frontend && npm run test -- src/api/stockTrades.test.ts src/pages/StockTradePage.test.tsx` | <30s target |
| Backend final | `cd backend && uv run pytest --cov=app --cov-fail-under=80` | Prior Phase8 measured 163.92s; allow measured growth |
| Frontend final | `cd frontend && npm run test -- --coverage` | Prior Phase8 approximately16s; measure |
| Recovery contract | `python3 deploy/tests/test-stock-recovery-contracts.py` | Measure |
| Real roles/TLS/recovery | `bash deploy/tests/test-db-operations.sh --all` | Serial minutes, separate from quick feedback |

New test paths above are targets, not existing passing tests. Final plans must
freeze exact paths and scripts after inspecting their actual entrypoints.

## Sampling Rate

- Every task: meaningful affected automated behavior tests plus scoped static
  checks. New monetary/rule/service features use failing behavioral assertions
  before implementation where practical, not import-failure-only RED.
- Every wave: affected integration/regression suites. No three consecutive
  tasks without automated feedback.
- Full phase gate: backend/frontend coverage, static/build/audits, actual isolated
  browser, hardened runtime/image scans and exact recovery/roles/TLS evidence.
- Keep quick feedback under30s where practical; full suites and real operational
  experiments are explicit longer gates. Do not claim estimates as measurements.
- No watch flags; no broad repeated runs unless source changes/failures justify.

## Preliminary Verification Map

| Capability / future tasks | Requirements | Threat / secure behavior | Meaningful proof |
| --- | --- | --- | --- |
| Pure contracts/math | STKTR-01/02/03 | Exact validated whole-share strings, bid/ask, zero fees | Boundary/overflow/rounding and opposite-side-price tests |
| Successor schema/grants/recovery | STKTR-03/05; compatibility | Immutable fill facts/causal links; no financial authority escalation | Actual migration/42501 denial, retained encrypted restore and restricted verified-TLS consumers |
| Status/eligibility | MKT-02 | Independent evidence, continuity, permission, action/unit authority | Unknown/halted/disconnected/stale refuse; no normal inference from quotes |
| Execution/journal/idempotency | STKTR-03/04/05/06, MKT-02 | Shared cash, original exact replay, post-helper wait guards | Real multi-session races, changed payload/cross-asset conflicts, rollback and after-close replay |
| Mixed portfolio | PORT-06/07 | One coherent financial snapshot; no fabricated marks or denominator | Midpoint/basis/starting cash, closed/halt dates, permission/action expiry, known subtotal/count/null totals |
| Typed client/ticket | STKTR-01/02/03/05, MKT-02 | Frozen uncertain payload/key, stale/auth response suppression | RTL and real browser retry/reprice/close/hold/expiry/account-switch journeys |
| Portfolio presentation | PORT-06/07 | Truthful status, stable rows, unavailable allocation | Desktop/mobile/keyboard/200% reflow and incomplete-value stories |
| Final local gates/checkpoints | All nine | Unchanged crypto and external activation boundaries | Actual automated proof, independent code/security/UI/goal review; actual owner new-UI answer |

## Wave 0 Requirements

Existing test infrastructure covers the phase. New test files/fixtures belong
to their owning feature tasks before implementation; final plan map must name
their creation dependencies. Do not create a speculative standalone test suite
or run networked tests as a substitute for fixture preparation.

## Mandatory PostgreSQL Experiments

Use independent real sessions, observable barriers and bounded lock waits.
Cover mixed stock/crypto and different-stock shared-cash spends; concurrent
sells; same-key retry/payload conflict across both assets; absent-holding race;
split/first-fill/cutoff and quote/unit races; permission/status/action/age changes
across instrument/account/holding and append_stock_movement awaits. A failure
after tentative writes must roll back cash, holding, trade, receipt and journal.
Restored replay must preserve once-only effects and next identity values.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
| --- | --- | --- | --- |
| New stock ticket/combined portfolio acceptance | UI decisions supporting all nine | Owner product acceptance | Review actual isolated screenshots/journeys after automated proof; record explicit answer |
| Live quote/status/action suitability | DATA-01 boundary, MKT-02 | Provider rights/access/continuity not established locally | Preserve owner deferral; no new calls or activation. Future explicit scope/evidence required |

Documentation whitespace checks never prove human acceptance, rights, account
entitlements or live freshness. Owner may defer external activation while local
execution completes, with live readiness explicitly pending.

## Validation Sign-Off

- [ ] Final task/wave/threat map matches PLAN files.
- [ ] Every task has automated verification or a genuine human checkpoint.
- [ ] Missing test targets have explicit creation dependencies.
- [ ] Actual critical coverage remains100% statements/branches and overall≥80%.
- [ ] Exact schema/grants/recovery and both verified-TLS lanes pass.
- [ ] Isolated browser and independent reviews pass.
- [ ] Actual owner UI decision and external disposition recorded.
- [ ] Set nyquist_compliant/wave_0_complete only on actual evidence.

**Approval:** Pending execution evidence; planning review is separate.
