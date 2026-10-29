---
phase: 4
slug: trading
status: draft
nyquist_compliant: true
wave_0_complete: false
planned: 2026-10-28
created: 2026-10-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx (backend, test stack, real Postgres for concurrency); Vitest + RTL (frontend); Playwright (e2e, `PRICE_SOURCE=fake`, CI only) |
| **Config file** | existing `backend/pyproject.toml`, `frontend/vite.config.ts`, `frontend/playwright.config.ts` |
| **Quick run command** | `cd backend && uv run pytest tests/test_trade_math.py tests/test_trading_service.py tests/test_trades_api.py -x -q` / `cd frontend && npx vitest run src/pages/TradePage.test.tsx` |
| **Full suite command** | test stack up, then `uv run pytest --cov=app --cov-fail-under=80` plus the critical-path step (including `trade_math.py`, `trading.py`); `npm run test -- --coverage`; e2e in CI |
| **Estimated runtime** | ~120 seconds (excluding image builds) |

---

## Sampling Rate

- **After every task commit:** quick command for the area you touched
- **After every plan wave:** full backend + frontend suites with the critical-path gate
- **Before `/gsd:verify-work`:** full suite, lint/types and e2e green. `trade_math.py` and `trading.py` are at 100%
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

Each task's `<automated>` command is in its plan. RED-first tasks (tdd) create the test files listed under "Wave 0" before the code they cover.

| Task | Plan | Wave | Requirement / Decision | Test Type | Automated Command (summary) | File Exists | Status |
|------|------|------|------------------------|-----------|-----------------------------|-------------|--------|
| 04-01-01 | 01 | 1 | git-flow branch | git | branch is feature/phase-04-trading, based on origin/develop, planning committed | n/a | ✅ green |
| 04-01-02 | 01 | 1 | TRADE-01/02/03/08, D-02, D-05 | e2e (RED) | `npm run typecheck && npx playwright test --list e2e/trade.spec.ts` | created | ✅ green |
| 04-02-01 | 02 | 2 | TRADE-01/02/04/06, D-01, D-04, D-06 | unit (RED) | `pytest tests/test_trade_math.py` fails; config tests | created | ✅ green |
| 04-02-02 | 02 | 2 | same + D-07 cost basis math | unit | `pytest tests/test_trade_math.py tests/test_config_trading.py --cov=app.services.trade_math --cov-branch --cov-fail-under=100` | ✅ | ✅ green |
| 04-03-01 | 03 | 2 | TRADE-06/07 schema, D-07, cents CHECK | migration | `alembic upgrade head && downgrade 0005 && upgrade head` on the test stack | n/a | ✅ green |
| 04-03-02 | 03 | 2 | DB backstops | integration (real PG) | `pytest tests/test_migrations.py tests/test_trading_schema.py` | created | ✅ green |
| 04-04-01 | 04 | 2 | TRADE-03/05/08 client contract | unit | `npx vitest run src/api src/lib` | extended + created | ✅ green |
| 04-04-02 | 04 | 2 | TRADE-03/07 hooks | unit | `npx vitest run src/hooks` | created | ✅ green |
| 04-05-01 | 05 | 2 | prod auth smoke | shell (offline) | `deploy/tests/test-smoke-trading.sh && deploy/tests/test-smoke-ports.sh` | created | ✅ green |
| 04-05-02 | 05 | 2 | RUNBOOK | doc grep | `grep "## Trading (release 0.3)" deploy/RUNBOOK.md` | ✅ | ✅ green |
| 04-06-01 | 06 | 3 | TRADE-01..07, D-03, D-07 | service (RED, real PG) | `pytest tests/test_trading_service.py` fails | created | ✅ green |
| 04-06-02 | 06 | 3 | same | service (real PG) | `pytest tests/test_trading_service.py tests/test_trade_math.py --cov=app.services.trading --cov=app.services.trade_math --cov-branch --cov-fail-under=100` | ✅ | ✅ green |
| 04-06-03 | 06 | 3 | critical-path gate | CI config | include lists identical; full suite >= 80%; critical list 100% | ✅ | ✅ green |
| 04-07-01 | 07 | 3 | D-05 entry + route | Vitest | `npx vitest run src/pages/MarketsPage.test.tsx src/App.test.tsx` | ✅ | ✅ green |
| 04-07-02 | 07 | 3 | TRADE-01/02/03/05/06/07/08 UI (key kept across network-error retry + mid-changing refetch) | Vitest | `npx vitest run src/pages/TradePage.test.tsx && npm run test -- --coverage && npm run build` | created | ✅ green |
| 04-08-01 | 08 | 4 | API contract | static + import | ruff, mypy, routes registered | n/a | ✅ green |
| 04-08-02 | 08 | 4 | TRADE-02/03/05/06/07/08, Auth | API (real PG) | `pytest tests/test_trades_api.py` | created | ✅ green |
| 04-08-03 | 08 | 4 | SC5, TRADE-07 (incl. seeded mixed buys/sells with holding-sum invariant) | concurrency (real PG) | `pytest tests/test_trading_concurrency.py` + full suite + critical 100% | created | ✅ green |
| 04-09-01 | 09 | 5 | all | full suite | CI-equivalent local run (minus e2e) | ✅ | ✅ green |
| 04-09-02 | 09 | 5 | SC1-4 by eye | manual (dev stack) | `alembic current` = 0007 (head) | n/a | ✅ green |
| 04-09-03 | 09 | 5 | push gate, E2E in CI | CI | `gh pr view` / `gh pr checks` (e2e trade.spec.ts) | n/a | ✅ green |
| 04-10-01 | 10 | 6 | release decision | manual | release-now and remaining release actions authorized | n/a | ✅ green |
| 04-10-02 | 10 | 6 | git-flow release | CI + git | PR #20/#21 green and merged; v0.3.0 in main/develop | ✅ | ✅ green |
| 04-10-03 | 10 | 6 | deploy + live trade | prod smoke + manual | origin 38/38, public 9/9; user browser check pending | ✅ | ⬜ pending |

