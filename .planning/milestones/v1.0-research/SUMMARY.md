# Project Research Summary

**Project:** Birja
**Domain:** Crypto paper-trading web app (virtual USD, real prices, market orders, small friends audience)
**Researched:** 2026-10-20
**Confidence:** MEDIUM-HIGH

## Executive Summary

Birja is a small, correctness-critical web app. Users get $10,000 of virtual cash once, trade about 10-20 major coins at real prices with a simulated spread and fee, and see portfolio P/L. Experts build this as a modular monolith. Postgres holds the authoritative balances (`accounts.cash`, `holdings`), protected by `CHECK` constraints and row locks. An insert-only `trades` ledger is the audit trail. One pure, 100%-tested `Decimal` pricing module serves both the quote preview and execution. Prices come from one scheduled job, run in exactly one container. The job writes Postgres first and Redis second. Trades read only the Postgres price row and refuse it if it is older than the max age. The SPA and API share one origin (Vite proxy in dev, nginx in prod), so cookie auth and CSRF work without CORS.

The recommended approach is vertical slices, each leaving the app runnable: skeleton + CI, auth, prices, trading, portfolio + history, deploy. Deploy is part of "done" because the definition of v1 is friends using it. Market data should come from the Kraken public Ticker (no key, verified live, true USD pairs). CoinGecko Demo is capped at 10k calls/month and cannot sustain a 60s poll (it would run out in about 7 days), so it is not primary. The OTP email provider is Resend, which needs a verified domain before anyone but the author can receive a code. That makes domain purchase and DNS verification an early external dependency with real wall-clock latency.

The main risks are all in money and trust: double-spend races, rounding and "sell all" dust, wrong average-cost math, trading on stale or garbage prices, OTP and cookie flaws, and a careless first VPS deploy. Each has a concrete prevention in PITFALLS.md: `SELECT ... FOR UPDATE` on the account row first, one defined rounding policy, storing total cost basis rather than average cost, a server-side staleness gate inside the trade transaction, and a parallel-trade test against real Postgres as a phase exit criterion. Scope discipline matters as much as correctness. Fallback providers, Celery/RabbitMQ, charts, watchlists and price-lock quotes should all stay out of v1.

## Open Decisions for the User

These are unresolved disagreements or product choices. They should be settled during requirements or phase discussion, not picked silently.

1. **Mark price for holdings (researchers disagree).** FEATURES recommends **mid**: simple, and a fresh buy then shows an immediate loss of about spread + fee, which teaches the lesson. ARCHITECTURE leans toward the **sell-side price** (mid x (1 - spread)), the true liquidation value. That is more honest to "what is it worth now" but looks harsher, and it is a one-line config. Whichever is chosen must be labeled in the UI and used everywhere (portfolio, per-holding P/L, total P/L). Needed before the portfolio phase.
2. **Background-job mechanism (researchers disagree).** STACK recommends **arq** (one worker container running both the 60s price cron and a queued, retrying OTP-email job). The arq risks are maintenance-mode cadence and a new named dependency. ARCHITECTURE and PITFALLS suggest a **single APScheduler/asyncio loop container** for the price job, with OTP email via **FastAPI `BackgroundTasks`**, which is lost on a crash but the user can re-request. CLAUDE.md allows "Celery + beat, or a single scheduler process". All options need exactly one scheduler container, so the roadmap is the same except for the email path and the dependency list. Celery 5.6.3 has no declared 3.14 support and needs a sync engine plus a beat container, so it is the least attractive for MVP. Decide before the auth phase (email path) and the prices phase (scheduler).
3. **Meaning of the "$ amount" input.** FEATURES recommends total spent including fee. The alternative is notional with the fee on top. Either is fine if the preview shows the total unambiguously. Quantity for $-orders rounds DOWN (Pitfall 4).
4. **Fee in cost basis.** Recommended yes. The fee is charged in USD, not in the coin.
5. **Thresholds (config, tune after real use).** Suggested: refresh 60s, aging badge above 120s, max trade age 180s (ARCHITECTURE and PITFALLS) to about 300s (FEATURES), minimum order about $1 with an exception for selling a full position.
6. **Confirm semantics.** Recommended: the client sends the `as_of` it saw. The server answers 409 `PRICE_CHANGED` with a fresh quote if a newer price has arrived, and 409/422 `PRICE_STALE` if the price is too old. Do not build price-lock quote timers.

## Key Findings

### Recommended Stack

