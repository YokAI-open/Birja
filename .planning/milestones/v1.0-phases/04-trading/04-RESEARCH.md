# Phase 4: Trading - Research

**Researched:** 2026-10-28
**Domain:** Simulated market-order execution (money math, idempotency, row-locking concurrency) on FastAPI + SQLAlchemy async + Postgres, with a React trade page
**Confidence:** HIGH (design is built on the existing codebase and Postgres semantics; worked examples were computed with Python Decimal in this session)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Spread is 0.25% and the fee is 0.25%, both settings, not hard-coded. Buy execution price = mid x (1 + 0.0025). Sell execution price = mid x (1 - 0.0025). The fee is 0.25% of the trade's USD value (notional at execution price), charged in USD. Buys pay notional + fee. Sells receive notional - fee.
- **D-02:** A "$ amount" buy is the total cash spent including the fee. Cash drops by exactly the typed amount, and the quantity is derived from it. Rounding rules for cents and 8-decimal quantities follow CLAUDE.md "Money and numbers". Research proposes the exact rounding points, so that cash change = typed amount to the cent and the quantity never overspends.
- **D-03:** Maximum price age for a trade is 120 s, the same as Phase 3's "fresh"/Live threshold. Trading is allowed only while the price shows Live; Delayed or Stale prices refuse the trade with a clear message. Reuse `price_fresh_seconds`; no second constant. The trade records the exact mid and its `as_of`. If the price changed since the preview, the user sees the new preview instead of a silent fill (TRADE-05).
- **D-04:** Minimum order is $1.00 of notional (setting). Selling a whole position is always allowed even below $1.00 (TRADE-06). Inputs below the minimum are refused with a clear message.
- **D-05:** Trading lives on a separate `/trade/<coin>` page (react-router). Markets rows link to it. The page shows the coin's live price and freshness badge, a Buy/Sell switch, an input for a $ amount (buy) or a quantity, a live preview, Confirm, then the fill result and the new cash balance. It handles refused (stale, insufficient, minimum) and price-changed states. Signed-in only. Unknown coin symbols redirect to `/`. Style from MASTER.md; no UI-SPEC.

### Claude's Discretion
- Schema: `holdings` (one row per user and coin, quantity NUMERIC(20,8), CHECK >= 0) and `trades` (side, quantity, mid used, its as_of, execution price, fee, cash delta, timestamps, idempotency key), FKs and indexes per CLAUDE.md. Cash stays in `accounts`. Only add indexes this phase's queries need.
- Preview/confirm mechanism (e.g. server-issued quote with id, mid, as_of, short TTL; confirm re-checks the price and returns a new preview if it moved).
- Idempotency: client-generated key plus a UNIQUE constraint.
- Locking: single transaction with SELECT ... FOR UPDATE on account and holding rows; concurrency test with many parallel buys against real Postgres.
- Coverage: trade execution and money math go on the CI 100% critical-path list.
- Release: decided at the push gate; deploy tooling re-runs itself.

### Deferred Ideas (OUT OF SCOPE)
- Limit/stop orders, short selling, other asset classes (v2)
- Portfolio/P&L/trade history views (Phase 5)
- UI-SPEC (skipped by the user)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRADE-01 | Buy by $ amount, amount = total cash incl. fee | Section "Money math", scheme B1 (fee first, then floor quantity) |
| TRADE-02 | Buy/sell by quantity, up to 8 dp | Scheme B2/S1; Pydantic `decimal_places=8` |
| TRADE-03 | Preview: market price, exec price, fee, quantity, total cash change | Stateless `POST /trades/quote` |
| TRADE-04 | Mid +/- spread plus % fee in USD | `trade_math.py` pure functions, settings |
| TRADE-05 | Stale price refused; changed price -> new preview | Confirm check order; 409 `stale_price` / `price_changed` + embedded fresh quote |
| TRADE-06 | Insufficient cash/coins and minimum refused; whole-position sell allowed | Check order under lock; `qty == held` exemption |
| TRADE-07 | Same trade twice executes once | `UNIQUE(user_id, idempotency_key)` + account row lock + replay lookup before any price check |
| TRADE-08 | Fill shown: quantity, price, fee, new cash | `FillOut` includes `cash_after`, built from the persisted row |
</phase_requirements>

## Summary

Phase 4 adds two tables (`holdings`, `trades`), one pure money-math module, one DB execution service, three endpoints and one React page. No new services, no new packages, no new infrastructure. The scheduler already writes `prices(coin_id, mid, as_of)`; the trade path only reads it.

The central design choices: (1) **stateless quote** — nothing is stored for a preview; the confirm request carries the same order input plus `expected_mid`, and the server recomputes everything under the account lock and refuses with 409 `price_changed` (embedding the fresh quote) if the mid moved; (2) **account row `FOR UPDATE` is the one lock** that serializes all of a user's trades, so idempotency lookup, funds check, cash update, holding upsert and trade insert are race-free, with the DB CHECK constraints and the `UNIQUE` key as backstops; (3) **cash is kept in whole cents**: every trade's cash delta is quantized to 2 dp, the typed `$` amount is the exact cash change, and the fee is computed first so the quantity (rounded DOWN to 8 dp) can never overspend.

**Primary recommendation:** Implement `app/services/trade_math.py` (pure, Decimal, no I/O) and `app/services/trading.py` (lock -> replay check -> price checks -> plan -> apply), with `plan_trade()` shared by quote and confirm so the preview can never disagree with the fill.

## Project Constraints (from CLAUDE.md)

