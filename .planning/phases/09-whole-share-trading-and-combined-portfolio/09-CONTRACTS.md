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
