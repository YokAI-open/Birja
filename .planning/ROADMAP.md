# Roadmap: Birja

## Overview

Six vertical slices, each ending with a runnable, usable app. Skeleton and CI come first, then auth (which creates the account row that trades lock), then prices, then the trading engine (the highest-risk slice), then the read side (portfolio and history), and finally deployment for friends. Auth and prices are independent and both must precede trading. No Celery, RabbitMQ, nginx, or second price provider until the phase that first needs them (nginx arrives in Phase 6).

## Phases

- [x] **Phase 1: Skeleton and CI** - Full stack runs with one command, frontend talks to backend, CI gates every PR (completed 2026-10-26)
- [x] **Phase 2: Authentication** - Email one-time-code sign-in, persistent session, $10,000 account created once (completed 2026-10-27)
- [x] **Phase 2.1: Deploy to nist.one** (INSERTED) - Production build on https://birja.nist.one with real secrets, nginx, Cloudflare TLS and a renewed certificate (completed 2026-10-27)
- [x] **Phase 3: Prices** - Curated coins with fresh prices refreshed every minute and visible "as of" ages (completed 2026-10-28)
- [x] **Phase 4: Trading** - Market buy/sell with itemized preview, safe execution and actual fill result (completed 2026-10-29)
- [ ] **Phase 5: Portfolio and History** - Cash, holdings, P/L against the $10k start, and paginated trade history
- [ ] **Phase 6: Deploy** - Trading verified on the live site, nightly off-server backups with a tested restore

## Phase Details

### Phase 1: Skeleton and CI

**Goal**: A developer can run the whole stack locally and every PR is checked automatically
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02
**Success Criteria** (what must be TRUE):

  1. `docker compose up --build` starts Postgres, Redis, backend and frontend, and the browser page shows a live backend health result (DB and Redis reachable) fetched through TanStack Query
  2. A PR into `develop`/`main` runs lint, type checks and tests (backend and frontend) in GitHub Actions, and a failing check blocks the merge
  3. The backend image builds from `uv.lock` on Python 3.14 and a smoke test (import app, asyncpg query, Pydantic Decimal round-trip) passes in CI
  4. The test stack (`docker-compose.test.yml`) runs backend tests against an isolated Postgres and Redis

**Plans:** 7/7 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Feature branch + prerequisites gate: create feature/phase-01-skeleton-and-ci, install uv + Node 24, confirm package legitimacy

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Backend health slice: create_app, GET /api/v1/health (DB + Redis), isolated test stack, smoke tests
- [x] 01-04-PLAN.md — Frontend toolchain: Vite/TS 6, ESLint/Prettier/Vitest, Tailwind 4 + MASTER.md tokens, shadcn card/badge/button

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Backend in Compose: Alembic async baseline, Dockerfile (uv.lock, py3.14, non-root), compose + dev override
- [x] 01-05-PLAN.md — Health page: API client, TanStack Query hook, page + provider, tests for ok/degraded/error/loading

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-06-PLAN.md — Full stack in Compose + the single Playwright e2e test (D-03)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-07-PLAN.md — GitHub Actions CI with aggregate ci-pass, docs/commands update, D-01 branch-protection decision + PR into develop

**UI hint**: yes

**Start now, in parallel (wall-clock latency):** buy the domain and begin Resend domain verification (SPF/DKIM, DMARC `p=none`). DNS verification takes time and Phase 2 delivery and Phase 6 both depend on it. This includes the Node 24 upgrade, Tailwind 4, shadcn init and the design system `MASTER.md` in this phase.

### Phase 2: Authentication

**Goal**: Users can sign in with an emailed one-time code, stay signed in, and get their $10,000 account once
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, ACCT-01, ACCT-02
**Success Criteria** (what must be TRUE):

  1. User enters an email and gets the same "code sent" response whether or not an account exists; in local dev the code appears in the console, and with Resend configured it arrives by real email from the verified domain
  2. User enters the correct code and lands signed in; the code cannot be reused, expires after about 10 minutes, and stops working after 5 wrong attempts
  3. Repeated code requests or wrong attempts from one email or IP are refused with a rate-limit message
  4. User stays signed in after a browser refresh and restart (up to about 30 days) and can sign out, after which the session no longer works
  5. A first-time user sees exactly $10,000.00 cash, signing in again never grants more, and there is no way to reset or add cash