- MVP first: no speculative models/endpoints. Flag Phase 5 items (history index, portfolio list, realized P/L) instead of building them.
- Money: `Decimal` / `NUMERIC(20,8)` default; JSON money as strings; explicit `quantize(..., ROUND_HALF_EVEN)` at defined points only, never round intermediates; timestamptz UTC.
- Transactions: one DB transaction per trade, `with_for_update()` on rows read then updated; schema invariants (`NOT NULL`, FK, `UNIQUE`, `CHECK`).
- bigint identity PKs; `text` not varchar; index FKs only for real queries; keyset pagination later (Phase 5).
- Staleness visible: record exact price and as_of used; refuse beyond max age.
- API: `create_app()`/lifespan, `Annotated` Dep aliases, thin routes (service owns transaction), uniqueness via constraint + `IntegrityError`, 401 vs 403 separate, `summary`/`response_model`/`tags` on every endpoint, `/api/v1`.
- Security: CSRF on every POST (existing `CsrfDep`); authorize server-side via `CurrentUserDep`; never log tokens/PII.
- Tests: new feature ships with tests; 80% overall, 100% on critical paths (money, trade execution); API tests for every endpoint; real Postgres, never mock the DB; no real email in tests/e2e (console backend, PRICE_SOURCE=fake).
- Migrations: autogenerate then review; schema-only; working `downgrade()`; immutable once merged; update the CLAUDE.md "Common commands" block and `.github/workflows/ci.yml` when the 100% list changes (they must stay identical).
- Frontend: TanStack Query for all API calls; shadcn/ui + MASTER.md tokens only; no `useEffect` fetching.
- Git: feature branch from develop, push only after asking.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fill/fee/quantity computation | API / Backend (`trade_math.py`) | — | Money must never be computed by the client; client only displays |
| Quote (preview) | API / Backend | Browser (renders, debounces) | Server is the single source of the numbers shown and executed |
| Price-age and price-changed checks | API / Backend (inside the trade txn) | — | Must read price under lock; UI badge is cosmetic only |
| Idempotency | Database (`UNIQUE`) + API | Browser (generates UUID per attempt) | CLAUDE.md: rely on DB constraints; client key is only an input |
| Cash/holding atomicity, no-overspend | Database (row lock, CHECK) | API | Concurrency safety must hold with N workers/processes |
| Cost basis maintenance | API / Backend (same txn) | — | Derived state updated atomically with the trade |
| Trade page, input validation UX, key generation | Browser / Client | — | Presentation; server re-validates everything |
| Price source | Existing scheduler -> `prices` table | — | Unchanged; trades only read |

## Standard Stack

