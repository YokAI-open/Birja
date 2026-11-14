# Feasibility: Free Current US Stock Data for Birja

**Researched:** 2026-11-10
**Verdict:** CONDITIONAL — no investigated free plan was verified to meet the full public-app requirement.
**Confidence:** HIGH in documented restrictions; MEDIUM in technical alternatives;
LOW in any unconfirmed free public-display entitlement.

## Decision in Plain Terms

Twenty stocks refreshed every minute is a small technical workload. Permission
to show recent US equity data to other people is the unresolved part. Free
personal access, noncommercial intent, login protection and a small friend group
do not by themselves grant redistribution/display rights. A public production
simulator is not automatically a provider's sandbox.

Recommend investigating **explicit zero-cost permission for Alpaca IEX first**.
That requires owner authorization to pursue/accept an agreement, not silent signup
or assistant contact with the provider. If permission cannot be established, the
owner must choose a changed licensed budget or an explicitly changed feature
scope. Do not lower freshness or reinterpret stock execution without approval.
This research does not claim that a free public-feed agreement is impossible.

## What “Like Crypto” Must Mean

| Concept | Meaning for requirements |
|---|---|
| Poll frequency | Scheduler asks upstream about every 60 seconds |
| Source age | Time since the event the returned price represents; checked separately from receipt time |
| Exchange-imposed delay | A fifteen-minute-delayed feed cannot meet the requested recency even if polled every second |
| One-minute bar | Aggregation interval, not a promise of delivery within one minute |
| IEX-only data | Current events from one trading venue for US-listed securities; not all US market activity |
| SIP/NBBO | Consolidated market activity/national best quotes; different coverage and entitlement from IEX |

Birja's existing crypto execution rejects age ≥120 seconds. A sensible **proposed**
stock contract is polling about once/minute with source-age rejection consistent
with that policy, including after locks. It is not a one-minute guaranteed market
data SLA. Must confirm exact age threshold and IEX coverage with the owner before
freezing requirements. A closed-market cached quote can remain useful for clearly
dated valuation, but cannot authorize stock orders.

## Provider Matrix

| Provider / plan | Documented data and quota | Workload fit | Display/usage finding | Decision |
|---|---|---|---|---|
| **Alpaca Basic, Trading API** | Current IEX; 200 calls/minute; 30 streaming symbols; all-US-exchange coverage is a different subscription [1] | Batch latest-quotes API accepts symbol list; one request/minute for 20 symbols [2] | Personal developer product does not establish Birja distribution rights. Official older Broker docs allow IEX redistribution in the sandbox but require production contact [3] | **Best conditional technical candidate; NOT cleared for public deployment** |
| **Finnhub free/personal** | US quote endpoint exists; official dynamic pricing/docs pages were not readable in this research, so advertised 60/minute is not re-verified here [4] | If 60/minute is confirmed, single-symbol polling needs 20/minute; no batch discount assumed | Terms explicitly require written approval for sharing data or derived results; paid personal access is not enough [5] | **Blocked on permission; quota/feed detail additionally unverified** |
| **Twelve Data Basic** | Eight credits/minute; 800/day; eight trial WebSocket credits; Basic internal non-display [6] | At least 20 credits/minute, 7,800/day for one-credit-per-symbol endpoint; batching does not eliminate symbol cost [7] | External display is a separately described business plan capability [6] | **Fails quota and usage scope** |
| **Massive, formerly Polygon, Stocks Basic** | Five API calls/minute; end-of-day; individual use; minute aggregate availability does not make it real-time [8] | Individual per-stock polling needs 20/minute, above five; no eligible current batch quote endpoint established | Free plan not a demonstrated public display license | **Fails freshness regardless of batching** |
| **Alpha Vantage standard free** | 25 API requests/day; current and fifteen-minute-delayed US data premium-only [9] | Single-symbol 7,800/day impossible; premium bulk endpoint does not rescue free entitlement [10] | Documentation differentiates personal premium from commercial sales [10] | **Fails freshness/quota** |
| **Market Data self-service** | A current-price endpoint exists; credit cost per symbol [11] | Freshness endpoint is technically promising; no free quota sufficient for workload established here | Official redistribution policy specifically routes app display to Commercial plan [12] | **No verified free public option** |

No provider above has been authenticated, probed with a key, signed up for, or
accepted on the owner's behalf. All capabilities are documentation findings.
Do not infer provider entitlement from a successful public HTTP request.

## Quota Calculation

Assume a normal 6.5-hour regular session, a single scheduler and exactly 20 stocks.
Use 390 one-minute intervals as a baseline; startup/close, retries, calendars,
reference metadata and corporate-action checks require additional reserved quota.
An implementation that samples both endpoints of the day can need 391 cycles.

