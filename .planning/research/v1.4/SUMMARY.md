# v1.4 research — Searchable Stock Trading

## Pricing and market data

Birja's live Alpaca REST rehearsal accepted all 20 IEX quotes in one batch.
An isolated scheduler cycle persisted and displayed 19 of 20 quotes. The
status stream acknowledged 20 subscriptions without providing an initial
status. The scheduler therefore has no live path to establish the status that
the current trade rule requires. [November 24 verification](../../quick/20261124-stock-activation/SUMMARY.md)

Use Alpaca's batched latest quotes as the first pricing candidate. Its Basic
plan documents IEX coverage and a 30-symbol WebSocket limit. REST requests for
selected and held symbols avoid that streaming limit. Test the effective
request quotas and data freshness using response headers and representative
stocks. A symbol listed in a directory can have sparse or missing IEX quotes.
Keep prices with their source timestamps, including the last permitted price
while closed. A closed-session price serves display only. Confirm applicable
use for the broadened catalog, marks, fill receipts and retained data before
production activation. [Alpaca plan](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api) ·
[Latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1)

Massive Basic documents end-of-day data and five requests per minute for
individual use. Twelve Data's free tier documents eight credits per minute and
800 per day, with external display treated separately in its business plans.
These tiers are weak substitutes for the approved fresh-price, shared-app flow.
Retain a provider decision in Phase 18 with measured coverage, operational
limits, applicable use, price freshness and effort. [Massive plans](https://massive.com/pricing) ·
[Twelve Data plans](https://twelvedata.com/pricing-business)

## Search and identity

The November 24 exchange directory sample contained 4,304 Nasdaq and 2,797
NYSE non-test, non-ETF entries. These counts include securities other than
common stock. Validate security type with supporting metadata. Nasdaq's files
include issuer/security names, exchange codes, test flags, ETF flags, multiple
symbol formats and a creation timestamp. SEC metadata can help with names and
issuer identity. Alpaca's Assets endpoint can help with provider identity and
coverage. The provider's `tradable` field refers to its brokerage and does not
establish that a stock is currently free of halts. [Directory fields](https://m.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs) ·
[SEC data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) ·
[Alpaca Assets](https://docs.alpaca.markets/us/docs/working-with-assets)

Search a refreshed local directory by case-insensitive company name, ticker
and verified aliases. Bound response size and rank exact ticker matches first.
Handle punctuation such as `BRK.B` without merging different share classes.
Keep an internal instrument ID stable across supported renames. Delisting or
an ambiguous ticker blocks new orders and preserves historical records.
Separate searchable metadata from financial instrument onboarding so the
catalog can be broad and hot quote/action work stays proportional to demand.

## Trading and operating behavior

Keep regular US sessions and effective early closes, eligible current-session
IEX bid/ask quotes aged under 120 seconds, portfolio ownership, zero commission
and transactional whole-share fills. Fetch quotes outside financial locks.
Recheck data and portfolio state at final confirmation, including requote
and idempotent retry behavior. Active quote requests can share cached results
and a provider-attempt budget. Search must work from local data when quote
access is down. Pin provider operations to documented endpoints.

Use a current, successfully read exchange halt snapshot as a simulator check.
Validate source timestamps, full response structure and reported resumption.
Handle individual and market-wide pauses. Source coverage and freshness must
be verified in Phase 18. Pause simulated execution with a clear reason when
necessary reports are stale or unavailable. Nasdaq asks clients to poll at
most once per minute. Publication and polling can delay an announced halt by
a minute or more. Record the source and observation time used for the fill.
This check makes no claim about continuous IEX venue-specific status.
[Nasdaq halt RSS](https://beta.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) ·
[NYSE circuit breakers](https://www.nyse.com/publicdocs/nyse/NYSE_MWCB_FAQ.pdf) ·
[NYSE calendar](https://www.nyse.com/trade/hours-calendars)

## Expansion and rollout risks

The old 20-symbol limit is enforced in services, schedulers, admissions,
actions, eligibility and UI. Leave sensible per-cycle and per-request bounds
in place. Replace fixed membership with catalog eligibility and bounded work
for stocks selected for trading or with active holdings. Confirm durable action
coverage and maintain a catch-up process for those instruments. Preserve
existing dividend and split semantics, including reconciliation holds. Check
calendar and action recovery after restart and rate limiting so ongoing
operation is viable on a free tier. [Corporate-action endpoint](https://docs.alpaca.markets/us/reference/corporateactions-1)

Prove a live-data simulated buy and sell alongside the existing crypto flow in
Phase 18, then repeat with a non-curated symbol once search and onboarding work.
Never send a brokerage order. Verify recovery and rollout at an integration
checkpoint using the project's normal release process. Reuse unaffected
portfolio, auth and crypto evidence where its inputs match.
