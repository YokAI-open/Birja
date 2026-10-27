# Feature Landscape

**Domain:** Crypto paper-trading web app (virtual USD, real prices), small friends audience, learning focus
**Researched:** 2026-10-20
**Overall confidence:** MEDIUM. Based on well-known behavior of Investopedia Simulator, Binance/Bybit demo trading, eToro virtual portfolio, Wall Street Survivor, and standard brokerage cost-basis conventions. Web research was not run this session. The P/L conventions are standard accounting, so they carry more confidence than the competitor feature lists, which come from training data and should be treated as LOW-MEDIUM.

## Table Stakes

Missing any of these makes a simulator feel broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Email OTP login, account auto-created on first verify | Zero-friction signup for friends | Med | Security-heavy (HMAC code, rate limits, refresh rotation). Per CLAUDE.md. |
| $10,000 starting cash, granted exactly once | Every simulator has a starting balance | Low | Seed in the same transaction as user creation. Record as a ledger or "initial deposit" row so P/L baseline is 10000 by definition. |
| Coin list with price, "as of" time, 24h change | Users must see what they can buy | Low-Med | 24h change needs the provider to return it; otherwise omit. It is a nice-to-have, not core. |
| Buy and sell market orders, by $ amount or by quantity | Core loop | Med | Single DB transaction with `FOR UPDATE` on cash and holding rows. |
| Trade preview with confirm step | Shows spread and fee and prevents fat-finger trades. Binance, eToro and Investopedia all have a preview or confirm step. | Med | See "Trade UX". |
| Insufficient funds / insufficient holdings validation | Basic correctness | Low | Server-side. Client-side hints only. |
| "Max" / "Sell all" shortcut | Selling an exact fractional balance by typing is error-prone. Every exchange has a 25/50/75/100% or Max control. | Low | "Sell all" must send the exact stored quantity so no dust is left behind. |
| Portfolio screen: cash, holdings, total value, total P/L ($ and %) | Core value | Med | See "Portfolio screen". |
| Per-holding quantity, avg cost, current value, unrealized P/L ($ and %) | Learning loop: "what is it worth now" | Med | Average-cost method. |
| Trade history (date, coin, side, qty, price, fee) | Audit trail; needed for trust | Low-Med | Keyset pagination, newest first (`created_at, id`). Also show total $ and realized P/L on sells. |
| Stale-price protection | Project core value: "correct to the cent" | Med | Max age check at execution, plus visible as-of times. |
| Logout and session persistence | Expected | Low | Part of auth. |
| Mobile-usable layout | Friends will open it on phones | Low-Med | Responsive tables or cards. No native app. |
| Clear empty states and errors | First login has no holdings. A refused trade needs a human message. | Low | "Price is 6 min old, trading paused until next refresh." |

## Differentiators

Not expected in an MVP, but valuable. Only the first group is cheap enough for v1.

