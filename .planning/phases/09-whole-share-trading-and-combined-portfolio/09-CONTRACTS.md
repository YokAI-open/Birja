# Phase 9 contracts

Frozen by Plan09-01 for downstream plans. These are local feature interfaces,
not permission to activate data or trade in production. Phase7/8 live deferrals
remain. Source of truth for concrete fields: `app/schemas/stock_trades.py` and
`app/services/stock_trading_rules.py`. No package or provider entitlement inferred.

## API and immutable receipt

All routes require existing authenticated current user; POST also requires CSRF.
No request accepts user_id, amount_usd, authority or client balance. Private
responses use Cache-Control: no-store. Unknown response shapes/codes fail closed.

| Endpoint | Input | Output / status | Consumer |
|---|---|---|---|
| POST /api/v1/stock-trades/quote | QuoteIn: symbol, side, quantity | 200 QuoteOut | Stock ticket preview |
| POST /api/v1/stock-trades | TradeIn: QuoteIn + UUID idempotency_key + expected_exec_price | 201 FillOut new / 200 FillOut replay | Confirm / Check order result |
| GET /api/v1/stock-trades/{symbol}/context | symbol path, current user | 200 ContextOut | Draft, bid/ask, cash and shortcuts |

Quantity is a JSON string matching `[1-9][0-9]{0,11}`, at most999999999999.
Expected price is a plain positive finite decimal string NUMERIC(20,8), no
exponents, signs, whitespace or leading zeroes except0.xxx. JSON numbers and
booleans are rejected. Crypto schemas/math are unchanged. Expected price is
confirmation evidence, excluded from economic payload identity. Economic replay
identity is user + stable instrument + side + quantity; key uniqueness is global
across stock and crypto endpoints. Replay original saved receipt before checking
current quote/session/permission/action, even after close/split/rename. Changed
economic input conflicts. A pre0013 stock row without full facts is
receipt_unavailable; never reconstruct it from current holdings/catalogue.

QuoteOut carries immutable stable string coin_id/provider_asset_id, saved
symbol/company/exchange, side/quantity, bid/ask/exact_mid/exec_price, alpaca/iex,
event_at/collected_at/observed_at/age_seconds, notional/zero fee/cash delta,
cash before-after/held before-after, source session/bounds, AuthorityIdentity
and strict valid_until. Midpoint preserves ninth decimal (NUMERIC21,9).
Money is Decimal internally and plain strings on wire; bigint IDs are strings.
AuthorityIdentity binds exact evaluated admission product/generation/SHA256 hash
and deadlines plus calendar_generation, safety_epoch, unit_epoch,
status_admission_generation, continuity_generation and status_sequence.

FillOut version1 saves the same economic/source facts with string trade_id and
executed_at, historical cash_after and held_after. It has no top-level renewed
execution deadline. Its nested historical admission deadlines are evidence of
what authorized that fill, never current eligibility. Receipt survives later
trades/splits/catalogue renames; no current holding lookup can alter it.

ContextOut carries permitted identity, own cash/whole held_quantity and
server-calculated buy_max_quantity, nullable QuoteFacts, independent SessionFacts,
StatusFacts, ActionFacts, nullable authority and conservative valid_until.
It defaults execution_enabled=false. No number in context authorizes a fill.
Buy max is bounded floor(cash/ask), not cent-rounding optimization; both quantity
shortcuts only populate a draft and require preview then confirmation.

| HTTP | Domain code / shape |
|---|---|
| 409 | price_changed: PriceChangedOut with previous_exec_price, previous_cash_delta, exec_price_change, cash_delta_change, replacement quote |
| 409 | idempotency_conflict |
| 409 | permission_unavailable, action_unavailable, units_changed, halted, frozen, status_unavailable, session_unavailable, market_closed, quote_unavailable, quote_stale, receipt_unavailable |
| 422 | invalid_quantity, insufficient_cash, insufficient_holding, numeric_range; request parser validation uses existing FastAPI validation detail |
| 401 / 403 | existing unauthenticated / CSRF or authorization contracts |

Price change uses relevant ask for buy/bid for sell, with renewed explicit
confirmation. UNKNOWN transport/malformed success retains frozen payload/key;
closed/hold state must not block Check order result. No queued or auto-filled
draft. Unknown codes never mean success or guaranteed no-fill.

## Pure authority contracts

Frozen dataclasses in `services/stock_trading_rules.py` are the service seam.
`AdmissionEvidence(product,generation,row_hash,valid_from,valid_until,approved)`
represents a semantically validated current admission, never raw caller JSON.
Exactly one each of reference/quotes/actions/status/calendar is required.
SHA256 identifies the full evaluated persisted row, not just its generation.
Freeze its SQL encoding as `encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),
'hex')` for the whole `stock_data_admissions a` row. Services retain that DB hash
alongside semantic evaluation; final SQL recomputes it. Do not recreate PostgreSQL
JSONB text formatting using a different Python/JavaScript JSON serializer.

`StatusEvidence` binds coin_id/provider_asset_id, normal|halted|frozen|unknown,
event_at/observed_at/session_date, admission_generation, continuity_generation,
sequence, valid_until, bootstrap_verified, continuity_current, source/source_ref.
Defaults deny; normal requires both bootstrap and continuity. The verified
lease is at most60s from observed_at, with strict equality expiry. Status event
age is independent of quote120s age: an unchanged old normal event requires
current independently verified contiguous transport. Heartbeats, quote updates,
HTTP200 or scheduler success never renew it.