The core stack is fixed by CLAUDE.md, and STACK.md pins current versions verified on PyPI/npm on 2026-10-20. All hot-path Python dependencies ship cp314 wheels, but a Docker build from `uv.lock` with a CI smoke test should confirm this on day one.

**Core technologies:**
- Python 3.14, FastAPI 0.155, SQLAlchemy 2.0.55 (pin `>=2.0.55,<2.1`, with the `[asyncio]` extra), asyncpg 0.32, Alembic 1.20, Pydantic 2.14 (>=2.12 required on 3.14) — fixed backend. Stay on SQLAlchemy 2.0, because 2.1 changes autoflush and drivers for no v1 gain.
- Postgres 18, Redis 8.8 (`noeviction`, `requirepass`, TTL on every key) — source of truth, plus OTP, rate limits and price cache.
- httpx 0.28 + respx 0.23 — provider calls and HTTP-boundary mocks.
- PyJWT, `resend` 2.50 — access tokens and OTP email.
- **Kraken public `Ticker`** — primary price source. No key, one batched call, real bid/ask (mid = (bid+ask)/2). Quirks: response keys differ from request pairs (`XBTUSD` returns `XXBTZUSD`), so keep a static symbol-to-pair-to-key map with a recorded-fixture test. Kraken gives no per-price timestamp, so `as_of` is the fetch time. Parse with `Decimal(str)`, never float.
- Node 24 LTS (upgrade from 18.19.1), React 19, Vite 8, **TypeScript pinned to ~6.0.3** (typescript-eslint does not yet support 7), Tailwind 4 (CSS-first), shadcn CLI, TanStack Query 5, react-router 7, Vitest 5, Playwright, ESLint 10.
- Deploy only: nginx + certbot (webroot challenge, in a container). Caddy is the simpler alternative if certbot gets painful. CLAUDE.md names nginx, so keep it.
- Scheduler: see Open Decision 2.

**Critical version notes:** `orjson` does not serialize Decimal natively, so run `model_dump(mode="json")` first so money goes out as strings. Pin `requires-python = ">=3.14,<3.15"` and use `uv sync --frozen` everywhere.

### Expected Features

**Must have (table stakes):**
- Email OTP login with auto-created account, and $10,000 cash granted exactly once, in the same transaction as user creation.
- Coin list (curated 10-20) with price, relative "as of" time and fresh/aging/stale states.
- Market buy/sell by $ amount or quantity, with a server-computed preview and confirm showing spread and fee in dollars and the total.
- Server-side stale-price refusal, insufficient funds/holdings validation, and "Max"/"Sell all" (sends the exact stored quantity so no dust is left).
- Portfolio: cash, holdings, total value, total P/L vs $10k, per-holding quantity, average cost (weighted average, fee in basis), value and unrealized P/L.
- Trade history, keyset-paginated: date, coin, side, quantity, price, fee, plus realized P/L on sell rows and the price timestamp.
- Mobile-usable layout and clear empty and error states.

**Should have (cheap differentiators, in v1):**
- Itemized cost of trading in the preview (the main learning differentiator).
- Realized P/L stored on each sell row, an allocation % column, the oldest price `as_of` on the portfolio.
- Idempotency key on trades (a unique column, cheap, blocks double-click double-trades).

**Defer (v2+):**
- Portfolio value-over-time chart and snapshot job, per-coin price charts, watchlist, leaderboard, limit/stop orders, trade notes, fees-paid summary, per-coin lot steps, notifications, other asset classes.
- Fallback price provider (CoinGecko). Put the provider behind a small interface now, but build the second integration only if Kraken proves unreliable.
- Push back on: price-lock quotes, per-coin precision rules (use one global 8 dp), a 24h-change column unless free, a price-history table.

### Architecture Approach

A modular monolith with thin routers calling services (auth, prices, trading, portfolio, email) plus one scheduler process. The scheduler shares `services/prices` with the web app, and the web app contains no scheduling code. Data model: `users`, `accounts` (cash, starting_cash, CHECK >= 0), `assets` (seeded by a data migration), `latest_prices` (one row per asset, upserted, guarded against out-of-order writes), `holdings` (quantity and total `cost_basis`, never average cost), `trades` (immutable ledger recording mid, executed price, spread rate, fee rate, fee, `price_as_of` and signed `cash_delta`) and `refresh_tokens` (hashed, with a family id). OTP state lives only in Redis. Balances are authoritative and the ledger is the audit trail, tied together by a reconciliation test: `starting_cash + SUM(cash_delta) == cash`.

