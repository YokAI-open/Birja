# Phase 4: Trading - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning
**Source:** plan-phase questions (no discuss-phase run, no UI-SPEC)

<domain>
## Phase Boundary

Signed-in users buy and sell the 15 curated coins with market orders at recent prices. They see the cost before confirming, and the result is correct to the cent. Requirements: TRADE-01 to TRADE-08.

- Buy by dollar amount, where the amount is the total cash spent including the fee.
- Buy or sell by quantity, with up to 8 decimals.
- A preview before confirming, the actual fill after.
- Refusals for stale prices, insufficient funds and the minimum order size.
- Idempotent submission, and safe concurrency against real Postgres.

Portfolio valuation, P/L and trade history are Phase 5. This phase records every trade so Phase 5 can show them.

</domain>

<decisions>
## Implementation Decisions

### Costs
- **D-01:** **Spread is 0.25% and the fee is 0.25%**, both settings, not hard-coded.
  - Buy execution price = mid × (1 + 0.0025). Sell execution price = mid × (1 − 0.0025).
  - The fee is 0.25% of the trade's USD value (notional at execution price), charged in USD.
  - Buys pay notional + fee. Sells receive notional − fee.
  - This is the PROJECT.md "Simulated pricing" decision with concrete values.
- **D-02:** **A "$ amount" buy is the total cash spent including the fee** (PROJECT.md key decision). Cash drops by exactly the typed amount, and the quantity is derived from it. Rounding rules for cents and 8-decimal quantities follow CLAUDE.md "Money and numbers". Research proposes the exact rounding points, so that cash change = typed amount to the cent and the quantity never overspends.

### Price age
- **D-03:** **The maximum price age for a trade is 120 s**, the same as Phase 3's "fresh"/Live threshold. Trading is allowed only while the price shows **Live**; Delayed or Stale prices refuse the trade with a clear message.
  - Reuse the single freshness definition from Phase 3 (`price_fresh_seconds`). Do not add a second constant.
  - The trade records the exact mid price and its `as_of` that it used (CLAUDE.md "Staleness is visible").
  - If the price changed since the preview, the user sees the new preview instead of a silent fill (TRADE-05).

### Minimum order
- **D-04:** **The minimum order is $1.00** of notional (setting).
  - Selling a whole position is always allowed even below $1.00 (TRADE-06).
  - Sell, buy and quantity inputs below the minimum are refused with a clear message.

### UI
- **D-05:** **Trading lives on a separate `/trade/<coin>` page** (react-router; Phase 3 added the router).
  - The Markets rows link to it.
  - The page shows the coin's live price and freshness badge, a Buy/Sell switch, an input for a $ amount (buy) or a quantity, a live preview, Confirm, then the fill result and the new cash balance.
  - It handles states for refused (stale, insufficient, minimum) and price-changed.
  - Signed-in only, like everything else (Phase 3 D-02). Unknown coin symbols redirect to `/`.
  - Style comes from MASTER.md and existing components. No UI-SPEC: the user skipped it.

### Decided after research (2026-10-28)
- **D-06: Minimum fee is $0.01.** The fee is `max($0.01, round_half_even_cents(notional × 0.25%))` (min fee as a setting). The user chose this over a $0.00 fee on tiny trades.
  - **Buy by $ amount A:** `fee = max(0.01, q2(A·f/(1+f)))`, then `budget = A − fee` and `qty = floor8(budget / exec_price)`. Cash change is still exactly −A.
  - **Buy by quantity:** `fee = max(0.01, q2(qty·exec·f))` and `total = q2(qty·exec) + fee`. Keep the parts reconciling: total = notional + fee.
  - **Sell by quantity:** `fee = min(max(0.01, q2(notional·f)), q2(notional))`. The fee is capped at the trade's value, so **proceeds are never negative**. This matters because selling a dust position worth less than a cent is allowed (D-04 whole-position exemption).
  - RESEARCH's worked examples must be re-derived for this rule, and tests must cover a $1.00 buy (fee $0.01) and a sub-cent whole-position sell (proceeds $0.00, fee equals notional).
- **D-07: Track cost basis now.** `holdings.cost_basis` (`NUMERIC(20,8)`, `CHECK >= 0`) is updated in the same transaction.
  - A buy adds the cash spent, including the fee.
  - A sell reduces the cost basis in proportion to the quantity sold. Round to cents at a defined point, and a full sell sets it to 0.
  - Phase 5 uses it for average cost (PORT-03). No realized P/L (v2).
- D-04 minimum for $-amount buys is checked against the typed amount A (fee-inclusive, D-02); quantity buys and sells check notional.
- **Accepted research defaults:**
  - "Price changed" means a different **mid**, not just a newer `as_of`.
  - No rate limiting on the trade endpoints in v1.
  - The UI dispatches on `detail.code`, so the HTTP status numbers can still change.
  - Stateless quote, with no server storage.
  - Lock order: account `FOR UPDATE` first, then holding.
  - Idempotency key `UNIQUE(user_id, idempotency_key)`. A replay returns the original fill.
  - `accounts.cash` stays whole cents (`CHECK cash = round(cash, 2)`). Add it in its own migration only if existing rows comply; verify before adding.

### Claude's Discretion
- **Schema:** `holdings` (one row per user and coin, quantity `NUMERIC(20,8)`, `CHECK >= 0`) and `trades` (side, quantity, mid used, its `as_of`, execution price, fee, cash delta, timestamps, idempotency key), all with FKs and indexes per CLAUDE.md. Cash stays in `accounts`. Research decides the exact columns. History pagination is Phase 5, so only add the indexes this phase's queries need.
- **Preview/confirm mechanism:** for example a server-issued quote with an id, mid and as_of, plus a short TTL; confirm re-checks the current price and returns a new preview if it moved.
- **Idempotency:** a client-generated key plus a UNIQUE constraint (CLAUDE.md "rely on DB constraints").
- **Locking:** a single transaction with `SELECT … FOR UPDATE` on the account and holding rows; a concurrency test with many parallel buys against real Postgres (TRADE success criterion 5).
- **Coverage:** trade execution and money math go on the CI 100% critical-path list (CLAUDE.md Test culture).
- **Release:** whether this phase ends with a release to https://birja.nist.one is decided at its push gate, as in Phase 3. The deploy tooling now re-runs itself, so one deploy is enough.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `CLAUDE.md`: Money and numbers; Data, caching & background jobs (Transactions, FOR UPDATE, constraints, staleness); API (thin routes, uniqueness and races); Security (CSRF on POST); Test culture (100% on money and trade execution)
- `.planning/PROJECT.md`: "Simulated pricing" and Key Decisions ("$ amount" = total incl. fee; holdings valued at mid)
- `.planning/phases/03-prices/03-CONTEXT.md` + summaries: freshness definition, `prices`/`coins` tables, `/api/v1/prices`, MarketsPage, router
- `.planning/phases/02-authentication/` summaries: `accounts.cash` (NUMERIC(20,8), CHECK ≥ 0), CurrentUserDep, CSRF dependency, apiFetch
- `design-system/birja/MASTER.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- Limit/stop orders, short selling, other asset classes: v2 (REQUIREMENTS)
- Portfolio/P&L/trade history views: Phase 5
- UI-SPEC: skipped by the user

</deferred>

---

*Phase: 04-trading*