`lose_status_continuity(status)` increments continuity_generation, sets unknown,
clears bootstrap/continuity/deadline; saturation raises instead of wrapping.
Reconnect/loss must invalidate first. `renew_status_continuity(status,observed_at,
*,trusted_contiguous=False,sequence)` renews only an unexpired verified baseline
on an explicit trusted contiguous transport frame at exactly next sequence.
Failure invalidates; new bootstrap requires separate verified baseline evidence.
No synthetic fixture/helper grants live access or bootstrap completeness.

`QuoteEvidence` binds stable identity, bid/ask, event_at/collected_at/session_date,
admission_generation/unit_epoch and source/feed. `ExecutionEvidence` binds stable
identity, all admissions, action_current/action_valid_until/next_blocking_at,
safety_epoch/unit_epoch, independent status, session_state/date/opens_at/closes_at/
session_valid_until/calendar_generation and quote.

`evaluate_execution(evidence,now) -> ExecutionDecision(allowed,reason,evaluated_at,
valid_until,evidence)` is pure, priority permission → action/units → status →
session → quote. Only allowed decisions retain exact immutable evidence.
Session opens inclusive; close and all authority deadlines exclusive. Quote must
match identity/generation/units/current regular session and source age<120s after
all waits; no future event/collection. Bid/ask finite positive NUMERIC20,8,
bid<=ask. Allowed deadline is the minimum of all admitted/monitor/status/calendar/
session/quote/boundary deadlines. Replay does not require this decision.

`ValuationEvidence(execution,retained_until,historical_admission_until)` and
`evaluate_valuation(evidence,now) -> ValuationDecision(mode,reason,mid,event_at,
valid_until)` select fresh|closed|halted|unavailable. Fresh respects execution
expiry. Closed and verified-halt marks can exceed120s but carry original dates
and distinct retention/admission/action/unit/status continuity deadlines.
Unknown/frozen has no fallback; uncertain actions/unit mismatch suppress even
recent values. Exact midpoint `(bid+ask)/2` preserves ninth fractional place.

## Portfolio consumer fields

Plan09-09 extends `get_portfolio(db,*,user_id,settings,now=...) -> PortfolioSnapshot`
and `calculate_portfolio(...) -> PortfolioValue`; preserve their existing required
arguments and scalar single-statement snapshot, no sequential cash/holdings reads.

| Projection | Additive fixed wire fields |
|---|---|
| PortfolioOut | known_value: Money; unvalued_holding_count: nonnegative int; class_values: {cash: Money, stocks: Money or null, crypto: Money or null}; class_allocation_percent: same keys, each Money or null |
| HoldingOut | asset_class: crypto or stock; coin_id: string bigint; provider_asset_id: string or null; average_cost: Money or null if unsafe; existing quantity/basis/value/P&L/allocations retained |
| Stock mark facts | mark_mode: fresh/closed/halted/unavailable; source/feed; original event_at/collected_at; historical_admission_until/retained_until/valid_until; authority identity with admission/calendar/safety/unit/status epochs; fixed valuation_reason |

Each class_value is null if any held member is unvalued. known_value is cash
plus only known holdings; unknown count explicit, missing never zero. Incomplete
means null total_value/total_pl/total_pl_percent/cash_allocation_percent, ALL
holding allocations and ALL class allocations. Known individual values/P&L remain
visible unless unsafe units prevent them. Complete zero denominator also has null
percentages. Cash/Stocks/Crypto bars never normalize a known subtotal. Stable
order symbol then coin_id; original starting_cash baseline. Future dividends
count once from Account.cash, never again from entitlement rows. Browser purges
marks/cache at conservative deadlines and prevents older authority restoration.

## Selected0013 schema and final guard

Plan09-03 owns `0013_stock_execution.py` over0012 and `models/stock_execution.py`:

- `public.stock_fill_facts`: trade_id PK, composite FK(trade_id,coin_id,user_id)
  to Trade and coin_id FK to stock_instruments; immutable identity/source/receipt
  facts, exact NUMERIC21,9 midpoint, held_after, schema_version1 and bounded8192-byte
  JSONB authority. Trade retains historical cash_after and global user/key.
- `public.stock_status_evidence`: coin_id key plus frozen StatusEvidence fields,
  scheduler-only writes; bounded source/reference, safe generations/sequence,
  UTC timestamps and lease<=60s checks.
- `public.check_stock_fill_integrity()`: SECURITY INVOKER, fixed
  search_path=pg_catalog,public, schema-qualified static SQL. Deferred cross-row
  triggers on trades/stock_fill_facts/stock_ownership_movements require complete
  same-user/instrument once-only fill/movement, signed quantity/derived basis and
  saved held_after. No crypto facts/orphan causes/nonzero stock fee. Facts and
  movements append-only even under ordinary privileged DML.
- `public.assert_stock_execution_current(bigint,bigint,jsonb)`: trade_id,user_id,
  expected evaluated authority; SECURITY INVOKER, fixed search_path, PUBLIC
  revoked, app-only EXECUTE. JSON uses ExecutionEvidence field names above and
  exact admission row hashes/generations, quote identity/sides/times/session/unit,
  status identity/continuity/sequence/deadline, action epochs and session bounds.
  It compares caller snapshot to independently read current committed rows.

Execution: instrument gate → shared account → deterministic instrument holdings
→ staged Trade/facts/movement/cash → flush → SET CONSTRAINTS ALL IMMEDIATE → final
guard → commit, no later business await. Final SQL statement snapshot linearizes
validity after all writes/constraints using advancing clock after internal waits.
External changes after that statement snapshot cannot be predicted. Refusal rolls
back every effect. App may SELECT/INSERT facts, SELECT status, execute guard;
scheduler writes status without expanded financial access. No new role,
SECURITY DEFINER or membership. Plan09-04 exact recovery/grants/verified-TLS
fresh/populated proof precedes runtime consumers. No package/entitlement inferred.