No 3 consecutive tasks lack an automated check (checkpoint tasks 04-09-02/03 and 04-10-* each have a command).

### Requirement-level map

From RESEARCH, with D-06/D-07 applied:

| Req | Behavior | Test Type | Command / File | Status |
|-----|----------|-----------|----------------|--------|
| TRADE-01 | Buy by $: cash change == −A exactly; qty·exec ≤ A − fee; min fee $0.01 (a $1.00 buy pays $0.01 and fills, minimum checked on A per the 04-02 D-04 interpretation); seeded random invariants | unit | `tests/test_trade_math.py` | ✅ green |
| TRADE-02 | Quantity buy/sell; > 8 dp, ≤ 0, NaN, both inputs set, or sell by $ are rejected | unit + API | `test_trade_math.py`, `test_trades_api.py` | ✅ green |
| TRADE-03 | Quote returns every preview field and writes no rows | API | `test_trades_api.py` | ✅ green |
| TRADE-04 | Spread and fee come from settings; execution price, mid and as_of recorded; sell fee capped so proceeds ≥ 0 | unit + service | `test_trade_math.py`, `test_trading_service.py` | ✅ green |
| TRADE-05 | Stale (≥ 120 s) → `stale_price`, no row; mid moved → `price_changed` with a new quote, no row; same mid with newer as_of executes | service + API | `test_trading_service.py` | ✅ green |
| TRADE-06 | Insufficient cash or quantity; below $1.00; whole-position sell below $1.00 allowed, including a sub-cent position | service + API | same | ✅ green |
| TRADE-07 | Replay returns the identical body with one row; same key with a different payload → conflict; replay allowed after the price went stale; concurrent same-key requests | service + concurrency | `test_trading_concurrency.py` | ✅ green |
| TRADE-08 | Fill has qty, price, fee and `cash_after`, which matches `/me` afterwards | API | `test_trades_api.py` | ✅ green |
| SC5 | N parallel buys: exactly floor(cash/cost) succeed, cash never below 0 | concurrency (real PG) | `test_trading_concurrency.py` | ✅ green |
| D-07 | Cost basis: a buy adds the total spent, a sell reduces it proportionally, a full sell sets it to 0 | service | `test_trading_service.py` | ✅ green |
| Auth | 401 signed out, 403 without CSRF on both POSTs | API | `test_trades_api.py` | ✅ green |
| UI | TradePage states; key reused on retry (also after a background refetch changed the mid) and reset only on edit, fill, definitive refusal or price_changed; a double-click sends once; Markets row links to it | Vitest | `TradePage.test.tsx`, `MarketsPage.test.tsx` | ✅ green |
| E2E | Sign in → Markets → Trade BTC → buy $100 → fill, cash $9,900.00 → sell all; tolerate `price_changed` | Playwright (CI) | `frontend/e2e/trade.spec.ts` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

