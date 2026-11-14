---
phase: 3
slug: prices
status: draft
nyquist_compliant: true
wave_0_complete: false
planned: 2026-10-28
created: 2026-10-28
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + respx (backend, test stack); Vitest + RTL (frontend); Playwright (e2e, `PRICE_SOURCE=fake`) |
| **Config file** | `backend/pyproject.toml`, `frontend/vite.config.ts`, `frontend/playwright.config.ts` (all exist) |
| **Quick run command** | `cd backend && uv run pytest tests/test_price_rules.py tests/test_prices_service.py tests/test_prices_api.py tests/test_kraken.py tests/test_scheduler.py tests/test_scheduler_loop.py -x -q` (test stack up) / `cd frontend && npx vitest run src/lib src/pages src/components` |
| **Full suite command** | `docker compose -f docker-compose.test.yml up -d --wait && cd backend && uv run pytest --cov=app --cov-fail-under=80` + critical-path coverage step; `cd frontend && npm run test -- --coverage`; e2e in CI |
| **Estimated runtime** | ~90 seconds (excluding image builds) |

---

## Sampling Rate

- **After every task commit:** quick command for the area you touched
- **After every plan wave:** full backend + frontend suites
- **Before `/gsd:verify-work`:** full suite, lint/types and e2e green. `evaluate_price` (spike/validity logic) is at 100% coverage and added to the CI critical-path list
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

Per task (filled by the planner, 2026-10-28). File names follow the plans: the rule lives in `services/price_rules.py` (tested in `test_price_rules.py`), freshness and price reads/writes in `services/prices.py`.

| Task | Requirement | Behavior | Test Type | Automated Command | Status |
|------|-------------|----------|-----------|-------------------|--------|
| 03-01 T1 | (git) | branch from develop, planning commit | git check | `test "$(git rev-parse --abbrev-ref HEAD)" = feature/phase-03-prices && git merge-base --is-ancestor origin/develop HEAD` | ⬜ pending |
| 03-01 T2 | (gate) | react-router 8.5.1 approved before install | human gate | n/a (blocking-human checkpoint) | ⬜ pending |
| 03-01 T3 | PRICE-01/02/03 | RED happy-path e2e written, react-router locked | static + list | `cd frontend && npm run typecheck && npx playwright test --list e2e/markets.spec.ts` | ⬜ pending |
| 03-02 T1 | PRICE-01 | 15 seeded coins; CHECK mid > 0; migrations roundtrip at head 0005, no drift | integration | `cd backend && uv run pytest tests/test_migrations.py tests/test_seed_coins.py` | ⬜ pending |
| 03-02 T2 | PRICE-01, PRICE-02 | freshness 119/120/300/301; API shape, ordering, strings, 401 signed out, no-store | unit + API | `cd backend && uv run pytest tests/test_prices_service.py tests/test_prices_api.py tests/test_config_prices.py tests/test_accounts.py` | ⬜ pending |
| 03-03 T1 | PRICE-04 | zero/negative/NaN/crossed rejected; >25% spike rejected; 3-poll confirmation; 100% coverage | unit (100%) | `cd backend && uv run pytest tests/test_price_rules.py --cov=app && uv run coverage report --include=app/services/price_rules.py --fail-under=100` | ⬜ pending |
| 03-03 T2 | PRICE-03 | Kraken 200-with-error, retries/backoff, no retry on unknown pair, fixture = 15 keys | respx | `cd backend && uv run pytest tests/test_kraken.py` | ⬜ pending |
| 03-04 T1 | PRICE-01, PRICE-03 | validator, formatUnitPrice (D-06), table rows, states, 30 s refetch | unit + component | `cd frontend && npx vitest run src/api/prices.test.ts src/lib/money.test.ts src/pages/MarketsPage.test.tsx` | ⬜ pending |
| 03-04 T2 | PRICE-01 | routes / and /account, nav, signed-out sign-in everywhere (D-02) | component | `cd frontend && npx vitest run src/App.test.tsx` | ⬜ pending |
| 03-05 T1 | PRICE-03, PRICE-04 | settings defaults, fake refused in prod, fake source valid | unit | `cd backend && uv run pytest tests/test_config_prices.py tests/test_fake_prices.py` | ⬜ pending |
| 03-05 T2 | PRICE-03, PRICE-04 | cycle upserts 15; spike keeps row and as_of; confirmed on 3rd cycle; lock held -> 0 calls; as_of never backwards | integration (respx + test stack) | `cd backend && uv run pytest tests/test_scheduler.py` + critical-path report incl. prices.py | ⬜ pending |
| 03-06 T1 | PRICE-02 | formatAge, freshnessStatus boundaries, badge labels/variants | unit + component | `cd frontend && npx vitest run src/lib/age.test.ts src/components/FreshnessBadge.test.tsx` | ⬜ pending |
| 03-06 T2 | PRICE-02 | ticking age, local status recompute, oldest-age header, reset on refetch | component | `cd frontend && npx vitest run src/pages/MarketsPage.test.tsx` | ⬜ pending |
| 03-07 T1 | PRICE-03 | loop cadence, first cycle immediate, overrun, heartbeat on failure, clean stop | unit/integration | `cd backend && uv run pytest tests/test_scheduler_loop.py` | ⬜ pending |
| 03-07 T2 | PRICE-03 | dev compose scheduler (no ports, data+app), CI e2e PRICE_SOURCE=fake, throwaway stack 15 fake prices | config + smoke | `docker compose --env-file .env.example config --services \| grep -qx scheduler && grep -q PRICE_SOURCE=fake .github/workflows/ci.yml` | ⬜ pending |
| 03-08 T1 | PRICE-03 | prod scheduler hardened, PRICE_SOURCE kraken; deploy/rollback start or remove it | config + bash | `bash -n deploy/deploy.sh && deploy/tests/test-rollback-target.sh` + prod `config` JSON assertion | ⬜ pending |
| 03-08 T2 | PRICE-02, PRICE-03 | smoke: one healthy scheduler, all coins priced <= 300 s, prices 401 | bash + SQL on test stack | `bash -n deploy/smoke-prod.sh` + PRICES_SQL against test stack (`15 0 -1`) | ⬜ pending |
| 03-09 T1 | all | full CI-equivalent suite (e2e in CI) | suite | see 03-09 Task 1 verify | ⬜ pending |
| 03-09 T2 | all | real Kraken prices on dev stack, ages reset ~60 s | manual + count query | `docker compose ps --status running --services \| grep -cx scheduler` | ⬜ pending |
| 03-09 T3 | all | push gate; CI incl. markets e2e green | CI | `gh pr checks <n>` | ⬜ pending |
| 03-10 T1-3 | all | conditional release + prod smoke | smoke | `/srv/birja/deploy/smoke-prod.sh --public` | ⬜ pending |