| Feature | Value Proposition | Complexity | v1? |
|---------|-------------------|------------|-----|
| Spread and fee itemized in the preview, in dollars ("Total cost of this trade: $X") | Teaches that trading costs money, a lesson most simulators hide by using zero-fee fills at mid. This is already in scope and is the main learning differentiator. | Low | YES |
| Realized vs unrealized P/L split on the portfolio | Most simple simulators show only a total. Learners benefit from seeing banked vs paper gains. | Low-Med | YES, if cheap (see P/L model). Otherwise show realized on sell rows in history only. |
| "Fees paid to date" total | Shows the drag of costs | Low | Optional. One SUM query. |
| Portfolio allocation (% by holding) | Teaches diversification. Can be a column, not a chart. | Low | Column yes, pie chart no. |
| Quote staleness shown inline, relative ("2 min ago") with color states | Builds trust and also teaches that prices move | Low | YES |
| Portfolio value-over-time chart | Strongest engagement feature in this category | High (snapshot job + storage) | v2 (already out of scope) |
| Per-coin price chart | Standard in Binance/eToro | High | v2 |
| Leaderboard, sharing | Competitive hook for friends | Med-High | v2 |
| Limit/stop orders | Real-trading learning | High (matcher) | v2 |
| Watchlist | Convenience | Low-Med | v2 (needs a table) |
| Trade notes or journaling ("why did I buy?") | Strong learning value, unusual in simulators | Low-Med | v2 candidate. Single nullable text column on a trade, but still a v1 scope creep. |
| Reset portfolio | Common in competitors | Low | Deliberately excluded by user. Keep excluded. |
| Education content, contests, achievements | Wall Street Survivor's angle | High | Never for this project. |

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Price lock / quote hold timers ("price valid for 15s") | Needs quote storage, expiry and race handling. Overkill for tens of users on 1-min prices. | Preview shows the price and its as-of time. Confirm is rejected with 409 if a newer price has arrived since. User re-previews. |
| Instant fills at exact mid, zero fees | Teaches the wrong lesson and breaks the learning goal | Fixed spread and fee, already decided |
| Silent execution on stale prices | Breaks the core promise | Refuse with a clear message |
| Streaming/websocket prices, ticking P/L | Complexity and free-tier limits for no learning value | Poll with TanStack Query `refetchInterval` about 30-60s and show the as-of time |
| FIFO/LIFO lot tracking and tax lots | Large complexity, irrelevant to a learning tool without taxes | Weighted-average cost |
| Short, margin, leverage, futures | Complex and dangerous for beginners (already out of scope) | None |
| Portfolio reset / "start over" button | Contradicts the no-hindsight philosophy | None |
| Editing or deleting trades | Breaks the audit trail | Trades are immutable. Corrections would be new rows, and are not needed in v1. |
| Deposits/withdrawals, "add funds" | It is a simulator, and it would invalidate the $10k baseline | None |
| Per-coin custom spread based on volume or volatility | Speculative realism | One global config value, maybe per-coin override later |
| Email notifications, price alerts | Extra background work and email cost | v2+ |
| Public profiles, other users' portfolios | Privacy and scope | v1 is solo |
| Hard-coded unlimited coin catalog or search over thousands of coins | Exceeds free-tier limits | Curated 10-20 coins in a config or DB table |

## Detailed Expected Behavior (v1)

### Trade UX (preview and confirmation)

Common pattern (Binance convert and market order, eToro open-trade dialog, Investopedia trade page): select coin, choose Buy or Sell, enter an amount, see an estimate, click Preview or Review, then Confirm, then see a result.

Recommended flow:

1. Trade form per coin: Buy/Sell toggle, an input with a toggle between "$ amount" and "Quantity", and available balance shown beside it (cash for buy, coin quantity for sell). Include a Max button.
2. Live client-side estimate as the user types. This is a computed hint only, never authoritative.
3. Preview step. The best approach is a server-computed quote endpoint (`POST /trades/preview`, no side effects) that uses the exact same pricing function as execution, so preview and fill can't drift. It returns:
   - market (mid) price and its as-of timestamp
   - executed price (mid ± spread) and the spread as % and in $
   - fee % and fee in $
   - quantity, gross notional, and total cash out (buy) or net proceeds (sell)
   - cash balance or holding after the trade
   - warnings or errors (insufficient funds, below minimum, price too old)
4. Confirm sends the same intent plus the price as-of timestamp the user saw. The server re-prices with the latest price. If a newer price arrived (the as-of differs), respond 409 with the new preview, so the user never pays a price they did not see. If the price is older than the max age, refuse with 422 or 409 and a clear message.
5. Result: a success toast or screen showing the actual fill (qty, price, fee), a link to the portfolio and history, and idempotency protection. The confirm button disables on click, and the request carries an idempotency key so a double-click or retry can't double-trade. The key is cheap in the DB (unique column on the trade).

Semantics of the "$ amount" input, which must be decided once and displayed clearly:
- Recommended: for Buy, "$ amount" means total cash spent including fee. Quantity = (amount) / (executed_price × (1 + fee%)), rounded DOWN or half-even to the coin's precision. For Sell by $ amount, it means gross notional to sell, and the fee is deducted from the proceeds. Alternative: the amount is the notional and the fee is charged on top. Either is fine if the preview shows the total unambiguously. The first is friendlier ("I spend $100").
- Rounding: quantity rounded to the coin's step with `ROUND_HALF_EVEN` (or DOWN for buys so cash never goes negative), fee and cash totals quantized to cents or 8 dp at one defined point. Store the quantized values on the trade row. Never recompute them later.