| Fetch scheme | Baseline/minute | Baseline/session | Notes |
|---|---:|---:|---|
| One request per symbol | 20 requests | 7,800 requests | 156,000 requests for a hypothetical 20-full-session month |
| Verified 20-symbol batch, e.g. Alpaca latest quotes | 1 request | 390 requests | 7,800 for that hypothetical month, before overhead |
| Symbol-metered batch, e.g. Twelve Data | ≥20 credits | ≥7,800 credits | Fewer HTTP requests do not reduce symbol metering |
| Twelve Data 800/day at 20 symbols | 40 full-list refreshes/day maximum | — | About one refresh per 9.75 minutes across a full session even ignoring the eight/minute cap and overhead; not acceptable |

Normal sessions used for quota budgeting follow exchange hours; holidays/early
closes reduce workload but do not make an underprovisioned full-day plan fit. [13,14]
Never multiply provider calls by users or trade previews. Do not rotate accounts,
keys or vendors to evade quota. Retries must be bounded inside quota headroom.

## Access, Contracts and Practical Constraints

- Alpaca says Paper Only registration is globally available with email and limits
  that account to IEX data. That is evidence for a prototype account path, not
  public redistribution or a country-specific production-eligibility guarantee.
  A real-money brokerage account is unnecessary for Birja; do not introduce KYC,
  deposits or real order routing to solve data access. [15]
- Paid subscriptions, sales agreements or registration are not authorized by this
  research. No credit card is available according to prior owner context. Confirm
  that any selected permitted account can operate without a payment instrument,
  and document any location/account restrictions rather than using a VPN or
  claiming universal access.
- Quotes shown through Birja's backend still reach third-party users. Storing
  fills and displaying holdings/P&L may also depend on provider retention and
  derived-data terms. Confirm those rights alongside raw quote display; hiding a
  provider key or calculating a midpoint does not itself resolve permission.
- Alpaca free IEX is a useful limited-venue candidate; access to complete SIP data
  and a personal paid subscription would not automatically solve public licensing.
- An exchange's direct-data redistribution policy is not sufficient evidence for
  the agreement applying to a separate vendor. Obtain the actual vendor/product
  terms for the selected account.

## Required Owner Decision Before Requirements Are Final

1. **Keep $0 and current freshness:** authorize pursuing explicit free public
   simulator/display permission for a suitable candidate, starting with Alpaca,
   and decide whether clearly labelled IEX-only quotes are acceptable. No provider
   contact/sign-up should occur without authorization. Live availability stays a
   blocking prerequisite until permission and account access are established.
2. **Change budget:** only if the owner chooses, research a price for the actual
   external-display use case. Do not present a personal subscription's price as
   the price of a public simulator license.
3. **Defer live stocks/change scope:** preserve crypto and record stock rollout as
   gated. Historical/replay/delayed stock trading would be a new scope decision,
   and delayed data still needs appropriate usage rights.

The owner has not yet chosen any of these responses to the research findings.
Research approval does not authorize expenditure or signing data agreements.

## Sources

Primary documentation accessed **2026-11-10**. Undated pages are current readbacks,
not dated guarantees. Sources with explicit dates: Twelve Data terms 2026-01-01;
Market Data redistribution policy 2026-10-23. Finnhub dynamic docs/pricing could
not be verified by readable primary text; this limitation is explicit above.

1. [Alpaca plans](https://docs.alpaca.markets/us/docs/about-market-data-api) — HIGH, updated about October 2026.
2. [Alpaca latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1) — HIGH, updated about May 2026.
3. [Alpaca official Broker docs](https://github.com/alpacahq/bkdocs/blob/master/content/market-data/_index.md) — HIGH for text, limited/older sandbox context.
4. [Finnhub quote docs](https://finnhub.io/docs/api/quote), [pricing](https://finnhub.io/pricing) — dynamic content unreadable; current numerical plan detail UNVERIFIED here.
5. [Finnhub terms](https://finnhub.io/terms-of-service) — HIGH, explicit sharing/personal-use rule.
6. [Twelve Data business pricing](https://twelvedata.com/pricing-business), [terms](https://twelvedata.com/terms) — HIGH.
7. [Twelve Data credits](https://support.twelvedata.com/en/articles/5615854-credits) — HIGH, symbol accounting and daily reset.
8. [Massive stocks pricing](https://massive.com/pricing?product=stocks) — HIGH.
9. [Alpha Vantage support](https://www.alphavantage.co/support/) — HIGH.
10. [Alpha Vantage API](https://www.alphavantage.co/documentation/) — HIGH, bulk current-data endpoint/entitlement distinction.
11. [Market Data stock prices](https://www.marketdata.app/docs/api/stocks/prices/) — HIGH, current endpoint and symbol credit cost.
12. [Market Data redistribution](https://www.marketdata.app/docs/account/data-policies/data-redistribution/) — HIGH, updated 2026-10-23.
13. [NYSE hours/calendars](https://www.nyse.com/markets/hours-calendars) — HIGH.
14. [Nasdaq calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar) — HIGH.
15. [Alpaca Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading) — HIGH for documented registration/entitlement; not a Birja distribution grant.