### CI evidence (2026-10-29)

- Run `40841931118` exposed missing accessible region names in the trade
  summary. Regression assertions failed before the fix.
- Commit `f5294a9` names the card from its current visible heading; all 161
  frontend tests passed (98.88% statements), with lint, types, format and build.
- Run `40842519915` passed backend, frontend, image, e2e and ci-pass.
- User chose `push-pr, release-now`; PR #19 was merged into develop as
  `5dc514d` after green CI.

### Release preparation (04-10, 2026-10-29)

- `release-0.3` was cut from updated develop after PR #19 merged.
- Commit `22ff0d5` changes only the four project version files to 0.3.0;
  both lockfiles were checked to contain no dependency changes.
- Backend: 476 tests, 99.89% total coverage, critical-path list 100%;
  ruff, formatting and mypy passed.
- Frontend: 161 tests, 98.88% statements, 99.76% lines; lint, types and build passed.
- The isolated test stack was removed after the tests.
- Release PR #20 and back-merge #21 passed CI and merged; v0.3.0 was published.
- Production cents check 0; one deploy exited 0, migrations 0006/0007 applied;
  origin/public smoke passed 38/38 and 9/9. User browser trade check remains pending.
- Durable evidence: `04-10-RELEASE-CHECKPOINT.md`.

## Wave 0 Requirements

- [ ] `backend/tests/test_trade_math.py`, `test_config_trading.py` (04-02 Task 1, RED first)
- [ ] `backend/tests/test_trading_schema.py` (04-03 Task 2)
- [ ] `backend/tests/test_trading_service.py` + helpers `put_price`, `set_cash`, `put_holding`, `cash_of`, `holding_of`, `trade_count`, `coin_id` and `db`/`new_user` fixtures (04-06 Task 1, RED first; users are unique per test, so no trade/holding wipe is needed; `clean_prices` resets prices)
- [ ] `backend/tests/test_trades_api.py`, `test_trading_concurrency.py` (04-08)
- [ ] `frontend/src/api/trades.test.ts`, `hooks/useDebouncedValue.test.ts` (04-04), `frontend/src/pages/TradePage.test.tsx` (04-07), `frontend/e2e/trade.spec.ts` (04-01, RED first)
- [ ] `deploy/tests/test-smoke-trading.sh` (04-05)
- [ ] No new packages

---

## Manual-Only Verifications

### Dev check evidence (2026-10-29)

- The user authorized the dev rebuild with `go`, then approved the trading check.
- `docker compose up --build -d --wait` exited 0; backend, frontend,
  Postgres, Redis and scheduler were healthy.
- `alembic current`: `0007 (head)`.
- Price aggregate after rebuild: `15 17` (15 prices, oldest 17 seconds old).
- Login delivery initially failed with Resend HTTP 401. The user updated
  the dev API key; the backend was recreated and reported healthy.
- Trade count after the user's approval: `2`.
- The assistant called no auth endpoint and placed no trades. No secrets,
  recipient addresses or account balances were recorded.

| Behavior | Why Manual | Instructions |
|----------|------------|--------------|
| A real buy and sell on the dev stack with live Kraken prices | Needs a human look at the full flow | After "go": open /trade/BTC, buy $100, check the fill and cash, sell all |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags (`vitest run`, `pytest -q`)
- [x] Feedback latency < 120s (per-task commands; full suite at wave end)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planned 2026-10-28 (statuses turn green during execution)
