# Architecture Research: Birja v1.1 US Stock Trading

**Domain:** Adding twenty curated US equities to an existing virtual-money crypto simulator
**Researched:** 2026-11-10
**Confidence:** HIGH for existing integration points and financial invariants; MEDIUM for proposed schema boundaries; provider, rights and corporate-action decisions remain gates.

## Recommendation

Extend the existing FastAPI monolith, shared USD account, holdings and immutable trade records. Keep one dedicated scheduler container with independent bounded crypto and stock refresh work. Do not introduce a brokerage integration, matching engine, Celery, message bus or second cash ledger.

Stock trading is conditional on an explicitly selected and permitted feed. Listing on NYSE/Nasdaq and a quote originating on those venues are different concepts. An IEX-only quote for a Nasdaq-listed company must never be described as a consolidated market quote. Alpaca documents this difference and exposes explicit feed selection; this is an architectural example, **not a selected or approved provider**. See [Alpaca market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) and [latest-quotes reference](https://docs.alpaca.markets/us/reference/stocklatestquotes-1).

```text
React markets / trade ticket / combined portfolio / stored history
                         |
                  FastAPI services
               /                    \
 instrument + quote reads       shared trading executor
                                account lock → policy → holding lock
               \                    /
          PostgreSQL: durable assets, quotes, accounts, holdings, fills
                         ^
            one scheduler process, bounded tasks
                 /                  \
        existing Kraken         stock provider + session/status sources

Redis: existing auth/rate-limit state and scheduler lease; no unique money state
```

## Existing System Evidence

| Existing boundary | Current behavior | Consequence for stocks |
|---|---|---|
| `backend/app/models/price.py` | `Coin` maps to `coins`; globally unique symbol and required unique `kraken_pair`. `Price` is keyed by `coin_id`, stores `mid`, `as_of`, and source limited to `kraken`/`fake`. | Stock rows cannot simply be seeded. Identity, nullable provider-specific fields, source checks and provenance need forward migrations. |
| `backend/app/models/trade.py` | Holdings have `(user_id, coin_id)` uniqueness and fee-inclusive cost basis; fills append price/time/cash/quantity/idempotency data. | Reuse these tables and identities rather than parallel stock holdings/trades. Preserve existing IDs, FKs and historical fills. |
| `backend/app/services/trading.py` | Account row lock before holding lock; replay precedes price checks; preview/fill use shared pure math; execute reloads current price. | A stock buy must serialize against a simultaneous crypto buy through the same account row. Replay must remain valid after market close. |
| `backend/app/services/trade_math.py` | Exact Decimal math; crypto dollar buys intentionally floor quantity to eight decimals; partial sells update stored basis. | Quantity policy belongs before shared planning: integral stock orders must never flow through fractional dollar-buy math. |
| `backend/app/tasks/scheduler.py` | One loop, HTTP call outside DB transaction, Redis token lease, bounded cycle, per-coin validation. Kraken ticker has no event timestamp, so current `as_of` is arrival time. | Preserve crypto behavior; stocks need actual source time, independent source failures and timing budgets. Do not copy the Kraken timestamp convention into equities. |
| `backend/app/services/prices.py` | Upsert only if incoming `as_of` moves forward; missing/invalid quotes leave last good price. | Retain monotonic event-time updates and last-good valuation, with independently expiring stock execution eligibility. |
| `backend/app/services/portfolio.py`, `portfolio_math.py` | One account/positive-holdings/asset/price outer join; inactive holdings remain visible; missing prices invalidate totals. | Extend the same statement and valuation math across asset classes. Session closure must not remove stock holdings or zero their values. |
| `backend/app/services/history.py` | User-scoped `(created_at, id)` descending keyset pagination over one fills table. | One chronological crypto/stock history remains simple; no UNION of separately numbered fills. |
| `frontend/src/api/{prices,trades,portfolio,history}.ts`, hooks and pages | Runtime response guards, symbol-only identity, TanStack Query keys and shared invalidation. | Add instrument identity/type throughout query keys and guards, not just stock labels on a market page. |

## Instrument Identity and Safe Generalization

**Recommended smallest expansion:** introduce an instrument vocabulary in code while retaining the existing physical `coins` table and `coin_id` FK columns during v1.1. Those are storage compatibility names, not public stock terminology. A broad table/column rename adds release and recovery risk without user value. Retain `Coin` compatibility where needed while services move toward `Instrument` concepts.

Add asset class (`crypto`/`stock`), quote currency (`USD` for this milestone), listing exchange/calendar metadata for stocks, quantity step and a provider symbol mapping. Current crypto IDs remain exactly the same; add stock IDs from the same identity sequence. `kraken_pair` becomes nullable only for stock rows, with type-aware checks preserving required valid Kraken mapping for crypto. Avoid a general provider registry until more than the two concrete adapters require it; one explicit stock mapping is enough.

Symbol is a display label and provider lookup value, not the global identity. Relax global symbol uniqueness through an explicit migration and enforce an unambiguous curated identity such as `(asset_class, symbol)` for this milestone, with listing venue stored separately. Provider symbols may contain punctuation; do not extend the existing alphanumeric regex into a universal stock identifier. Stable numeric asset ID is the durable identity, including across ticker changes. No automatic delete/reinsert on a rename or delisting.

**Compatibility contract:** preserve existing symbol-only requests as crypto requests. Add an explicit mutually exclusive asset-ID selector for generalized requests, or an equivalently explicit stock route; never reinterpret a legacy symbol as a stock because it matches first. Keep legacy `/api/v1/prices` crypto-default behavior while adding an explicit asset filter/catalog path for the updated UI. Old `/holdings/{symbol}` crypto lookups keep their meaning. Add asset ID/class to generalized price, quote, fill, portfolio and history responses without removing existing fields. Update strict schemas, response guards and request `extra="forbid"` contracts together.

On the frontend, scope new quote/holding keys by asset ID and order inputs, not symbol alone. Update `useTrade` invalidation for the new catalog/quote/holding keys while continuing to invalidate shared `me`, portfolio and history. Keep TanStack Query; do not fetch a provider from the browser or expose its credentials.

## Quote and Market-State Contracts

Normalize a stock observation at the provider boundary into a small typed record:

| Field group | Required meaning |
|---|---|
| Identity | Stable asset ID plus explicitly configured provider symbol. |
| Price | Positive finite Decimal; bid/ask mid only if the feed supplies a valid usable pair. A last trade is labelled `last_trade`, not called a mid; a bar close is not silently substituted for either. |
| Time | Source/event timestamp, local fetched/received timestamp and applicable session date. Freshness uses event time; excessively future timestamps are rejected rather than clamped fresh. |
| Provenance | Provider, explicit feed and venue coverage, price kind, currency, raw/adjusted semantics. Immutable fills preserve the provenance actually used. |
| Status | Session/calendar authority and validity; instrument halt/availability status with its own observed time and validity. Unknown or expired status does not mean open. |

If the selected provider only supplies last-trade prices, owner acceptance of that reference-price semantics must precede changes to the existing `mid` contract. If it supplies eligible bid/ask data, retain the familiar midpoint valuation and simulated spread/fee, subject to the separately approved stock cost policy. Explicitly reject unsupported feed fallback; never let a subscription-dependent API default choose execution coverage.

Store latest good prices in PostgreSQL. Do not overwrite a good quote with zero, malformed data or old timestamps. Repeatedly receiving yesterday's quote does not renew its event timestamp or execution validity. Persist enough latest status/calendar metadata to make execution independent of Redis survival. The exact representation (bounded session rows and per-asset status columns/table) should follow the chosen provider; avoid storing an unbounded market-data history.

**Calendar is not status.** NYSE documents regular hours and specific holidays/early closes; Nasdaq separately documents instrument trading halts. Model the regular interval in `America/New_York`, derive UTC boundaries for each date, and use an open-inclusive/close-exclusive predicate. Do not hardcode a fixed UTC offset or Monday–Friday rule. A calendar library or provider schedule still needs a documented validity horizon and exceptional-closure update policy. See [NYSE calendar](https://www.nyse.com/trade/hours-calendars) and [Nasdaq halt codes](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes).

If a reliable timely halt/status signal is unavailable within the approved free data arrangement, do not claim faithful halt enforcement. This is a feasibility/scope decision to surface before enabling stock orders, not an excuse to infer tradability from a recent quote.

## Execution Flow and Concurrency

Reuse one transaction and deterministic lock order:

1. Authenticate and validate the explicit instrument selector and exact Decimal input.
2. Lock the user's existing account row `FOR UPDATE`.
3. Find a user-scoped idempotency replay before evaluating today's session, price, inactive status or halt. Compare stable asset identity plus side/input/value, and return the original stored fill on a matching replay. Reusing a key across crypto and stock must conflict.
4. Load authoritative instrument, quote and bounded market status. For stocks, require approved feed, recent source timestamp, current regular session, known nonhalted status and allowed whole-share order type.
5. Lock the holding and construct the pure trade plan, with exact shared cash/fee/cost-basis math.
6. **Resample current time and re-evaluate stock eligibility after all awaited lock acquisition**, including holding/status locks. Refuse a request that waited past close, quote expiry or status validity. The existing crypto check is already after account lock; do not introduce a stock-only pre-lock check.
7. Verify the current quote against the preview. Retain `expected_mid` behavior for crypto. Stock preview comparison must also bind feed/price kind/session or a deterministic quote version so unchanged numeric price cannot conceal a source/policy change.
8. Write cash, holding, basis and immutable fill/provenance atomically, then commit. Any refusal rolls back everything.

Avoid provider network calls while holding financial DB locks. The scheduler persists bounded state before execution. Where status updates race with fills, serialize the relevant status row/version in a documented common lock order and recheck after waits. This yields an atomic decision against the latest ingested state; periodic ingestion cannot promise zero-latency awareness of external halts. Document the actual bounded status delay.

Whole-share buys and sells use quantity input only and require `quantity == quantity.to_integral_value()` with positive value; reject fractions rather than rounding them. Preserve fractional crypto, exact-eight-decimal storage and minimum/whole-position rules. For a DB-level integral-stock invariant, use a denormalized checked asset class on holdings/fills tied to the catalog through a composite FK, then a conditional integral-quantity CHECK. A PostgreSQL row CHECK cannot safely enforce a rule by looking up another table. Resolve reverse-split residual policy before assuming every future stock holding must remain integral.

Keep simulated execution language. This is not routing an actual exchange market order and does not model order-book liquidity, partial fills, margin or settlement. Reuse current immediate simulated cash availability unless the owner explicitly adds settlement as scope.

## Combined Valuation, History and Corporate Actions

Keep one account and one portfolio statement. Show stock values using the latest appropriate regular-session observation while closed, labelled with its actual timestamp and reference kind. A retained quote is not automatically an official closing-auction price. Closed session, quote recency, valuation availability and tradability are separate states; a normal weekend must not look like all stock data failed, and must never enable stock orders. Missing prices still make totals incomplete; do not count unpriced stock as zero or omit an inactive held stock.

Preserve fee-inclusive cost basis and average-cost sell accounting. Existing fills remain immutable facts; do not retroactively rewrite purchase prices on a split to make today's holdings reconcile. `history.py` currently joins current catalog names/symbols; if historical ticker labels are required for stocks, snapshot them on new fills. Do not backfill invented historical symbols for old rows.

**Owner decision still required before stock enablement:** split/reverse-split, dividend and delisting treatment. A split changes share count and reference price; ignoring the count while accepting the new quote creates fictitious P/L. The SEC explains the stock-count effect in its [stock-split glossary](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split).

Two viable bounded policy branches, neither assumed approved:

- **Explicit limited simulator:** owner accepts no simulated dividends/total-return claim; affected instruments are frozen before a corporate action until an audited resolution. This requires a reliable detection/review path; simply declaring corporate actions out of scope does not protect existing holders.
- **Minimal supported action handling:** an immutable action identifier plus account-scoped idempotent adjustment record updates quantity/cost basis under the same account lock, preserving existing fills. Split total basis remains unchanged; reverse-split fractions need an explicit residual/cash-in-lieu decision. Dividend crediting requires an explicit entitlement-date/amount policy and durable cash adjustment record. A first implementation need not become a general accounting engine.

Do not use adjusted historical bars for execution while leaving holdings unchanged. Feed adjustment semantics, action scheduling and the quantity CHECK must agree. If neither safe policy is available, keep stocks disabled and preserve crypto operation.

## Scheduler, Quota and Failure Isolation

Retain a single scheduler process and current lifespan-managed HTTP/DB/Redis clients. Add stock polling/status refresh as separate bounded work so provider 429s, entitlement errors or a closed stock session do not consume the full crypto cycle timeout. Existing `CYCLE_TIMEOUT_S`, `SOURCE_TIMEOUT_S` and Redis lease assumptions cannot simply be stretched by appending another slow request. Keep per-source budgets, bounded backoff and explicit cancellation, with any concurrency bounded inside the one process.

Refresh stocks in approved batched calls during relevant sessions, with minimal bounded calendar/status maintenance outside sessions. Do not poll once per browser, per API worker, or per holding. Preserve per-asset missing-data isolation and monotonic upserts. Repeated observations of the same event are not independent confirmation of a price spike; adapt current crypto spike confirmation carefully. Split-related jumps must not be mechanically accepted after a few polls.

For tens of friends, provider quota and rights are the first constraint, not PostgreSQL capacity. Measure actual API credits per batched call, not just HTTP request count. Keep latest observations only; no new chart snapshots or tick archive in this milestone.

## Migration, Privilege and Recovery Integration

All changes are new migrations after `0008`; never edit shipped migrations. Expand with crypto-safe defaults, backfill existing rows while preserving every ID and value, then enforce constraints after validation. Use an explicit downgrade or explain why existing stock fills make a downgrade unsafe. Do not delete new financial records to force a downgrade. Prove old crypto API/money results remain equivalent on a seeded `0008` upgrade.

This repository has **schema-specific operational contracts**:

- `deploy/db/bootstrap-roles.sql` currently admits only revisions `0007`/`0008`, enumerates tables, grants app append-only access to fills and scheduler write access to prices, and intentionally grants no automatic privileges to new tables. New catalog/status tables, sequences and migrations need explicit least-privilege decisions. Do not solve deployment with superuser runtime access or blanket grants.
- `deploy/backup-manifest.sql` hashes explicit old table columns and a fixed table list. `deploy/backup-snapshot.py` validates that exact set. A dump may contain a new table while the old integrity proof omits it; update versioned manifest/validation and restore assertions deliberately.
- Recovery and deploy tooling is retained and authenticated separately from the app checkout. Plan reviewed successor artifacts and compatibility with older retained backups; changing the repository script alone does not update an installed timer. Do not mutate production recovery material during research or routine development.
- Provider secrets stay server-side and out of fixtures, logs and chat. A live stock release must include required new configuration in encrypted recovery custody, while keeping old restore instructions usable.

These are part of a stock schema release, not optional future hardening. They do not authorize live operations. Isolated real-PostgreSQL/Redis tests, migration/role tests, restore rehearsals and fresh strict image/security gates remain required at their normal workflow steps.

## Suggested Build Order: Runnable User Slices

| Candidate phase | Runnable result | Mandatory dependency / proof |
|---|---|---|
| **7 — Stock data feasibility and truthful market view** | Existing crypto works; approved curated stocks appear with real source age, feed attribution and closed/unknown states; stock trading remains disabled until eligibility is proven. | First gate: free quota, user display rights, actual recency, feed coverage, status/calendar and chosen corporate-action policy. Stop and ask scope questions if no viable provider; do not promise a provider first and discover licensing at rollout. Catalog/provenance schema includes recovery compatibility work. |
| **8 — Whole-share stock trade end to end** | Preview/buy/sell a stock during the regular session using shared USD; resulting holdings/history appear in existing combined screens. | Stock/crypto concurrent overspend, replay after close, holding-lock expiry, early close/DST/holiday, unknown/halt and feed-change tests. Integrality enforced at service/DB boundaries. Basic combined portfolio/history is part of this slice, not deferred until after live stock fills. |
| **9 — Multi-asset acceptance and release** | Complete combined filters/labels and offline/closed experience, corporate-action policy proofs, tested upgrade/recovery, owner acceptance and separately authorized release. | Mixed portfolio math, unchanged immutable fills, price age versus closure, failed-provider isolation, restricted roles, `0008` upgrade and isolated exact restore. No premature production enablement. |

Phase names/counts are recommendations for the roadmapper, not approved plans. If corporate actions require a supported adjustment workflow, include it before enabling long-lived stock holdings rather than burying it after release.

## Planner Pitfalls to Carry Forward

- Refreshing old data each minute does not satisfy recent prices.
- A listing venue, a single-venue data feed and a consolidated feed are distinct.
- A calendar-open result alone cannot rule out a halt or stale status.
- Checking session before locks permits fills after closing time.
- Rechecking today's session before idempotency breaks legitimate replays.
- Separate stock accounts/executors can defeat cross-asset cash serialization.
- Global symbol-only identity corrupts cache keys and ambiguous order selection.
- Dollar-input crypto math silently creates fractional stock fills.
- Accepting post-split prices without position treatment invents investment losses.
- Hiding closed/inactive stocks or rounding missing prices to zero falsifies portfolio totals.
- New schema that passes superuser tests can still fail live restricted roles or invalidate backup integrity assumptions.

## Sources and Confidence

Existing behavior is verified directly in the repository paths above (HIGH). Proposed integration structure is an engineering recommendation (MEDIUM), not a claim that it is implemented. Official pages checked on 2026-11-10; rolling documentation does not establish Birja's account-specific entitlements or display rights.

- [NYSE hours/calendar](https://www.nyse.com/trade/hours-calendars): HIGH for current published session/holiday examples; future exceptional closures require maintained data.
- [Nasdaq trading-halt codes](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes): HIGH for distinct halt/resumption states; not proof of an approved machine-readable source or rights.
- [Alpaca market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq): HIGH for provider-documented feed distinctions and latest-data semantics; no provider selected.
- [Alpaca latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1): HIGH for batch quote endpoint, bid/ask data and explicit feed choices.
- [SEC stock-split glossary](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split): HIGH for split effect; simulator action policy remains undecided.

No library addition/version is recommended here; this architecture reuses the locked stack. No private provider API, production database, service or tests were accessed for this research.