**Major components:**
1. `services/trading` + pure `pricing.py` — quote and execute in one transaction: lock account, then holding, read the price from Postgres, check max age, compute, write. The 100%-coverage critical path.
2. `services/prices` + scheduler container — one batched provider call per tick. It validates (> 0, spike guard), upserts Postgres, then sets Redis, and keeps the old price (so it goes stale) on failure.
3. `services/auth` — OTP issue/verify (HMAC in Redis), rotating refresh tokens, CSRF double-submit, get-or-create user + account.
4. `services/portfolio` — valuation on read, in one consistent snapshot, no snapshots in v1.
5. Frontend `api/` wrapper + TanStack Query hooks — one fetch client (credentials, CSRF header, single-flight 401 refresh, money as strings) and pages `/login`, `/markets`, `/trade/:symbol`, `/portfolio`, `/history`.

### Critical Pitfalls

1. **Trading on a stale, missing or garbage price** — Persist `as_of` in Postgres and check age inside the trade transaction, never in the UI or Redis. Validate on ingest (reject <= 0 and big spikes, never overwrite `as_of` on a failed fetch), parse with Decimal.
2. **Double-spend and lost-update races** — Lock the account row `FOR UPDATE` first, then the holding, always in the same order. Add CHECK constraints and an idempotency key. No network I/O inside the transaction. Exit criterion: N parallel buys against real Postgres leave cash >= 0 and exactly the affordable number succeed.
3. **Rounding, fee and "sell all" dust errors** — One pure pricing function. Cash in whole cents, `$`-orders round quantity DOWN (the one documented exception to HALF_EVEN), sell-all reads the exact stored quantity under the lock. Hypothesis property tests and the reconciliation invariant.
4. **Wrong average-cost math** — Store total cost basis. A sell must not change the average. A full sell removes all remaining cost exactly (`quantity = 0 -> cost_basis = 0` CHECK). Store `realized_pnl` per sell and test golden scenarios.
5. **Price quota and scheduler duplication** — One batched call per tick on a source with no monthly cap, and the scheduler in exactly one container. Verify with `docker compose up --scale backend=2`. Expose price age in `/healthz` so a dead poller is visible.
6. **OTP, cookie and deploy flaws** — Identical responses for known and unknown emails, atomic attempt counters, `GETDEL` for single use, email normalized before hashing, trusted-proxy IP handling behind nginx. Single origin everywhere. In prod, publish no DB or Redis ports (Docker bypasses ufw), set up cert renewal, and take off-box `pg_dump` backups with one restore drill.

## Implications for Roadmap

Six phases, each ending runnable, matching ARCHITECTURE's build order with a few adjustments. Scope per phase is deliberately minimal.

### Phase 1: Skeleton, CI and design system
**Rationale:** Everything depends on a working Compose stack and CI. CLAUDE.md requires CI in the first phase that adds tests. The single-origin and Python 3.14 decisions are made here.
**Delivers:** `docker compose up` gives FastAPI `/health` (DB + Redis) and a React page calling it via TanStack Query through the Vite proxy. Also an Alembic baseline, `docker-compose.test.yml`, GitHub Actions (ruff, mypy, pytest cov, eslint, vitest, `pip-audit`/`npm audit`), Node 24, Tailwind 4, shadcn init and the design system `MASTER.md`. A Docker build from `uv.lock` plus a smoke test (import app, asyncpg query, Pydantic Decimal round-trip).
**Uses:** Postgres, Redis, backend and frontend only. No scheduler, nginx or Celery yet.
**Avoids:** Pitfalls 12 (3.14 wheels), 9 (single-origin decision), 13 (session factory, `expire_on_commit=False`), 15 (testing gaps).
**Start now, in parallel (wall-clock latency):** buy the domain, then verify it in Resend (SPF/DKIM, DMARC `p=none`).

### Phase 2: Auth (email OTP + session)
**Rationale:** The account row created at first login is the trade lock target. Auth has the most security surface, so get it right early. It is independent of prices.
**Delivers:** Request code, verify code, land logged in, `/me`, refresh, logout. The account with $10,000 is created once, in the same transaction as the user. Console email backend in dev and a Resend adapter behind an interface. Protected app shell and login page.
**Addresses:** OTP login, $10k seed, session persistence.
**Implements:** `users`, `accounts`, `refresh_tokens`, Redis OTP and rate limits, CSRF, JWT cookies.
**Avoids:** Pitfalls 7 (OTP), 9 (cookies, CSRF, refresh race), 8 (Resend errors handled), 16 (double bootstrap).
**Note:** the email path depends on Open Decision 2.

