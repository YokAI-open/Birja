# YokaiExchange

## What This Is

A website where you practice investing with virtual money at real market prices. You start with $10,000 of virtual cash, buy and sell assets at live prices, and watch your portfolio's value and profit/loss move with the real market. The first audience is the author and a handful of friends. v1 covers crypto only. Stocks, gold, bonds and currencies come later.

## Core Value

Making a trade at a real, recent market price and then seeing what it's worth now. If everything else fails, "buy at today's price, check back later, see real P/L" must work and must be correct to the cent.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Sign in with email + one-time code (no passwords); codes emailed via Resend
- [ ] New account starts with $10,000 virtual cash, once, with no reset
- [ ] Curated list of ~10–20 major cryptocurrencies with prices refreshed about every minute, each shown with its "as of" time
- [ ] Market buy/sell orders, by dollar amount or by quantity (fractional quantities allowed)
- [ ] Trades execute at market price ± a fixed simulated spread, plus a fixed % fee. Both are shown before the user confirms.
- [ ] Trades are refused if the price is older than a maximum allowed age
- [ ] Portfolio view: cash, holdings, total value now, total P/L vs the $10k start
- [ ] Per-holding P/L against average cost
- [ ] Trade history: date, coin, side, quantity, price, fee
- [ ] Deployed on a server with a domain and TLS, so friends can sign up and use it

### Out of Scope

- Stocks, gold/metals, FX, bonds: v2+. Each needs its own data source and market-hours handling. Crypto first proves the core loop.
- Portfolio value-over-time chart: v2. It needs a snapshot job and stored history.
- Limit/stop orders: v2+. They need a background matcher. Market orders cover the core loop.
- Short selling, leverage, margin: not planned. Too complex for a learning tool aimed at beginners.
- Leaderboard and social features: v2+. v1 is solo; each user sees only their own portfolio.
- Portfolio reset: deliberately excluded. Mistakes stay, like real investing.
- Streaming tick-by-tick prices (websockets): not planned for v1. Prices about 1 minute old are enough and work on free data tiers.
- Real money, deposits, brokerage integration: never. This is a simulator.
- Real bid/ask order books: not available on free tiers, so the spread is simulated.

## Context

- Motivation: most people learn investing by losing real money. This removes that risk. No hindsight or time travel: you decide today and find out over weeks and months.
- Users: the author plus friends. Small scale (tens of users), but it is public on the internet, so security still matters (see CLAUDE.md Security).
- Market data: free tiers only. The curated coin list keeps API calls within free rate limits. Prices are fetched by a single scheduled job and cached in Redis, with the latest price also persisted in Postgres, which is the source of truth.
- Simulated pricing: buy price = mid × (1 + spread), sell price = mid × (1 − spread), plus fee = % of notional. The exact values are config. The executed price, fee and price timestamp are recorded on every trade.
- The repo started with only `main`. Git-flow is mapped as `main` = production (the "master" role in CLAUDE.md) and `develop` = integration.
- `.claude/skills/ui-ux-pro-max` is available for the design system (`design-system/<project>/MASTER.md`). shadcn setup needs a Node upgrade (Node 18 is too old). Do this in the first frontend phase.

## Constraints

- **Tech stack**: FastAPI/Python 3.14, async SQLAlchemy 2.0 + asyncpg, Alembic, Postgres, Redis, React + Vite + TS, Tailwind + shadcn/ui, TanStack Query, Docker Compose. Defined in CLAUDE.md. Components are added when a step first needs them.
- **Budget**: free market-data tiers only. Resend free tier for email. A small VPS for hosting.
- **Money correctness**: `Decimal` / `NUMERIC(20,8)`, explicit `ROUND_HALF_EVEN` at trade execution, money sent as JSON strings, trades in one DB transaction with row locks.
- **Security**: email OTP stored as an HMAC in Redis, JWT access + rotating refresh token in HttpOnly cookies, CSRF double-submit, rate limits. Per CLAUDE.md.
- **Process**: MVP-first. Each phase leaves the app runnable. Tests ship with features; 80% coverage, and 100% on money, trade execution, login and authorization.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Crypto only in v1 | 24/7 market, free near-real-time APIs, fractional quantities; proves the core loop with one data source | — Pending |
| Prices refreshed about every 1 min by one scheduled job, not streamed | Fits free tiers; much less infra; "as of" time shown | — Pending |
| Market orders only | Delivers the core value without a background order matcher | — Pending |
| Fixed % simulated spread + fixed % fee | Free APIs give no bid/ask; still teaches that trading costs money | — Pending |
| $10k start, no reset | Mistakes stay, like real investing | — Pending |
| Curated ~10–20 coins | Keeps API calls within free rate limits | — Pending |
| Resend for one-time-code email | Free tier, simple API | — Pending |
| v1 done = deployed for friends | Real use by real people is the validation | — Pending |
| `main` acts as master; `develop` created from it | Repo started with `main`; avoids renaming the default branch | — Pending |
| Kraken public Ticker as the price source | No key, one batched call, real bid/ask; CoinGecko's free 10k calls/month can't sustain a 60s poll | — Pending |
| Holdings valued at mid price | Simple; a fresh buy shows the cost of spread + fee, which teaches that trading costs money | — Pending |
| One simple scheduler-loop container for prices; OTP email via FastAPI BackgroundTasks | Fewest dependencies; Celery has no declared Python 3.14 support; a lost email just means re-requesting | — Pending |
| "$ amount" on buys = total cash spent including fee | Cash drops by exactly what the user typed | — Pending |
| Repo made public so branch protection can require `ci-pass` on `develop` and `main` (D-01) | Free real merge blocking. The private plan returned 403 for protection. A git-history secret scan came back clean before the switch | ✓ Good (2026-10-26: protection verified, strict, enforce_admins off) |
| No `ORJSONResponse`/`orjson` (D-02) | Deprecated in FastAPI. Pydantic already serializes `response_model` output | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-20 after initialization*