**Plans:** 9/9 plans complete

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Branch gate (after PR #2 merges) + package legitimacy gate + Phase 1 review fixes WR-02/WR-04/WR-05

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Request a code: OTP store (HMAC, single-use, 5 attempts), CSRF, POST /auth/request-code, console sender

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — Verify a code: users/accounts (migration 0002), $10,000 exactly once, POST /auth/verify-code

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-04-PLAN.md — Sessions: auth_sessions/refresh_tokens (0003), JWT + cookies on sign-in, GET /me

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02-05-PLAN.md — Sign-in UI (no router, D-03): apiFetch + CSRF, sign-in card, account view, e2e from compose logs
- [x] 02-06-PLAN.md — Rate limits per email, IP and global (429 + Retry-After)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 02-07-PLAN.md — Stay signed in + sign out: refresh rotation with reuse detection, logout, single-flight refresh, e2e
- [x] 02-08-PLAN.md — Resend sender over httpx (D-01), email settings, prod guard, respx tests (D-02)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 02-09-PLAN.md — CI critical-path coverage gate, full suite, real-email checkpoint (D-01/D-02), push gate

**UI hint**: yes

### Phase 02.1: Deploy to nist.one (INSERTED)

**Goal**: Friends can open https://birja.nist.one and sign in with an emailed code, served by a production build
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: DEPL-01 (partial: public HTTPS + sign-up; trading on the live site is verified in Phase 6)
**Success Criteria** (what must be TRUE):

  1. https://birja.nist.one serves the production frontend build through nginx, HTTP redirects to HTTPS, and the TLS chain is valid end to end through Cloudflare (SSL mode Full, strict)
  2. The backend runs with `ENV=prod` and real secrets (startup refuses placeholders), `/docs`/`/redoc`/OpenAPI are off, and only nginx is reachable from the internet (Postgres, Redis and the backend publish no ports)
  3. A visitor requests a code on the public site, receives it by real email from the verified domain and signs in; no codes or keys appear in logs
  4. The expired `*.nist.one` certificate is re-issued (once, via the Cloudflare DNS API) and the manual renewal procedure is documented with the next renewal date
  5. Redeploying from `main` is one documented command
**Plans:** 10/10 plans complete

Plans:
**Wave 1**

- [x] 02.1-01-PLAN.md — Branch feature/deploy-nist-one (D-05), IN-04 (ENV required), IN-03 (redacted CI logs), Playwright browser cache

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02.1-02-PLAN.md — Prod compose (birja-prod, 127.0.0.1:18000, pinned subnet), init-prod-env.sh, deploy.sh (main default, DEPLOY_REF, --rollback; D-02)
- [x] 02.1-03-PLAN.md — nginx site + headers/real-IP/limit_req, install/check scripts, cloudflare-ips.sh (manual, D-06), cloudflare-dns.sh (D-04), renew-cert.sh (D-07)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02.1-04-PLAN.md — smoke-prod.sh (local/--public), CSP Playwright spec, deploy/RUNBOOK.md (renewal, undo), README/CLAUDE.md deploy docs

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02.1-05-PLAN.md — D-08: token-free repo + manual DNS two-step renew-cert.sh, cert renewed via user-added TXT records (SC4), runbook dates, nginx enabled

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 02.1-06-PLAN.md — prod.env + Resend key checkpoint, /srv/birja, loopback-only rehearsal (smoke, client IP, CSP, idempotency, rollback)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 02.1-07-PLAN.md — Full local suite, push gate, PR into develop (user merges)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 02.1-08-PLAN.md — release-0.1 -> PR into main, tag v0.1.0, back-merge into develop (all user-approved)

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 02.1-09-PLAN.md — First deploy from main (twice), user creates the proxied DNS record by hand (D-08), DoH + public smoke + CSP

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 02.1-10-PLAN.md — Real-email sign-in checkpoint, real-IP/log checks, closeout push gate

### Phase 3: Prices

**Goal**: Users can see current prices for a curated coin list, always with how old each price is
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: PRICE-01, PRICE-02, PRICE-03, PRICE-04
**Success Criteria** (what must be TRUE):

  1. User opens a markets page listing about 10-20 coins with current USD prices
  2. Each price shows its "as of" age and a fresh, aging or stale badge
  3. Prices update about every 60 seconds without reloading the page, driven by a single scheduler container (scaling the backend does not duplicate it)
  4. A zero, negative or implausibly spiking price from the provider is rejected, the last good price stays, and its age keeps growing until it shows as stale

**Plans:** 10/10 plans complete

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Branch feature/phase-03-prices, react-router 8.5.1 legitimacy gate + install, RED markets e2e (helpers.ts, markets.spec.ts)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — coins/prices schema (0004, mid only per D-05) + 15-coin seed (0005, D-01), freshness rule (D-03), GET /api/v1/prices behind CurrentUserDep (D-02)
- [x] 03-03-PLAN.md — price_rules.evaluate_price (25% spike + 3-poll confirmation, D-04) at 100% in CI, Kraken Ticker client with bounded retry (respx)
- [x] 03-04-PLAN.md — Markets table (formatUnitPrice per D-06, 30 s refetch) + routes / and /account with nav, e2e moved to /account

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-05-PLAN.md — run_cycle: Redis lock, evaluate, idempotent upsert; scheduler settings; fake source refused in prod; prices.py on the 100% list
- [x] 03-06-PLAN.md — Freshness badges (Live/Delayed/Stale) with ticking ages and oldest-age header

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 03-07-PLAN.md — Scheduler loop + heartbeat + graceful stop; single scheduler service in dev compose; CI e2e PRICE_SOURCE=fake

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 03-08-PLAN.md — Prod scheduler (PRICE_SOURCE kraken, D-07), deploy.sh/rollback support, smoke checks (one scheduler, fresh prices, 401), RUNBOOK; offline verification only

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 03-09-PLAN.md — Full local suite, real Kraken prices on the dev stack (human check), push gate + PR into develop, release decision

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 03-10-PLAN.md — Conditional: release-0.2 via git-flow, tag v0.2.0, deploy + smoke (only if chosen at the push gate)

**UI hint**: yes

### Phase 4: Trading

**Goal**: As a signed-in Birja user, I want to buy and sell coins at real, recent market prices with the full cost shown before I confirm, so that I can practise trading and get a result that is correct to the cent.
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: TRADE-01, TRADE-02, TRADE-03, TRADE-04, TRADE-05, TRADE-06, TRADE-07, TRADE-08
**Success Criteria** (what must be TRUE):

  1. User can place a market buy by dollar amount (cash drops by exactly that amount, fee included) and a market buy or sell by quantity (fractional, up to 8 decimals)
  2. Before confirming, user sees market price, execution price with spread, fee, quantity and total cash change; after confirming, user sees the actual fill and new cash balance
  3. A trade on a price older than the maximum age is refused with a clear message, and if a newer price arrived since the preview, the user sees the new preview instead of a silent fill
  4. Trades are refused for insufficient cash or coins or below the minimum order size (selling a whole position is always allowed), and a double-click or retry executes only once
  5. Many parallel buys against real Postgres never push cash below zero and exactly the affordable number succeed

**Plans:** 10/10 plans complete

Plans:
**Wave 1**

- [x] 04-01-PLAN.md — Branch feature/phase-04-trading (after PR #18 merged), RED trade e2e (buy $100 -> $9,900.00, sell all, price_changed tolerated)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — TDD trade_math.py: D-01 spread/fee settings, D-06 min fee + sell cap, D-02 exact $ buys, D-04 minimum, D-07 cost basis math, 100% coverage
- [x] 04-03-PLAN.md — holdings + trades schema (0006) and guarded accounts cents CHECK (0007), DB backstop tests
- [x] 04-04-PLAN.md — Frontend trade API contract (ApiError.detail, guards, formatQuantity) and TanStack hooks (debounced quote, trade, holding)
- [x] 04-05-PLAN.md — Prod smoke: trade endpoints 401/403 signed out (offline-tested), RUNBOOK "Trading (release 0.3)"

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-06-PLAN.md — trading.py: account FOR UPDATE -> replay -> Live price (D-03) -> holding lock -> plan -> apply; idempotency, price_changed, cost basis; trade_math/trading on the 100% list
- [x] 04-07-PLAN.md — /trade/:symbol page (D-05): live preview, Buy/Sell, confirm with idempotency key, refusals, price changed, fill; Markets Trade links

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04-08-PLAN.md — POST /trades/quote, POST /trades, GET /holdings/{symbol} (CSRF, auth, plain-decimal JSON), API tests, real-Postgres concurrency proof

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 04-09-PLAN.md — Full local suite, live-price dev trades (human check), push gate + PR into develop, release decision

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 04-10-PLAN.md — Conditional: release-0.3 via git-flow, tag v0.3.0, pre-deploy cents check, one deploy + smoke, live trade check
**UI hint**: yes

### Phase 5: Portfolio and History

**Goal**: As a signed-in Birja user, I want to see my current portfolio value and profit or loss alongside every past trade, so that I can understand how my practice investments are performing.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, HIST-01, HIST-02
**Success Criteria** (what must be TRUE):

  1. User sees cash, each holding and total portfolio value at current mid prices, along with the "as of" time of the prices used
  2. User sees total profit/loss against the $10,000 start in dollars and percent
  3. For each holding, user sees quantity, average cost (fees included), current value, unrealized P/L in dollars and percent, and its allocation share
  4. User sees past trades newest first (date/time, coin, side, quantity, execution price, fee, total), and a long history loads page by page

**Plans:** 4/8 plans executed

Plans (eight serial waves; fixed PostgreSQL/Redis fixtures share auth cleanup and destructive migration state):

**Wave 1**

- [x] 05-01-PLAN.md — Wave 1: Real portfolio summary, full Decimal valuation response and RED happy path

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — Wave 2: Complete holding performance and cash-inclusive allocation

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — Wave 3: Used-price freshness/availability and real-PG snapshot proof

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 05-04-PLAN.md — Wave 4: Actual stored trade history with strict user-scoped cursor API

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 05-05-PLAN.md — Wave 5: Load more/retry/end focus and reversible concurrent history index

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 05-06-PLAN.md — Wave 6: Fill/replay invalidation and private-cache identity isolation

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 05-07-PLAN.md — Wave 7: Responsive navigation, CI happy path, coverage and full quality gates

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 05-08-PLAN.md — Wave 8: Fresh dev/browser approval and scoped push/release handoff

**UI hint**: yes

### Phase 6: Deploy

**Goal**: Friends can sign up and trade on the live site, with data safely backed up
**Mode:** mvp
**Depends on**: Phase 5 (public hosting itself is done in Phase 2.1)
**Requirements**: DEPL-01, DEPL-02
**Success Criteria** (what must be TRUE):

  1. A friend opens https://birja.nist.one, requests a code that arrives in a real inbox (Gmail and Outlook), signs up and completes a trade
  2. Production data is backed up nightly off the server, and a restore has been performed once successfully
  3. The Playwright e2e in CI covers the trading happy path
  4. Production Postgres uses a least-privilege app role (not superuser); DB SSL decision recorded

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Skeleton and CI | 7/7 | Complete    | 2026-10-26 |
| 2. Authentication | 9/9 | Complete    | 2026-10-27 |
| 2.1. Deploy to nist.one | 10/10 | Complete   | 2026-10-27 |
| 3. Prices | 10/10 | Complete    | 2026-10-28 |
| 4. Trading | 10/10 | Complete    | 2026-10-29 |
| 5. Portfolio and History | 4/8 | In Progress|  |
| 6. Deploy | 0/TBD | Not started | - |