### Phase 3: Prices (provider, scheduler, markets page)
**Rationale:** A trade needs a price row. Independent of auth and can overlap Phase 2. Run a short spike first, since the symbol map and provider limits determine `as_of` semantics.
**Delivers:** `assets` seeded by a data migration (only coins with a Kraken USD pair). The scheduler container makes one batched Kraken call every 60s, upserts `latest_prices`, then sets Redis. Ingest validation, backoff with jitter and a Redis lock. Markets page with price, relative "as of" and fresh/aging/stale badge. `/healthz` reports price age.
**Uses:** httpx, respx and the chosen scheduler mechanism.
**Avoids:** Pitfalls 1 (quota), 2 (bad ticks), 6 (scheduler duplication), 11 (symbol mapping), 19 (silent poller death).

### Phase 4: Trading engine
**Rationale:** The highest-risk slice, so it gets the most review. Needs an account (Phase 2) and prices (Phase 3).
**Delivers:** Pure `pricing.py` (spread, fee, rounding) and the quote endpoint. `POST /trades` runs in one locked transaction with the staleness gate, minimum order check, idempotency key and `PRICE_CHANGED`/`PRICE_STALE` errors. Trade form with preview and confirm, and a result showing the actual fill and new balance, so the phase is usable before the portfolio exists. `holdings` and `trades` tables with hand-written CHECK constraints.
**Addresses:** Market buy/sell by amount or quantity, itemized preview, Max/Sell all, stale refusal.
**Avoids:** Pitfalls 2 (gate), 3 (races), 4 (rounding), 5 (cost basis), 17 (rates stored per trade), 13 (constraint tests).
**Exit criteria:** Concurrency test passes, 100% coverage on the pricing module and trade service, golden-scenario cost-basis tests.

### Phase 5: Portfolio and history
**Rationale:** A read side on top of the trading tables, so low risk. Needs Open Decision 1 settled.
**Delivers:** `/portfolio` (cash, holdings, average cost, value, unrealized P/L, total P/L vs $10k, allocation %, oldest-price `as_of`) and keyset-paginated `/history` (`useInfiniteQuery`) with realized P/L on sell rows. Money formatted in the UI from server strings only. Includes the reconciliation test and the P/L identity invariant.
**Avoids:** Pitfalls 14 (UI money display), 5 (display side).

### Phase 6: Deploy
**Rationale:** "v1 done = deployed for friends". It is last because it needs everything, but the prod compose split and "no published DB ports" rule apply from Phase 1. Consider a throwaway early smoke deploy to catch Secure-cookie and TLS surprises.
**Delivers:** `docker-compose.prod.yml` (only nginx publishes ports, `edge` and `internal` networks, non-root, pinned images, healthchecks, restart policies, log rotation). nginx with TLS 1.2/1.3, security headers, a short HSTS first, rate limits on `/api/v1/auth/*`, gzip and immutable asset caching. certbot with webroot, a reload hook and a tested `renew --dry-run`. `/docs` and OpenAPI off in prod, Resend live from the verified domain, trusted-proxy IP handling for rate limits, a one-shot migrate step, nightly off-box `pg_dump` with one restore drill, a Playwright happy-path e2e in CI, and friends signing up.
**Avoids:** Pitfalls 10 (VPS), 7 (proxy IP re-check), 8 (real inbox test on Gmail and Outlook).

### Phase Ordering Rationale

