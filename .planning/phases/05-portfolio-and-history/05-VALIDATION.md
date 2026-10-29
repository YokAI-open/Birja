---
phase: 5
slug: portfolio-and-history
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-29
---

# Phase 5 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Backend | Existing pytest/pytest-asyncio; real isolated PostgreSQL/Redis from docker-compose.test.yml |
| Frontend | Existing Vitest/Testing Library; Playwright happy paths in fake-price CI only |
| Config | backend/pyproject.toml; frontend/vite.config.ts; frontend/playwright.config.ts |
| Quick backend | `cd backend && uv run pytest -q tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py tests/test_history_service.py tests/test_history_api.py` (use the implemented subset until all exist) |
| Quick frontend | `cd frontend && npm run test -- --run src/pages/PortfolioPage.test.tsx src/pages/HistoryPage.test.tsx` (use the implemented subset until all exist) |
| Full backend | `cd backend && uv run pytest --cov=app --cov-fail-under=80` plus project critical-path coverage command extended to new money/auth services |
| Full frontend | `cd frontend && npm run test -- --coverage` plus lint/typecheck/format/build |
| Execution preflight | Docker daemon reachable; isolated stack healthy; no dev/prod database or real-email e2e target |
| Feedback target | Focused task commands <=120s; full suite at each wave boundary |

## Sampling Rate

- Every implementation task has its own focused automated check before commit.
- RED tests must fail for the intended missing behavior before implementation;
  update route/head assertions only with their corresponding real change.
- At each wave end run the available full backend/frontend suites, lint,
  formatting and types. Before final UAT/PR, run all project CI-equivalent
  gates, dependency audits, migration round trips and deploy offline tests.
- Coverage >=80% overall and 100% on money, auth and execution. Add the new
  pure portfolio math and user-scoped portfolio/history services to the
  identical CI/CLAUDE critical lists; meaningful assertions remain required.

## Requirement and Secure Behavior Map

The planner must replace this capability map with actual task IDs/waves
and commands when writing the plans; no test is claimed to have run.

| Requirement | Threat Ref | Behavior | Automated evidence | Status |
|-------------|------------|----------|--------------------|--------|
| PORT-01 | T-05-01, T-05-02 | Session-scoped, single-snapshot cash/holdings/prices; no mixed concurrent trade state; missing price never zero | portfolio service/API real-PG tests, PortfolioPage component tests | pending |
| PORT-02 | T-05-02 | Decimal total/start P/L including completed round trip, explicit cent/% rounding | portfolio_math examples/invariants; full liquidation API fixture | pending |
| PORT-03 | T-05-02 | Fee-inclusive basis, raw intermediates, 8dp average, zero basis returns N/A percent | math/service/API fixtures, null-aware UI assertions | pending |
| PORT-04 | T-05-02 | Cash-inclusive allocation denominator; zero/incomplete total is unavailable | math edge cases and labelled-bar/UI assertions | pending |
| PORT-05 | T-05-02 | Exact used timestamp, late clock, 119/120/300/301 boundary, last-known warning and retained data | service/API freshness plus ticking/failure component tests | pending |
| HIST-01 | T-05-01, T-05-03 | User-only actual stored fills including signed fee-inclusive total, inactive coin retained | history service/API tests; HistoryPage/CI round trip | pending |
| HIST-02 | T-05-03 | Bounded strict cursor, tied timestamps/id ordering, lookahead, safe retry | cursor matrix, real-PG multi-page tests, migration index checks, infinite-query UI tests | pending |
| Private cache | T-05-01 | No prior-user data after logout/passive expiry and new login; cancel pending private requests | auth/query lifecycle integration tests; trade invalidation/replay tests | pending |

Threat IDs are phase-local placeholders to reconcile with each PLAN threat
model. Models must cover private data/auth, valuation integrity, cursor
validation/resource bounds, migration operational safety and cache identity
isolation, with exact test-linked mitigations. No new service, secret or
package is required by the research.

## Wave 0 Requirements

- [ ] New portfolio math/service/API tests using existing isolated fixtures.
- [ ] New history cursor/service/API tests, including tied timestamps,
  foreign-user boundaries, malformed/oversized cursors and limit bounds.
- [ ] Real-PG concurrent-read fixture proving complete before/after trade states.
- [ ] Existing migration tests extended for the concurrent history index,
  downgrade/upgrade, validity/definition and model parity.
- [ ] Portfolio/History page and API-guard tests; hook/private-cache lifecycle
  tests cover cancellation, identity changes and successful fills/replays.
- [ ] CI Playwright portfolio/history user flow reuses fake-price auth helpers.
- [x] Existing frameworks and dependencies suffice; no installation task.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|----------|-------------|------------|--------------|
| Read portfolio/holding/history after a real-price buy/sell | PORT-01..05, HIST-01 | Human review of actual visible flow and fee/spread explanation | After explicit dev rebuild approval, user signs in, trades, checks values/freshness and matching history; assistant reads no individual balances or secrets |
| Responsive/accessibility feel | PORT-01..05, HIST-01..02 | Visual/keyboard inspection | Check 375/768/1024/1440px, keyboard/focus/200% zoom, safe-area tabs, labelled card/table fields, reduced motion and load-more retry/end focus |

Automated CI e2e does not replace the user's live-data checkpoint. A future
release/deployment requires a fresh phase-specific decision; Phase 4's
release approval is not permission to release Phase 5.

## Validation Sign-Off

- [ ] Every actual task mapped to automated verification or an explicit human checkpoint.
- [ ] No three consecutive implementation tasks without automated feedback.
- [ ] Every new test reference has a producer/dependency; no stale provisional commands.
- [ ] No watch flags, secret/env reads, dev/prod tests or real-email browser automation.
- [ ] Focused checks target <=120s; full suites preserved at wave/final gates.
- [ ] Planner finalized task/wave/threat map and set nyquist_compliant true.

**Approval:** planning in progress; execution results and user checks pending.