Sampling continuity: every auto task has an automated verify. Only the human gates (03-01 T2, the manual part of 03-09 T2, and 03-10) rely on a person, and no three consecutive tasks lack an automated check.

Requirement-level map (from RESEARCH.md):

| Requirement | Behavior | Test Type | Automated Command | Status |
|-------------|----------|-----------|-------------------|--------|
| PRICE-01 | 15 seeded coins; API returns them ordered with Decimal-string prices; signed-out → 401; page shows rows | integration + unit + e2e | `pytest tests/test_prices_api.py tests/test_seed_coins.py`; `vitest MarketsPage`; `playwright markets.spec.ts` (CI) | ⬜ pending |
| PRICE-02 | Age and status boundaries (<120 fresh, 120–300 aging, >300 stale); badge text; age ticks client-side | unit + component | `pytest tests/test_prices_service.py`; `vitest age FreshnessBadge MarketsPage` | ⬜ pending |
| PRICE-03 | One cycle fetches and upserts; Redis lock prevents a concurrent run; cadence; single scheduler; UI refetch | integration (respx) + component + e2e | `pytest tests/test_scheduler.py tests/test_scheduler_loop.py`; `vitest MarketsPage` (30 s refetch); `playwright markets.spec.ts` | ⬜ pending |
| PRICE-04 | Zero, negative, NaN and crossed prices rejected; >25% spike rejected and the last good price kept; as_of unchanged; accepted after 3 consistent polls | unit (100%) + integration | `pytest tests/test_price_rules.py tests/test_scheduler.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Test files are created inside the task that implements the behavior (TDD tasks write tests first), so no separate scaffold wave is needed:

- [ ] e2e target `frontend/e2e/markets.spec.ts` + `e2e/helpers.ts` (03-01, RED until 03-04/06/07); `auth.spec.ts` and `health.spec.ts` moved to `/account` (03-04); CI `.env` gets `PRICE_SOURCE=fake` (03-07)
- [ ] Backend: `test_seed_coins.py`, `test_migrations.py` head 0005 (03-02 T1); `test_prices_service.py`, `test_prices_api.py`, `test_config_prices.py`, allow-list in `test_accounts.py` (03-02 T2); `test_price_rules.py` (03-03 T1); `test_kraken.py` + `fixtures/kraken_ticker_ok.json` (03-03 T2); `test_fake_prices.py` (03-05 T1); `test_scheduler.py` (03-05 T2); `test_scheduler_loop.py` (03-07 T1)
- [ ] conftest: `clean_prices` fixture (03-02), `sim:lock:*` in autouse cleanup (03-05)
- [ ] Frontend: `api/prices.test.ts`, `money.test.ts` additions, `MarketsPage.test.tsx` (03-04); `App.test.tsx` + `test/render.tsx` router option (03-04); `age.test.ts`, `FreshnessBadge.test.tsx` (03-06)
- [ ] Critical-path 100% list: `app/services/price_rules.py` (03-03), `app/services/prices.py` (03-05), in ci.yml and CLAUDE.md
- [ ] Package install behind a legitimacy checkpoint: `react-router` 8.5.1 (03-01 T2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live prices on production move over a few minutes | PRICE-03 | Needs real Kraken data on the live host | After deploy: open https://birja.nist.one signed in, watch ages reset about every 60 s; smoke checks the scheduler and DB freshness |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner sign-off 2026-10-28 (execution status pending)
