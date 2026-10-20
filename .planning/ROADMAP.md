# Roadmap: YokaiExchange

## Overview

Six vertical slices, each ending with a runnable, usable app. Skeleton and CI come first, then auth (which creates the account row that trades lock), then prices, then the trading engine (the highest-risk slice), then the read side (portfolio and history), and finally deployment for friends. Auth and prices are independent and both must precede trading. No Celery, RabbitMQ, nginx, or second price provider until the phase that first needs them (nginx arrives in Phase 6).

## Phases

- [ ] **Phase 1: Skeleton and CI** - Full stack runs with one command, frontend talks to backend, CI gates every PR
- [ ] **Phase 2: Authentication** - Email one-time-code sign-in, persistent session, $10,000 account created once
- [ ] **Phase 3: Prices** - Curated coins with fresh prices refreshed every minute and visible "as of" ages
- [ ] **Phase 4: Trading** - Market buy/sell with itemized preview, safe execution and actual fill result
- [ ] **Phase 5: Portfolio and History** - Cash, holdings, P/L against the $10k start, and paginated trade history
- [ ] **Phase 6: Deploy** - Public domain over HTTPS with backups, so friends can sign up and trade

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
**Plans**: TBD
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
**Plans**: TBD
**UI hint**: yes

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
**Plans**: TBD
**UI hint**: yes

### Phase 4: Trading
**Goal**: Users can buy and sell coins at real recent prices, with cost shown up front and the result correct to the cent
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: TRADE-01, TRADE-02, TRADE-03, TRADE-04, TRADE-05, TRADE-06, TRADE-07, TRADE-08
**Success Criteria** (what must be TRUE):
  1. User can place a market buy by dollar amount (cash drops by exactly that amount, fee included) and a market buy or sell by quantity (fractional, up to 8 decimals)
  2. Before confirming, user sees market price, execution price with spread, fee, quantity and total cash change; after confirming, user sees the actual fill and new cash balance
  3. A trade on a price older than the maximum age is refused with a clear message, and if a newer price arrived since the preview, the user sees the new preview instead of a silent fill
  4. Trades are refused for insufficient cash or coins or below the minimum order size (selling a whole position is always allowed), and a double-click or retry executes only once
  5. Many parallel buys against real Postgres never push cash below zero and exactly the affordable number succeed
**Plans**: TBD
**UI hint**: yes

### Phase 5: Portfolio and History
**Goal**: Users can see what their holdings are worth now, their profit or loss, and every past trade
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, HIST-01, HIST-02
**Success Criteria** (what must be TRUE):
  1. User sees cash, each holding and total portfolio value at current mid prices, along with the "as of" time of the prices used
  2. User sees total profit/loss against the $10,000 start in dollars and percent
  3. For each holding, user sees quantity, average cost (fees included), current value, unrealized P/L in dollars and percent, and its allocation share
  4. User sees past trades newest first (date/time, coin, side, quantity, execution price, fee, total), and a long history loads page by page
**Plans**: TBD
**UI hint**: yes

### Phase 6: Deploy
**Goal**: Friends can open the app on a public domain over HTTPS, sign up and trade, with data safely backed up
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: DEPL-01, DEPL-02
**Success Criteria** (what must be TRUE):
  1. A friend opens the public domain over HTTPS, requests a code that arrives in a real inbox (Gmail and Outlook), signs up and completes a trade
  2. Only nginx is reachable from the internet (no published Postgres or Redis ports), HTTP redirects to HTTPS, and `/docs` is off in production
  3. Production data is backed up nightly off the server, and a restore has been performed once successfully
  4. Certificate renewal works (`renew --dry-run` passes) and a Playwright happy-path e2e runs in CI
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Skeleton and CI | 0/TBD | Not started | - |
| 2. Authentication | 0/TBD | Not started | - |
| 3. Prices | 0/TBD | Not started | - |
| 4. Trading | 0/TBD | Not started | - |
| 5. Portfolio and History | 0/TBD | Not started | - |
| 6. Deploy | 0/TBD | Not started | - |
