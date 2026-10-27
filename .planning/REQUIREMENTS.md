# Requirements: YokaiExchange

**Defined:** 2026-10-20
**Core Value:** Making a trade at a real, recent market price and then seeing what it's worth now. "Buy at today's price, check back later, see real P/L" must work and must be correct to the cent.

## v1 Requirements

Requirements for the initial release. Each maps to a roadmap phase.

### Foundation

- [x] **FOUND-01**: Developer can start the full stack locally with one `docker compose up` and see the frontend talk to the backend
- [x] **FOUND-02**: Every PR into `develop`/`main` runs lint, type checks and tests in GitHub Actions, and a failure blocks the merge

### Authentication

- [ ] **AUTH-01**: User can request a 6-digit sign-in code by entering their email. The response is identical whether or not the email has an account.
- [ ] **AUTH-02**: User can sign in by entering the emailed code. The code is single-use, expires after about 10 minutes, and dies after 5 wrong attempts.
- [ ] **AUTH-03**: Code requests and verification attempts are rate-limited per email and per IP
- [ ] **AUTH-04**: User stays signed in across browser refreshes and restarts, up to about 30 days, without re-entering a code
- [ ] **AUTH-05**: User can sign out, which ends the session server-side
- [x] **AUTH-06**: Sign-in codes arrive by real email (Resend, from a verified domain). In local dev they are logged to the console instead.

### Account

- [ ] **ACCT-01**: A new user starts with $10,000.00 of virtual cash, granted exactly once when their account is created
- [ ] **ACCT-02**: User cannot reset their account or add cash

### Prices

- [ ] **PRICE-01**: User can see a list of about 10–20 curated cryptocurrencies with their current USD price
- [ ] **PRICE-02**: Every price shows how old it is ("as of" time) and whether it is fresh, aging or stale
- [ ] **PRICE-03**: Prices refresh automatically about every 60 seconds from a free public market-data source, without the user reloading the page
- [ ] **PRICE-04**: Invalid prices (zero, negative or implausible spikes) are rejected and the last good price is kept

### Trading

- [ ] **TRADE-01**: User can place a market buy by dollar amount. The amount is the total cash spent, fee included.
- [ ] **TRADE-02**: User can place a market buy or sell by coin quantity (fractional, up to 8 decimals)
- [ ] **TRADE-03**: Before confirming, user sees a preview with market price, execution price (including spread), fee, quantity and total cash change
- [ ] **TRADE-04**: Trades execute at mid price ± a fixed simulated spread, plus a fixed percentage fee charged in USD
- [ ] **TRADE-05**: A trade is refused with a clear message if the price is older than the maximum allowed age. If the price changed since the preview, the user sees the new preview instead.
- [ ] **TRADE-06**: A trade is refused if the user lacks the cash or coins for it, or if it is below the minimum order size (selling a whole position is always allowed)
- [ ] **TRADE-07**: Submitting the same trade twice (double-click, retry) executes it only once
- [ ] **TRADE-08**: After a trade, user sees the actual fill: quantity, price, fee and new cash balance

### Portfolio

- [ ] **PORT-01**: User can see cash, each holding and total portfolio value at current mid prices
- [ ] **PORT-02**: User can see total profit/loss against the $10,000 start, in $ and %
- [ ] **PORT-03**: User can see, per holding: quantity, average cost (fees included), current value and unrealized P/L in $ and %
- [ ] **PORT-04**: User can see each holding's share of the portfolio (allocation %)
- [ ] **PORT-05**: The portfolio shows the "as of" time of the prices used

### History

- [ ] **HIST-01**: User can see their past trades, newest first: date/time, coin, side, quantity, execution price, fee and total
- [ ] **HIST-02**: Long trade histories load page by page

### Deployment

- [ ] **DEPL-01**: Friends can open the app at a public domain over HTTPS, sign up and trade
- [ ] **DEPL-02**: Production data is backed up nightly off the server, and a restore has been tested once

## v2 Requirements

Deferred to a future release. Tracked but not in the current roadmap.

### Portfolio & insight

- **PORT-V2-01**: Portfolio value-over-time chart (needs a snapshot job)
- **PORT-V2-02**: Realized P/L shown on each sell in history
- **PORT-V2-03**: Per-coin price charts

### Trading

- **TRADE-V2-01**: "Max" and "Sell all" buttons
- **TRADE-V2-02**: Limit and stop orders

### Assets

- **ASSET-V2-01**: Stocks
- **ASSET-V2-02**: Gold and other metals
- **ASSET-V2-03**: Currencies (FX)
- **ASSET-V2-04**: Bonds

### Social

- **SOCL-V2-01**: Leaderboard of friends by total return

### Reliability

- **PRICE-V2-01**: Fallback price provider if the primary source proves unreliable

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Account reset / adding cash | Deliberate: mistakes stay, like real investing |
| Short selling, leverage, margin | Too complex and risky to model for a beginner learning tool |
| Streaming tick-by-tick prices (websockets) | Prices about 1 minute old are enough; streaming needs more infra and paid data |
| Price-lock quotes with countdown timers | Re-pricing at confirm plus a stale-price check covers the same need |
| Real bid/ask order books | Spread is simulated as a fixed %, the same for every coin |
| Per-coin precision or lot-size rules | One global 8-decimal precision keeps the math simple |
| FIFO/LIFO tax lots | Weighted average cost is enough for learning |
| Real money, deposits, brokerage integration | This is a simulator |
| Passwords | Login is email + one-time code only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Complete |
| FOUND-02 | Phase 1 | Complete |
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 2 | Pending |
| AUTH-04 | Phase 2 | Pending |
| AUTH-05 | Phase 2 | Pending |
| AUTH-06 | Phase 2 | Complete |
| ACCT-01 | Phase 2 | Pending |
| ACCT-02 | Phase 2 | Pending |
| PRICE-01 | Phase 3 | Pending |
| PRICE-02 | Phase 3 | Pending |
| PRICE-03 | Phase 3 | Pending |
| PRICE-04 | Phase 3 | Pending |
| TRADE-01 | Phase 4 | Pending |
| TRADE-02 | Phase 4 | Pending |
| TRADE-03 | Phase 4 | Pending |
| TRADE-04 | Phase 4 | Pending |
| TRADE-05 | Phase 4 | Pending |
| TRADE-06 | Phase 4 | Pending |
| TRADE-07 | Phase 4 | Pending |
| TRADE-08 | Phase 4 | Pending |
| PORT-01 | Phase 5 | Pending |
| PORT-02 | Phase 5 | Pending |
| PORT-03 | Phase 5 | Pending |
| PORT-04 | Phase 5 | Pending |
| PORT-05 | Phase 5 | Pending |
| HIST-01 | Phase 5 | Pending |
| HIST-02 | Phase 5 | Pending |
| DEPL-01 | Phase 6 | Pending |
| DEPL-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 31
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-20*
*Last updated: 2026-10-20 after initial definition*