No new packages. Everything below already exists in the repo. [VERIFIED: codebase read of backend/app/*, frontend/src/*]

### Core
| Library | Purpose | Use in this phase |
|---------|---------|-------------------|
| FastAPI + Pydantic v2 | Routes, request validation | `TradeIn` models; Decimal serialises to JSON strings (as `MeOut.cash_usd` already does) |
| SQLAlchemy 2.0 async + asyncpg | DB access | `select(...).with_for_update()`, `pg_insert ... on_conflict` |
| Alembic | Migration `0006` | Two tables + accounts cents CHECK |
| `redis` rate limiter (`services/ratelimit.py`) | Optional | Not needed in v1 (see Open Questions) |
| React 19 / react-router / TanStack Query / shadcn (`button`, `card`, `input`, `badge`) | Trade page | New: `TradePage`, hooks, api module |
| pytest + pytest-asyncio + httpx + real Postgres test stack | Tests | Concurrency test uses the existing `auth_client`/`running_app` fixtures |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stateless quote | Stored quote (Redis TTL / Postgres) | Adds storage, expiry, a lookup and a "quote not found/expired" error path for no safety gain: the server must re-read the price under lock anyway. Rejected. |
| Property tests with Hypothesis | Seeded `random.Random` loops in pytest | Hypothesis would be a new dev dependency (needs legitimacy check, CI time). Seeded loops give the same invariant coverage with no package. Use seeded loops. |

**Installation:** none. **Package Legitimacy Audit:** no external packages are added; slopcheck not required. Packages removed: none. Packages flagged: none.

## Money Math (the exact scheme)

All of this lives in `app/services/trade_math.py`: pure functions, `Decimal` only, no I/O, wrapped in `localcontext()` with `prec = 50` so products of two 8-dp numbers are exact (default prec 28 is enough for realistic values, but pinning it removes a class of surprise). [ASSUMED: Decimal default prec 28 is sufficient; pinning is cheap insurance]

**Constants (settings, Decimal fractions like `price_max_move`):** `trade_spread = 0.0025`, `trade_fee = 0.0025`, `trade_min_order_usd = 1.00`. Validate `0 <= spread < 1`, `0 <= fee < 1`, `min_order > 0` in `Settings` (backend only; the scheduler's `SchedulerSettings` does not need them).

**Rounding points (the complete list; nothing else is rounded):**

| # | Point | Quantum | Mode |
|---|-------|---------|------|
| R1 | `exec_price = mid x (1 +/- spread)` | 1e-8 | HALF_EVEN |
| R2 | Buy-by-$ quantity | 1e-8 | **DOWN** (the one deliberate exception; rounding up could overspend) |
| R3 | Fee in cents | 0.01 | HALF_EVEN |
| R4 | Cash total (buy debit / sell credit) in cents, qty paths only | 0.01 | HALF_EVEN |

Typed `$` amounts are already on the cent grid (validated `decimal_places=2`), so they are never rounded.

**B1. Buy by $ amount `A` (total cash out, fee included) — TRADE-01/D-02**
```
exec   = q8(mid * (1 + spread))                      # R1
fee    = q2(A * f / (1 + f))                         # R3: the fee implied by a total of A
budget = A - fee                                     # exact cents: what is spent on coins
qty    = floor8(budget / exec)                       # R2 (ROUND_DOWN)
cash_delta = -A                                      # exactly the typed amount
notional   = budget                                  # reported as "coins value"
```
Guarantees: `cash_delta == -A` to the cent; `qty * exec <= budget` so coins never cost more than the budget; the unspent dust (< 1e-8 x exec, at most about $0.001 for BTC at $100k) stays in the fee/dust remainder and is **not** returned (cash change must equal the typed amount). Reject if `qty < 1e-8` (`below_minimum`) or `budget < min_order`.

**B2. Buy by quantity `q` — TRADE-02**
```
exec  = q8(mid * (1 + spread))
raw   = q * exec                                     # exact, NOT rounded
total = q2(raw * (1 + f))                            # R4: cash out
fee   = q2(raw * f)                                  # R3
notional = total - fee                               # derived, so total == notional + fee always reconciles
cash_delta = -total
```

**S1. Sell by quantity `q` — TRADE-02**
```
exec  = q8(mid * (1 - spread))
raw   = q * exec
proceeds = q2(raw * (1 - f))                         # R4: cash in
fee   = q2(raw * f)
notional = proceeds + fee                            # derived
cash_delta = +proceeds
```
Sells by `$` amount are NOT in v1 (TRADE-02 says sell by quantity only).

**Minimum order (D-04):** buy: `notional >= min_order`; sell: `notional >= min_order` unless `q == held` (exact Decimal equality under the lock). `notional` is the cents value above, so a typed `$1.00` buy passes (budget 1.00).

**Worked examples** (computed with Python Decimal in this session, `f = s = 0.0025`):

| Case | Inputs | exec | fee | qty / cash | Notes |
|------|--------|------|-----|------------|-------|
| BTC buy by $ | mid 100000.00, A = 100.00 | 100250.00000000 | 0.25 | budget 99.75, qty **0.00099501**, cash -100.00 | qty*exec = 99.74975250 <= 99.75; dust $0.000248 |
| DOGE buy by $ | mid 0.08, A = 10.00 | 0.08020000 | 0.02 | budget 9.98, qty **124.43890274**, cash -10.00 | qty*exec = 9.9799999997; dust 2.5e-10 |
| BTC buy by $ at minimum | mid 100000, A = 1.00 | 100250.00000000 | **0.00** | budget 1.00, qty 0.00000997, cash -1.00 | True fee $0.0025 rounds to $0.00 (cent granularity). Accepted artifact, see Open Questions Q3 |
| BTC buy by qty | mid 100000, q = 0.00015 | 100250.00000000 | 0.04 | raw 15.0375, total **15.08**, notional 15.04 | |
| DOGE buy by qty | mid 0.08, q = 125 | 0.08020000 | 0.03 | raw 10.025, total **10.05**, notional 10.02 | |
| BTC sell (whole position) | mid 100000, q = 0.00099501 | 99750.00000000 | 0.25 | raw 99.2522475, proceeds **+99.00**, notional 99.25 | Immediate round trip of the BTC buy: $100.00 -> $99.00 (spread + fees cost about 1%) |
| DOGE sell | mid 0.08, q = 124.43890274 | 0.07980000 | 0.02 | raw 9.93022444, proceeds **+9.91**, notional 9.93 | |

**Cash is stored in whole cents.** Every cash delta above is a 2-dp value and starting cash is `10000.00`, so `accounts.cash` always has at most 2 dp even though the column is `NUMERIC(20,8)`. Make that a DB invariant in the migration: `ALTER TABLE accounts ADD CONSTRAINT ck_accounts_cash_cents CHECK (cash = round(cash, 2))` (existing rows are all whole cents; the phase is not yet deployed with trades). Do not change the column type (a type change is a heavier migration for no gain).

**Overflow/validation bounds:** quantity: `Decimal(gt=0, max_digits=20, decimal_places=8)`; amount: `gt=0, decimal_places=2, max_digits=14`. Compute in Python before touching the DB; the funds/holding check happens before any `UPDATE`, so products larger than NUMERIC(20,8) are refused (`insufficient_*`), never overflow in Postgres. `mid` is bounded by `MAX_MID = 1e12` at ingest; `qty*exec` is exact in Decimal.

## Architecture Patterns

### System Architecture Diagram

```
Browser /trade/BTC
  |  debounced input (side, $|qty)
  v
POST /api/v1/trades/quote  (CurrentUser + CSRF)            read-only, no lock
  |-> load coin+price (join) -> age check (freshness == "fresh") -> plan_trade(cash, held) -> QuoteOut
  |   errors: 404 unknown_coin | 409 stale_price | 422 below_minimum | 422 insufficient_*
  v
User sees preview (mid, exec, fee, qty, cash change)  --- clicks Confirm
  |  generate idempotency_key (UUID) once per preview/attempt
  v
POST /api/v1/trades  {symbol, side, amount_usd|quantity, expected_mid, idempotency_key}
  |   BEGIN
  |   1. SELECT accounts WHERE user_id FOR UPDATE            <- serialises this user's trades
  |   2. SELECT trades WHERE (user_id, key)                   -> replay: same fingerprint -> 200 original fill
  |                                                              different fingerprint -> 409 idempotency_conflict
  |   3. load coin + price; age != fresh -> 409 stale_price
  |   4. mid != expected_mid -> 409 price_changed + fresh QuoteOut (nothing written)
  |   5. SELECT holdings (user, coin) FOR UPDATE; plan_trade -> 422 below_minimum / insufficient_*
  |   6. UPDATE accounts.cash; upsert/UPDATE holdings (qty, cost_basis); INSERT trades; COMMIT
  v
FillOut (201; replay 200 identical body) -> invalidate me/holdings/prices queries -> fill summary card
                                  ^
Scheduler container -> prices table (read-only for trades; no lock interaction)
```

### Recommended Project Structure
```
backend/app/
├── models/trade.py            # Holding, Trade (export in models/__init__.py)
├── schemas/trades.py          # TradeIn, QuoteIn, QuoteOut, FillOut, HoldingOut
├── services/trade_math.py     # PURE: plan_trade(), constants; 100% coverage
├── services/trading.py        # quote(), execute(); DB + locking; 100% coverage
├── api/v1/trades.py           # POST /trades/quote, POST /trades, GET /holdings/{symbol}
└── core/config.py             # + trade_spread, trade_fee, trade_min_order_usd
backend/alembic/versions/0006_trading.py
backend/tests/{test_trade_math.py, test_trading_service.py, test_trades_api.py, test_trading_concurrency.py}
frontend/src/{api/trades.ts, hooks/useQuote.ts, hooks/useTrade.ts, hooks/useHolding.ts, lib/money.ts(+formatQuantity), pages/TradePage.tsx}
frontend/e2e/trade.spec.ts
```

### Pattern 1: Shared planner (preview == fill)
`plan_trade(side, kind, value, mid, cash, held, settings) -> Plan | raises TradeRefused(code, message)`. Quote and execute both call it; the execute path calls it with the locked `cash` and `held`. Keep it a pure function returning a frozen dataclass (`quantity, exec_price, fee, notional, cash_delta, whole_position`). Refusals are a small exception class mapped to HTTP by the route (thin routes).

### Pattern 2: Execute under the account lock (sketch)
```python
# Source: SQLAlchemy 2.0 docs (Select.with_for_update); project patterns in services/accounts.py
async def execute(db, user_id, order, settings, now):
    account = (await db.execute(
        select(Account).where(Account.user_id == user_id).with_for_update()
    )).scalar_one()                                   # lock order: account FIRST, always
    existing = (await db.execute(
        select(Trade).where(Trade.user_id == user_id,
                            Trade.idempotency_key == order.idempotency_key)
    )).scalar_one_or_none()
    if existing is not None:                          # replay BEFORE any price check
        if fingerprint(existing) != order.fingerprint():
            raise TradeRefused("idempotency_conflict", ...)
        return fill_from_row(existing), True
    coin, price = await load_coin_price(db, order.symbol)   # raises unknown_coin
    require_fresh(price.as_of, now, settings)               # stale_price
    if price.mid != order.expected_mid:                     # Decimal equality, scale-insensitive
        raise PriceChanged(plan_for_quote(...))             # carries the fresh quote
    holding = (await db.execute(
        select(Holding).where(Holding.user_id == user_id, Holding.coin_id == coin.id)
        .with_for_update())).scalar_one_or_none()
    held = holding.quantity if holding else Decimal(0)
    plan = plan_trade(..., cash=account.cash, held=held)
    ...apply: account.cash += plan.cash_delta; holding upsert; db.add(Trade(...))
    await db.commit()   # CHECKs (cash>=0, qty>=0) and UNIQUE are the backstop
```
Because step 1 serialises every request of one user, the idempotency check-then-insert (step 2 then INSERT) has no race: two identical requests queue on the account lock, the second one finds the first's committed row. Keep `UNIQUE(user_id, idempotency_key)` as the hard backstop and map an `IntegrityError` on the trade insert to the same replay path anyway (one `except IntegrityError: rollback; re-run lookup`), because CLAUDE.md requires constraint-backed uniqueness; with the lock it is unreachable in practice, so cover it with a direct unit test that inserts a duplicate key. [CITED: CLAUDE.md "Uniqueness and races"]

Rollback on every refusal: raising before any write and not committing releases the lock when the session closes (`get_db` yields a session without auto-commit; the service commits only on success).

### Pattern 3: Holdings and cost basis
Track `cost_basis` (total USD paid for the currently held quantity, fees included) on `holdings`, updated in the same transaction. PORT-03 needs "average cost (fees included)" next phase; deriving it later by replaying trades is possible but must reproduce exact rounding and needs a data migration for existing rows.

- Buy: `cost_basis += total paid` (cents, exact: `-cash_delta`).
- Sell part: `removed = q2(cost_basis * q / held)` (HALF_EVEN, R5); `cost_basis -= removed`. Average cost per unit (`cost_basis / quantity`) is therefore unchanged by a sell, up to cent rounding.
- Sell whole (`q == held`): `cost_basis = 0` and quantity `0`.
- Keep a zero-quantity row (do not delete): keeps the holding row stable for later locking and avoids insert races; Phase 5 filters `quantity > 0`.

Adding R5 is the only extra rounding point. Store `cost_basis NUMERIC(20,8) NOT NULL DEFAULT 0 CHECK (cost_basis >= 0)`. Do NOT add `realized_pnl` to trades now (PORT-V2-02 is v2). This is the one "slightly ahead of need" item; see Open Questions Q2.

### Pattern 4: Stateless quote and price-changed
Quote and confirm take the same order fields. Confirm adds `expected_mid` (string from the last quote) and `idempotency_key`. Compare **mid only** (not `as_of`): the scheduler bumps `as_of` every 60 s even when the mid is identical, and an unchanged mid yields an identical fill, so failing on `as_of` alone would cause pointless re-confirms. The fill still records the `as_of` actually used. The 409 body for `price_changed` embeds the new quote (`detail.quote`), so the UI swaps the preview and asks the user to confirm again.

### Anti-Patterns to Avoid
- **Recomputing the preview on the client.** Display only; all numbers come from the server.
- **Idempotency check after the price checks.** A replay at a later time (price now stale/changed) must still return the original fill, so lookup comes first.
- **Locking the holding before the account**, or locking multiple accounts: only ever lock account -> holding. With one account per user and one lock order, no deadlock is possible.
- **`float`, `round()`, f-string numbers, `Decimal(float)`** anywhere in the diff.
- **Returning replay cash as "current cash"**: store `cash_after` on the trade so the replayed body is byte-identical.
- **Checking funds in SQL only**: check in Python first for a clear refusal message; the CHECK constraint is the backstop that makes an overspend impossible even if a bug slips through.

## Schema (migration 0006, schema only)

```
holdings
  id            bigint GENERATED ALWAYS AS IDENTITY PK
  user_id       bigint NOT NULL FK users(id)
  coin_id       bigint NOT NULL FK coins(id)
  quantity      numeric(20,8) NOT NULL CHECK (quantity >= 0)
  cost_basis    numeric(20,8) NOT NULL DEFAULT 0 CHECK (cost_basis >= 0)
  UNIQUE (user_id, coin_id)          -- also serves the (user, coin) lookup and Phase 5 "all holdings of a user"

trades
  id               bigint GENERATED ALWAYS AS IDENTITY PK
  user_id          bigint NOT NULL FK users(id)
  coin_id          bigint NOT NULL FK coins(id)
  side             text NOT NULL CHECK (side IN ('buy','sell'))
  input_kind       text NOT NULL CHECK (input_kind IN ('usd','quantity'))   -- idempotency fingerprint
  input_value      numeric(20,8) NOT NULL CHECK (input_value > 0)           -- idempotency fingerprint
  quantity         numeric(20,8) NOT NULL CHECK (quantity > 0)
  mid_price        numeric(20,8) NOT NULL CHECK (mid_price > 0)
  price_as_of      timestamptz  NOT NULL
  exec_price       numeric(20,8) NOT NULL CHECK (exec_price > 0)
  fee              numeric(20,8) NOT NULL CHECK (fee >= 0)
  cash_delta       numeric(20,8) NOT NULL         -- signed: negative for buys, >= 0 for sells
  cash_after       numeric(20,8) NOT NULL CHECK (cash_after >= 0)
  idempotency_key  uuid NOT NULL
  created_at       timestamptz NOT NULL DEFAULT now()
  UNIQUE (user_id, idempotency_key)
  CHECK ((side = 'buy' AND cash_delta < 0) OR (side = 'sell' AND cash_delta >= 0))
accounts: ADD CONSTRAINT ck_accounts_cash_cents CHECK (cash = round(cash, 2))
```
- Notional is derivable (`-cash_delta - fee` for buys, `cash_delta + fee` for sells), so it is not stored. Average cost incl. fees derives from `holdings.cost_basis`.
- **Indexes:** the UNIQUE index covers the only query this phase runs on `trades` (idempotency lookup) and is prefixed by `user_id` (covers the FK). Do NOT add `(user_id, created_at, id)` now: history is Phase 5; adding it then is a `CREATE INDEX CONCURRENTLY` on a tiny table. No index on `coin_id` (no query filters by it alone). [CITED: CLAUDE.md "add them for queries that exist"]
- Follow the existing naming convention (`NAMING_CONVENTION` in `db/base.py`), add `__table_args__` CheckConstraints with short names like `Account`, review the autogenerated migration by hand (CHECKs and server defaults are missed by autogenerate), write a real `downgrade()` (drop trades, holdings, then the accounts constraint). Extend `tests/test_migrations.py` if it checks head/downgrade.
- Trade rows are append-only. Postgres identity `always` is fine.

## API Design

All routes under `/api/v1`, `tags=["trades"]`, `CurrentUserDep`; POSTs also `CsrfDep` (add `dependencies=[Depends(verify_csrf)]` as `auth.py` does). Responses carry `Cache-Control: no-store`. Money as Decimal -> JSON strings.

| Route | Purpose | Success | Errors |
|-------|---------|---------|--------|
| `POST /trades/quote` | Preview, read-only, no lock | 200 `QuoteOut` | 401, 403 csrf, 404 `unknown_coin`, 409 `stale_price`, 422 `below_minimum`, 422 `insufficient_cash`, 422 `insufficient_quantity`, 422 validation |
| `POST /trades` | Execute | 201 `FillOut` (replay: 200, identical body) | same as quote plus 409 `price_changed` (detail.quote) and 409 `idempotency_conflict` |
| `GET /holdings/{symbol}` | Quantity held for the trade page (0 if none) | 200 `{symbol, quantity}` | 404 `unknown_coin` |

Request body: `{symbol, side: "buy"|"sell", amount_usd?: "100.00", quantity?: "0.00015"}`; exactly one of the two (model_validator); `amount_usd` only with `buy`. Confirm adds `expected_mid`, `idempotency_key` (UUID). Error bodies use the existing `detail: {code, message}` shape (`toApiError` already parses it); `price_changed` adds `detail.quote`. Symbols: upper-case before lookup.

`QuoteOut`: `symbol, side, input_kind, input_value, mid, as_of, age_seconds, exec_price, quantity, notional, fee, cash_delta, cash_before, cash_after, held_before, whole_position`. `FillOut`: same fields plus `trade_id, created_at` (built from the persisted row, so the replay body is identical). Use one schema with optional extras if simpler.

Refusal message copy (clear and specific): stale_price "The price for BTC is {n}s old. Trading is paused until it refreshes."; below_minimum "The minimum order is $1.00."; insufficient_cash "You have $X.XX; this order needs $Y.YY."; insufficient_quantity "You hold X BTC."; price_changed "The price moved. Review the new total and confirm again."

Rate limits: skip in v1 (authenticated friends-only app; `/api` is not behind a limit zone, only `/auth`). Document in Open Questions Q4.

## Frontend

- Route `trade/:symbol` inside `SignedIn` in `App.tsx`. Redirect to `/` when prices have loaded and the symbol is not in the list, and on backend 404.
- Markets: add a 4th column "Trade" with a `Link` per row (keep the table `aria-label="Markets"`; e2e finds the Price column by header text, so adding a column is safe). Update `MarketsPage.test.tsx`.
- `api/trades.ts`: `quote()`, `execute()`, `fetchHolding()` through `apiFetch` (the only `fetch` for /api).
- **`client.ts` change:** `ApiError` must carry the parsed `detail` (new field, e.g. `details: unknown`) so the page can read `detail.quote` on `price_changed`. Update `client.test.ts`.
- Quote: `useQuery` (POST is read-only) keyed `["quote", symbol, side, kind, value]`, enabled only when the input matches `^\d+(\.\d{1,2})?$` (USD) or `^\d+(\.\d{1,8})?$` (quantity) and is non-zero; 300 ms debounce; `placeholderData: keepPreviousData`; `retry: false`; `refetchInterval: 30_000` so the preview tracks the scheduler. Never `parseFloat` a money string.
- Confirm: `useMutation`. Idempotency key held in a `useRef`, created lazily on first Confirm click of a preview and **reused** for retries of that same attempt (network error/unknown outcome); reset when the input, side, or displayed quote changes, or after any terminal result. Button `disabled` while `isPending` (UX only; the server is the protection).
- States: `price_changed` -> `queryClient.setQueryData(quoteKey, detail.quote)` and show an inline notice "Price moved, review and confirm again" (no auto-retry). `stale_price`/`below_minimum`/`insufficient_*` -> inline `role="alert"` message, Confirm disabled. Success -> preview card becomes the fill summary (quantity, exec price, fee, cash change, new cash); `invalidateQueries` for `["me"]`, `["holding", symbol]`, `["prices"]`. Per MASTER.md: Buy/Sell is a neutral segmented control (no green/red buttons), fill summary as a toast/summary, skeletons not spinners, 7/5 column cards.
- Sell side shows "You hold X SYM" with the full 8-dp quantity so the user can type their whole position; a "Sell all" button is TRADE-V2-01 (v2, do not build). Buy side offers an Amount ($) / Quantity switch; sell is quantity only.
- Formatting: add `formatQuantity(value)` to `lib/money.ts` (up to 8 dp, trailing zeros trimmed, string-safe like `formatUsd`); fees/cash via `formatUsd`; exec price via `formatUnitPrice`. Add tests.

## Concurrency Test Design (criterion 5)

File `tests/test_trading_concurrency.py`, real test-stack Postgres, no mocks:
1. Sign in a new user (existing `sign_in` helper), set cash with an engine-level `UPDATE accounts SET cash = 1000.00 ...`, insert a fresh `Price` row for BTC (`as_of = now`, via `upsert_prices` or direct insert; use the `clean_prices` fixture and clean up trades/holdings after).
2. Fire `N = 25` identical buys of `$100.00` with 25 different idempotency keys using `asyncio.gather` on the shared `auth_client` (each request gets its own session/connection from the pool; default pool 5 + 10 overflow, so use N <= 15 per gather or raise nothing: run 2 gathers of 12, or set `N = 15`). Expected: exactly 10 return 201, the rest 422 `insufficient_cash`; final cash `0.00`; `count(trades) == 10`; `holdings.quantity == sum(trades.quantity)`; `cash == 1000 - sum(100)`.
3. Same-key test: 10 concurrent requests with the SAME key -> exactly one `trades` row, all responses identical bodies (one 201, nine 200).
4. Sell oversell: hold Q, fire parallel sells of Q/2 + epsilon-sized so only floor succeed; assert holding never negative.
5. Backstop test: a direct SQL `UPDATE accounts SET cash = -1` raises `IntegrityError` (proves the CHECK exists independent of app code), and a duplicate `(user_id, key)` insert raises.
6. Confirm the test can fail: temporarily removing `with_for_update()` should make test 2 produce > 10 successes or a CHECK violation (mention in the plan as a manual mutation check).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Overspend prevention | Application-only balance check | Account `FOR UPDATE` + `CHECK (cash >= 0)` | Survives multiple workers and bugs |
| Idempotency | In-memory/Redis dedupe | `UNIQUE (user_id, idempotency_key)` in Postgres | Redis can be lost (CLAUDE.md: Postgres is truth) |
| Decimal serialisation | Custom JSON encoders | Pydantic `Decimal` -> string | Already how `MeOut` works |
| Freshness | A second max-age constant | `prices.freshness(age, price_fresh_seconds, price_stale_seconds) == "fresh"` and `age_seconds()` | D-03: one definition |
| CSRF / auth | New checks | `CsrfDep`, `CurrentUserDep` | Existing and 100%-covered |
| Property testing | Hypothesis dependency | Seeded `random.Random` pytest loops | No new package |

## Runtime State Inventory

Not a rename/refactor phase. Omitted. (Greenfield tables only; no existing data migrated.)

## Common Pitfalls

### Pitfall 1: Cash change differs from the typed amount by a cent
**What goes wrong:** Recomputing `notional + fee` after rounding each part gives `A +/- 0.01`.
**How to avoid:** In B1 `cash_delta = -A` by construction; fee is derived first and notional is `A - fee`. Test invariant over thousands of random `(mid, A)` pairs: `cash_delta == -A`, `qty*exec <= A - fee`, `fee >= 0`.

### Pitfall 2: Rounding quantity to nearest overspends
**How to avoid:** R2 is `ROUND_DOWN`; the property test asserts `qty * exec <= budget`.

### Pitfall 3: Whole-position sell leaves dust or is refused by the minimum
**How to avoid:** Compare the typed `Decimal` with the locked stored quantity for exact equality (no float, no rounding of a displayed value); show the full 8-dp holding in the UI. Property test: selling exactly `held` always succeeds, even when notional < $1; a sell of `held - 1e-8` below $1 is refused.

### Pitfall 4: Replay returns an error because the price is now stale/changed
**How to avoid:** Idempotency lookup precedes price checks (lock -> lookup -> price).

### Pitfall 5: Replayed body differs from the original
**How to avoid:** Build both responses from the persisted row (`cash_after` stored); compare in a test with `==` on the JSON.

### Pitfall 6: Session not committed / lock held
`get_db` yields a plain session with no auto-commit. Service must `await db.commit()` on success only; on refusal let the session close (rollback). Idle-in-transaction timeout is a backstop.

### Pitfall 7: Pool exhaustion in the concurrency test
Default asyncpg pool is 5 + 10 overflow; N=25 simultaneous requests queue on the pool and on the row lock, which is fine for correctness but each holds a connection while waiting for the lock. Keep `N <= 15` per gather or the test slows/times out.

### Pitfall 8: Fake price moves between quote and confirm in e2e
`PRICE_SOURCE=fake` changes the mid each minute boundary; an e2e confirm can legitimately hit `price_changed`. The e2e must handle it (if the "Price moved" notice appears, click Confirm again) rather than assume a single click.

### Pitfall 9: Unknown/inactive coin
Treat `is_active = false` or missing price row as `unknown_coin`/`stale_price` (no price ever -> `stale_price` "No price yet"). Selling a disabled coin's holdings is a known edge (PITFALLS.md) with no case today (all 15 active); note it, do not build it.

## Code Examples

### Pure planner skeleton
```python
# Source: derived from CLAUDE.md "Money and numbers"; verified numerically in this session
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext

Q8, Q2 = Decimal("1e-8"), Decimal("0.01")

def q8(x: Decimal) -> Decimal: return x.quantize(Q8, rounding=ROUND_HALF_EVEN)
def q2(x: Decimal) -> Decimal: return x.quantize(Q2, rounding=ROUND_HALF_EVEN)

def buy_by_usd(mid, amount, spread, fee_rate):
    with localcontext() as ctx:
        ctx.prec = 50
        exec_price = q8(mid * (1 + spread))
        fee = q2(amount * fee_rate / (1 + fee_rate))
        budget = amount - fee
        qty = (budget / exec_price).quantize(Q8, rounding=ROUND_DOWN)
    return exec_price, fee, budget, qty, -amount
```

### Pydantic request (exactly one of amount/quantity)
```python
class QuoteIn(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    amount_usd: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=8)

    @model_validator(mode="after")
    def _one_input(self) -> Self:
        if (self.amount_usd is None) == (self.quantity is None):
            raise ValueError("send exactly one of amount_usd or quantity")
        if self.amount_usd is not None and self.side == "sell":
            raise ValueError("sell is by quantity only")
        return self
```

## State of the Art

| Old | Current | Impact |
|-----|---------|--------|
| Stored quote with TTL | Stateless preview + `expected` price on confirm | Fewer moving parts; server stays authority |
| Check-then-insert idempotency | Row lock + UNIQUE backstop | Race-free and constraint-backed |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pydantic v2 `Decimal` fields reject NaN/Infinity (and `gt=0` rejects them regardless) | API / code example | Low; `gt=0` already guards, add a test with `"NaN"` and `"Infinity"` |
| A2 | Decimal context `prec=28` would suffice; pinning to 50 is harmless | Money math | None |
| A3 | Default SQLAlchemy async pool (5 + 10 overflow) applies to the app engine (`main.py` sets only `pool_pre_ping` in the snippet seen) | Concurrency test | Test N may need tuning |
| A4 | `FOR UPDATE` on the account row plus READ COMMITTED gives the required serialisation (a waiting transaction re-reads the updated row after the lock is released) | Locking | Low; this is standard Postgres behaviour, and the concurrency test proves it on the real stack |

## Open Questions (RESOLVED)

1. **Cent-granular fee on tiny trades.** A $1.00 buy shows fee $0.00 (true $0.0025). Options: accept (HALF_EVEN per CLAUDE.md), or raise the practical floor. Recommendation: accept; it is an artifact only below about $2. RESOLVED: D-06, the user chose a **minimum fee of $0.01**. Sell fees are capped at the notional so proceeds are never negative. Worked examples must be re-derived.
2. **Track `cost_basis` on holdings now?** Recommended yes (3 lines of logic in the same transaction, avoids a data migration and replay in Phase 5, supports PORT-03 exactly). If the planner/user wants strictly minimal Phase 4, drop the column and let Phase 5 add it with a replay migration. `realized_pnl` on trades stays out (PORT-V2-02). RESOLVED: D-07, track `cost_basis` now.
3. **Compare `expected_mid` only vs mid+as_of.** Recommended mid only (above). Confirm that is the desired reading of TRADE-05 "price changed". RESOLVED: mid only (CONTEXT accepted defaults).
4. **Rate limiting `/trades*`.** Recommended none in v1 (friends-only, authenticated). If wanted, add `rl_trade_limit/window` using `ratelimit.enforce` keyed `sim:rl:trade:<user_id>`. Trivial to add later. RESOLVED: no rate limiting in v1.
5. **Status codes.** Chosen: 409 for stale/changed/idempotency conflict, 422 for business refusals, 404 unknown coin. The frontend dispatches on `detail.code`, so the planner may adjust the numbers without UI impact. RESOLVED: as chosen; the UI dispatches on `detail.code`.

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| Test stack (Postgres 18, Redis 8 via `docker-compose.test.yml`) | backend tests, concurrency test | Provided by repo (not started in this research session) | `docker compose -f docker-compose.test.yml up -d --wait` |
| uv / Node 24 | tests, frontend | Per memory: linked in /usr/local/bin | — |
| Full compose stack with `PRICE_SOURCE=fake` | e2e | CI sets it (ci.yml) | Never use `resend` backend for e2e |

No missing blocking dependencies. No new external services.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend | pytest + pytest-asyncio + httpx against the isolated test stack |
| Frontend | Vitest + React Testing Library; Playwright e2e |
| Quick run | `cd backend && uv run pytest tests/test_trade_math.py tests/test_trading_service.py tests/test_trades_api.py -x` |
| Full suite | `cd backend && uv run pytest --cov=app --cov-fail-under=80`; `cd frontend && npm run test -- --coverage`; `npx playwright test` |

### Phase Requirements -> Test Map
| Req | Behavior | Type | Command / File | Exists |
|-----|----------|------|----------------|--------|
| TRADE-01 | Buy by $: `cash_delta == -A`, `qty*exec <= A-fee`, seeded random invariants (>= 5,000 cases) + worked examples above | unit | `tests/test_trade_math.py` | Wave 0 |
| TRADE-02 | Qty buy/sell worked examples; > 8 dp / <= 0 / NaN / both-inputs / sell-by-$ rejected | unit + API | `test_trade_math.py`, `test_trades_api.py` | Wave 0 |
| TRADE-03 | Quote returns all preview fields; read-only (no rows written) | API | `test_trades_api.py` | Wave 0 |
| TRADE-04 | Spread/fee from settings; exec price recorded | unit + service | `test_trade_math.py`, `test_trading_service.py` | Wave 0 |
| TRADE-05 | Stale (>=120 s) -> 409 `stale_price`, no row; mid moved -> 409 `price_changed` with new quote, no row; same mid with new as_of executes | service + API | `test_trading_service.py` | Wave 0 |
| TRADE-06 | insufficient cash/qty; below $1.00; whole-position sell below $1.00 allowed; `held - 1e-8` refused | service + API | same | Wave 0 |
| TRADE-07 | Replay returns identical body, one row; same key different payload -> 409; replay allowed after price went stale; duplicate-key IntegrityError path | service + API + concurrency | `test_trading_concurrency.py` | Wave 0 |
| TRADE-08 | Fill has qty, price, fee, `cash_after` equal to `/me` cash afterwards | API | `test_trades_api.py` | Wave 0 |
| SC5 | N parallel buys: exactly floor(cash/cost) succeed, cash never < 0 | concurrency (real PG) | `test_trading_concurrency.py` | Wave 0 |
| Auth | 401 signed out, 403 without CSRF on both POSTs, GET holdings 401 | API | `test_trades_api.py` | Wave 0 |
| Schema | CHECKs/UNIQUE exist; migration up/down | migration | `test_migrations.py` (extend) | exists, extend |
| UI | TradePage states (loading, preview, price_changed, refused, success), key reuse on retry and reset on edit, double-click sends once, Markets link | Vitest | `TradePage.test.tsx`, `MarketsPage.test.tsx`, `client.test.ts`, `money.test.ts` | Wave 0 |
| E2E | Sign in -> Markets -> Trade BTC -> buy $100 -> fill, cash $9,900.00 -> sell all -> cash within expected loss; tolerate `price_changed` by re-confirming | Playwright | `frontend/e2e/trade.spec.ts` | Wave 0 |

### Sampling Rate
- Per task commit: quick run command above (plus the relevant Vitest file).
- Per wave merge: full backend suite with coverage and the critical-path gate.
- Phase gate: full backend + frontend + e2e green before `/gsd:verify-work`.

### Critical-path coverage (100%) — additions
Add `app/services/trade_math.py` and `app/services/trading.py` to the `--include` list in **both** `.github/workflows/ci.yml` and the CLAUDE.md "Common commands" block (they must match). Also add `app/api/v1/trades.py` only if desired; the route is thin, so API tests plus the 80% gate suffice.

### Wave 0 Gaps
- [ ] `backend/tests/test_trade_math.py`, `test_trading_service.py`, `test_trades_api.py`, `test_trading_concurrency.py`
- [ ] A test helper to set cash, insert a fresh `Price`, and clean `trades`/`holdings` (in `tests/helpers.py` or conftest fixture like `clean_prices`; trades/holdings reference users so clean by deleting rows created by the test user)
- [ ] `frontend/src/pages/TradePage.test.tsx`, `frontend/e2e/trade.spec.ts`
- [ ] Framework install: none

## Security Domain

| ASVS Category | Applies | Control |
|---------------|---------|---------|
| V2 Authentication | inherited | Existing session cookie; endpoints behind `CurrentUserDep` |
| V3 Session | inherited | Existing |
| V4 Access Control | yes | Every query filters by `current_user.id`; user id never taken from the request body (no IDOR) |
| V5 Input Validation | yes | Pydantic: `Decimal` bounds, `decimal_places`, symbol allow-list via DB lookup, UUID type for the key, exactly-one-input rule |
| V6 Cryptography | no | Nothing new (idempotency key is not a secret) |
| V13 API / CSRF | yes | `CsrfDep` on both POSTs |

| Threat | STRIDE | Mitigation |
|--------|--------|------------|
| Double-spend via parallel requests | Tampering | Account `FOR UPDATE` + `CHECK (cash >= 0)` |
| Replay / double submit | Tampering | `UNIQUE (user_id, idempotency_key)` + payload fingerprint |
| Client-chosen price | Tampering | Price only from `prices` table; `expected_mid` can only cause a refusal, never set a fill price |
| Trading on stale/spiked price | Tampering | 120 s check under lock; ingest spike rules already in Phase 3 |
| Reusing another user's key | Info disclosure | Key scoped by `user_id` in the UNIQUE and in every lookup |
| Log leakage | Info disclosure | Do not log request bodies; log trade id and user id only |

## Production

No new services, ports or env vars required (new settings have defaults). Migration `0006` runs via the existing deploy path (backend start applies migrations). Smoke additions in `deploy/smoke-prod.sh` (mirror `prices_requires_auth`): `POST /api/v1/trades/quote` signed out is 401 (CSRF failure may precede it; use the same approach as existing checks, e.g. send no CSRF and accept 401 or 403, or check `GET /api/v1/holdings/BTC` is 401, which is simpler and unambiguous). Update the smoke tests under `deploy/tests` if the script has a test harness. Whether to cut a release is decided at the push gate.

## Sources

### Primary (HIGH confidence)
- Codebase (read this session): `backend/app/models/{user,price,auth}.py`, `services/{accounts,prices,ratelimit,fake_prices,price_rules}.py`, `core/{deps,config}.py`, `api/v1/{prices,me,auth,router}.py`, `schemas/*`, `alembic/versions/0004`, `tests/{conftest,helpers}.py`, `frontend/src/{App.tsx,api/client.ts,lib/money.ts,pages/MarketsPage.tsx,hooks/usePrices.ts}`, `frontend/e2e/*`, `deploy/smoke-prod.sh`, `.github/workflows/ci.yml`
- `./CLAUDE.md`, `.planning/REQUIREMENTS.md`, `.planning/PROJECT.md`, `.planning/research/PITFALLS.md` (pitfalls 2, 3, 4), `design-system/birja/MASTER.md`
- Worked examples: Python 3 `decimal` computation run in this session

### Secondary (MEDIUM)
- Postgres/SQLAlchemy behaviour of `SELECT ... FOR UPDATE` under READ COMMITTED (standard, from training knowledge; proven on the real stack by the concurrency test) [ASSUMED, see A4]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, nothing new
- Architecture / locking / idempotency: HIGH, standard pattern, matches PITFALLS.md pitfall 3
- Money math: HIGH for the scheme (numerically checked); MEDIUM for product choices flagged in Open Questions (Q1, Q2, Q3)
- Pitfalls: HIGH

**Research date:** 2026-10-28
**Valid until:** 30 days (stable domain; the codebase is the moving part)