### P/L and average cost

Convention for retail simulators and most broker UIs (Investopedia, Robinhood, Coinbase, Binance "average price"): weighted-average cost, not FIFO. FIFO and specific-lot methods are tax-driven and not needed here.

Definitions (recommended for v1):
- On a buy of q coins at executed price p with fee f (USD): cost_basis += q×p + f. Quantity += q. avg_cost = cost_basis / quantity. Including the buy fee in the basis is the broker convention and makes P/L honest. (Binance's displayed "avg price" often excludes fees, so document the choice.)
- On a sell of q coins: avg_cost does NOT change. cost_basis -= q × avg_cost (reduce proportionally). Realized P/L for this sell = (q × executed_sell_price − sell_fee) − q × avg_cost. Cash += q×p − f.
- If quantity reaches exactly 0, reset cost_basis to 0. Handle it with exact Decimal arithmetic so no residue is left.
- Unrealized P/L per holding = quantity × mark_price − cost_basis. Percent = unrealized / cost_basis.
- Mark price: recommend mid (the latest cached market price) for valuing holdings. A buy then shows an immediate small loss equal to roughly spread + fee, which is exactly the lesson. Alternative: mark at the sell-side price (mid × (1 − spread)), the true liquidation value, which is more honest but looks harsher. Pick one, label it ("valued at market price"), and use it everywhere. Flag as a requirements decision.
- Total portfolio value = cash + sum(quantity × mark). Total P/L vs start = total value − 10,000 (and %). This is an identity, so it is robust and does not depend on the average-cost bookkeeping. Check: total P/L = total realized + total unrealized − (nothing else), because fees are already in cash and in the basis. Use this as an invariant in tests.
- Store on the holding row: quantity, cost_basis (not avg_cost, which is derived). Store realized P/L on each sell trade row (computed at execution, immutable) so history can show it and the sum gives total realized P/L cheaply.
- Selling every coin of a holding: keep the row with quantity 0 or delete it, but the portfolio view hides zero holdings.

### Portfolio screen

Typical contents (Investopedia "Portfolio", eToro portfolio, Binance wallet overview):
- Header summary: Total value, Cash available, Invested value (sum of holdings), Total P/L in $ and % vs $10,000 with green/red color and sign (plus an icon or text so color is not the only signal).
- Holdings table: coin, quantity, avg cost, current price, current value, % of portfolio, unrealized P/L $ and %, and a Trade/Sell action. On mobile, collapse into cards.
- Price as-of indicator for the page ("Prices as of 14:32, 1 min ago") using the OLDEST price among held coins, so the total is never presented as fresher than it is.
- Optionally a realized P/L line and a "fees paid" line.
- Empty state: "You have $10,000 in cash. Pick a coin to make your first trade."
- Auto-refresh via TanStack Query at about the price refresh interval, with no flicker.
- Show money to sensible display precision: USD to 2 dp, quantities up to 8 dp with trailing zeros trimmed, and tiny prices (e.g. $0.00001234) at enough significant digits. Values are formatted in the UI only from string decimals.

### How stale prices are communicated

Common patterns in trading UIs: a timestamp, a "live"/"delayed" badge, and disabling actions when data is unreliable.
- Every price shows a relative as-of ("42 s ago", tooltip with absolute local time) wherever it appears (coin list, trade form, preview, portfolio).
- Three states, tied to config thresholds: fresh (under about 2 refresh intervals), aging (amber badge and note "may be out of date"), stale (above the max trade age: red, trade button disabled, message "Prices are delayed, trading is paused. Last update 7 min ago.").
- The server remains the authority: the max age check happens at execution (and preview), and the error is a typed code the UI maps to a friendly message.
- If the provider is down, keep serving the last persisted price with its true timestamp (never fake "now"). Viewing the portfolio always works, and only trading is blocked.
- Record the exact price, timestamp, and mid on each trade, and show the price timestamp on trade history rows or in a detail view.
- Suggested starting thresholds (config, not code): refresh every 60 s, aging above 120 s, max trade age about 5 min. These are judgment values and should be tuned after real use.

### Small quantity and minimum trade rules

Exchanges enforce a minimum notional (Binance spot: about $5 to $10, varying per pair) and a per-coin lot step/precision (e.g. BTC 0.00001 step, others coarser). Paper-trading apps usually enforce less.
Recommended for v1:
- Minimum order value of about $1 (config) for both sides. It blocks zero or dust trades and avoids pointless history rows. Exception: allow selling an entire position even if it is below the minimum, so dust can always be cleared.
- Quantity precision: 8 decimal places max (matches NUMERIC(20,8)). A single global precision is enough for v1. A per-coin step is v2 and only if needed.
- Reject quantity <= 0, amounts with more than 2 dp for $ inputs, and quantities with more than 8 dp (validate, don't silently round the user's input). Rounding is only for derived values (quantity computed from a $ amount).
- Maximum: bounded by cash (buy) and by holding (sell). No other cap in v1.
- Sell by $ amount that exceeds the holding value: reject with a message, or clamp to a full sell only via the explicit "Sell all" button. Never clamp silently.
- A $-amount sell that would leave a tiny dust remainder is allowed. "Sell all" is the way to clear it.

## Feature Dependencies

```
Email OTP login -> user account -> $10k seed (cash row)
Price refresh job (single scheduler) -> price cache + persisted latest price -> coin list with as-of
Price as-of + max age -> preview/quote endpoint -> trade execution (same pricing function)
Config (spread, fee %, min order, max age) -> pricing function -> preview AND execution
Trade execution (transaction, row locks, idempotency key) -> holdings (qty, cost_basis) -> portfolio view
Trade execution -> trade rows (price, fee, realized P/L, price timestamp) -> trade history
Portfolio view -> needs price cache; total P/L needs only cash + holdings + marks
Realized P/L column -> needs avg cost at sell time (done in execution)
Deployment (domain, TLS, nginx, Resend) -> everything above in production
v2: portfolio chart -> snapshot job -> stored history
v2: limit orders -> background matcher -> reservation of cash or holdings
```

## MVP Recommendation

Prioritize, in order:
1. Prices: scheduled refresh, coin list with as-of and stale states (the data foundation, and no trade is correct without it).
2. Account: email OTP login plus the $10k seed.
3. Trading engine: pricing function (spread, fee, rounding), preview endpoint, atomic execution with row locks, idempotency, stale and minimum checks. This is the 100%-coverage critical path.
4. Portfolio and history: holdings with weighted-average cost (fees in basis), unrealized P/L, total P/L vs $10k, realized P/L stored per sell, keyset-paginated history.
5. Deploy: domain, TLS, real email, so friends can use it.

Include only low-cost differentiators: itemized cost in the preview, realized P/L on sell rows, allocation % column, oldest-price-as-of on the portfolio.

Defer (v2 backlog): value-over-time chart, price charts, watchlist, leaderboard, limit orders, trade notes, fees-paid summary, per-coin lot steps, notifications, other asset classes.

Push back on during requirements:
- Price-lock quotes: use the 409-on-newer-price rule instead.
- Per-coin precision rules: use one global precision.
- 24h change column: only if the data provider returns it for free. Do not make a second API call for it.

## Open decisions to make in requirements (flag for the user)

1. Mark price for holdings: mid (recommended) or sell-side price.
2. Meaning of the "$ amount" input: total including fee (recommended) or notional with the fee on top.
3. Buy fee in cost basis: yes (recommended).
4. Thresholds: refresh interval, aging threshold, max trade age, minimum order value (suggested above).
5. Whether the fee is charged in USD (recommended, simplest) or in the coin (Binance style, more confusing).

## Sources

- Training-data knowledge of Investopedia Stock Simulator, Binance spot and demo trading, eToro virtual portfolio, Wall Street Survivor, and Coinbase and Robinhood cost-basis display conventions. MEDIUM-LOW confidence, not re-verified online this session.
- Weighted-average cost accounting and the realized/unrealized split are standard accounting conventions. MEDIUM-HIGH confidence.
- Exchange minimum-notional and lot-size behavior (Binance exchange filters `MIN_NOTIONAL` and `LOT_SIZE`). MEDIUM confidence, and the exact values should be checked if per-coin rules are ever added.
- Project constraints: `/home/Birja/.planning/PROJECT.md` and `/home/Birja/CLAUDE.md`.