- Auth and prices are independent, and both must precede trading. Auth goes first for security surface and the lock-target account row. A prices spike can run first or in parallel if the provider question feels risky.
- Trading is split from portfolio to keep slices small, but the trading phase includes a result screen so it is usable alone.
- Deploy is last, but domain and Resend verification start in Phase 1 because of DNS latency, and same-origin is fixed in Phase 1 so deploy does not break cookies.
- MVP push-back: no Celery/RabbitMQ, no second provider, no price-history table, no charts, no price-lock quotes, no per-coin precision, no PgBouncer or nginx tuning beyond what deploy needs. Nightly backups are required before friends sign up (Phase 6, not v2), because "no reset" makes data loss unrecoverable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Prices):** Verify the Kraken pair and response-key map for the final coin list live, check the public rate limit (not found in docs) and whether `assetVersion=1` works, and decide mid vs last trade. Smoke-test the chosen scheduler library on Python 3.14 early (arq is unproven there in practice).
- **Phase 6 (Deploy):** The certbot bootstrap script, nginx config and Resend DNS record set were not verified against current docs. Use Let's Encrypt `--staging` first.
- **Phase 2 (Auth):** Mostly standard, but check the Resend quota (100/day, 3,000/month) against the rate-limit design, since a brute-force burst can exhaust it.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Standard scaffolding, but the 3.14 smoke test is mandatory.
- **Phase 4:** Well-established patterns, and the design is fully specified in ARCHITECTURE and PITFALLS. Needs careful execution and tests, not more research.
- **Phase 5:** Pure read side with standard conventions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions and peer ranges read from PyPI/npm on 2026-10-20. Kraken verified live. CoinGecko and Resend limits from official pricing pages. Weaker: Kraken rate limit, arq on 3.14 in practice, certbot details (MEDIUM). |
| Features | MEDIUM | Weighted-average cost and P/L conventions are standard (MEDIUM-HIGH). Competitor feature lists come from training data, with no web research (LOW-MEDIUM). |
| Architecture | MEDIUM-HIGH | Follows CLAUDE.md and established brokerage and ledger patterns. Not verified against provider specifics, and two product decisions are open. |
| Pitfalls | MEDIUM | Money, concurrency, OTP, cookie and deploy items are well-established (HIGH). Free-API limits are volatile. The CoinGecko per-minute conflict in PITFALLS is resolved by STACK's read of the official page (100/min, 10k/month). |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Mark price (mid vs sell-side)** and **scheduler/email mechanism (arq vs single loop + BackgroundTasks):** open user decisions. Resolve in requirements.
- **Kraken public rate limit and pair/response-key map:** unknown. Confirm live when freezing the coin list in Phase 3. Exclude ultra-low-price coins that do not fit 8 dp.
- **Kraken has no per-price timestamp:** `as_of` is the fetch time. Acceptable with a max-age gate, and it must be recorded explicitly. This overrides ARCHITECTURE's "provider timestamp if given" wording for the primary source.
- **Disabled-asset policy:** decide whether users can still sell holdings of a later-disabled coin (recommended: allow selling at the last price if not stale, otherwise a clear message).
- **Max trade age:** 180s vs about 300s. It is config, so pick 180s and tune after real use.
- **Refresh-token rotation race (two tabs):** pick a short grace window or a single-flight refresh in the frontend. Single-flight is cheaper.
- **Backups:** STACK called them v1.x, PITFALLS says never skip once friends have accounts. Scheduled in Phase 6.
- **CoinGecko attribution:** relevant only if CoinGecko is ever added as a fallback.
- **If Kraken proves unreliable:** add CoinGecko at a 5-minute cadence with a monthly-call counter. Not in v1.

## Sources

### Primary (HIGH confidence)
- PyPI JSON API and npm registry (queried 2026-10-20) — package versions, cp314 wheel presence, peer ranges
- https://docs.kraken.com/api/docs/rest-api/get-ticker-information plus a live call from this host — Ticker shape and multi-pair batching
- https://www.coingecko.com/en/api/pricing and https://docs.coingecko.com/docs/common-errors-rate-limit — Demo plan 100/min and 10k/month, attribution required
- https://resend.com/pricing and https://resend.com/docs/send-with-python — 100/day, 3,000/month, domain verification, SDK and idempotency
- https://nodejs.org/dist/index.json — Node 24 is LTS
- `CLAUDE.md`, `.planning/PROJECT.md` — fixed rules and scope

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.1 migration notes — reasons to stay on 2.0
- Standard brokerage and accounting practice (weighted-average cost, ledger plus materialized balances, idempotency keys, row-lock serialization) — training knowledge
- Docker/ufw bypass, Let's Encrypt behavior, OWASP session and CSRF guidance — established knowledge, not re-verified

### Tertiary (LOW confidence)
- Investopedia, Binance, eToro and Wall Street Survivor feature lists — training data, not re-verified
- Binance `api.binance.com` US-IP blocking and the region/ToS of `data-api.binance.vision` — third-party reports, validate if ever used
- Caddy vs nginx comparison blogs — directional only

---
*Research completed: 2026-10-20*
*Ready for roadmap: yes*
