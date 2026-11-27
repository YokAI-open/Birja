# Phase 23 historical source qualification

The initial provider review on 2026-11-26 checked public documentation.
The subsequent live sample is recorded below. Both candidates remain
unqualified for serving live history to Birja users. Historical source generation, validity, and any
account or server binding remain unset. Prior live quote evidence applies to
that product and supplies no historical collection or display evidence.

| Candidate | Proposed windows and sample | Published technical coverage | Initial result on 2026-11-26 |
|---|---|---|---|
| Alpaca IEX stock bars | AAPL and exact catalog identity ORCL across 1D, 1W, 1M | 5-minute and 30-minute bars, IEX feed, USD, split adjustment, as-of symbol mapping and page tokens. Basic lists 200 historical requests/minute. [Endpoint](https://docs.alpaca.markets/us/reference/stockbars) · [Subscriptions](https://docs.alpaca.markets/us/docs/about-market-data-api) | 0 private calls. Bar counts, lag, rate headers, account quota and issue continuity remain unmeasured. Existing paper-account keys and quote approvals do not establish exact historical product access or conditions. |
| Kraken USD OHLC | BTC/USD across 1D, 1W, 1M | 5-, 60- and 240-minute candles, at most 720 rows including the unfinished final candle, which Birja discards. [Endpoint](https://docs.kraken.com/api-reference/market-data/get-ohlc-data) | 0 live calls. Bar counts, lag, rate headers, applicable rate ceiling and usable coverage remain unmeasured. Kraken's terms introduction places conditions on nonpersonal use. [API terms introduction](https://docs-legacy.kraken.com/api/docs/guides/global-intro/) |

For each source, activation requires applicable evidence for collection, user
display, derivation of price changes, and the actual transient cache retention
within Birja's audience. Record required attribution, permitted exact scopes,
covered instruments and intervals, validity and binding to the actual service
where applicable. An authorized sample would measure closed-bar counts,
freshness, identity and observed rate headers. The proposed campaign ceiling
is 12 IEX and 6 Kraken attempts across all ranges within 10 minutes, subject
to the applicable lower limits. IEX access uses the explicit IEX feed.
[Alpaca market data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)

Record whether each observed limit applies just to historical bars or to the
entire Alpaca account. When the provider's measured shared account ceiling
is lower than Birja's existing quote and corporate-action account ceiling,
bind the shared configuration to that lower ceiling before enabling history.

Local fixtures are enabled for both candidates. Live collection, display,
derived changes, and caching remain gated. The live portion of CHART-04
remains open.

## Provider terms recheck on 2026-11-27

- **Alpaca IEX.** The stock-bars endpoint supports the planned requests and
  Alpaca lists 200 historical requests per minute for Basic. Its public
  terms distinguish personal use from making data available through an
  application and describe advance notice for the latter. Birja's recorded
  Phase 7 confirmation covers quotes, actions and trading status. Evidence
  specific to historical bars for Birja's audience, derived price changes
  and short-lived cache is still missing.
  [Basic plan](https://docs.alpaca.markets/us/docs/about-market-data-api) ·
  [Alpaca terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf) ·
  [Phase 7 owner confirmation](../07-permitted-stock-discovery/07-OWNER-CLOSURE.md)
- **Kraken OHLC.** The public endpoint supports the planned intervals and
  returns at most 720 entries, including the unfinished candle. Kraken's
  published terms restrict making its content available to third parties.
  The project records contain no applicable historical display, derived
  change or cache permission for Birja. The combined OHLC and ticker rate
  budget also remains unmeasured.
  [OHLC reference](https://docs.kraken.com/api-reference/market-data/get-ohlc-data) ·
  [Global terms](https://www.kraken.com/legal/global-terms) ·
  [EEA terms](https://www.kraken.com/legal/eea-terms)

The public documentation review made zero live historical API requests.
The owner subsequently directed the bounded read-only verification below.

## Live sample on 2026-11-27

The owner approved the bounded test. The existing history adapters and
normalizer processed nine HTTP 200 responses in about 15 seconds. The test
used the existing local Alpaca credentials and Kraken's public endpoint.
It kept only sanitized metrics. The source application was `e7b08d1`,
whose application tree matches the Phase 25 candidate.

| Instrument | 1D points | 1W points | 1M points | Result |
|---|---:|---:|---:|---|
| BTC/USD | 288/288 | 168/168 | 180/180 | Complete, on time |
| AAPL | 78/78 | 65/65 | 286/286 | Complete, on time |
| ORCL | 78/78 | 65/65 | 286/286 | Complete, on time |

The expected slots came from the chart windows and the local exchange
calendar. The stock tests ran before the November 27 regular session,
so the latest expected stock close was November 25 at 21:00 UTC. ORCL's
sample used the NYSE symbol previously checked against the catalog.
[ORCL identity evidence](../21-verify-release-and-activate-stock-trading/21-LIVE-QUALIFICATION.md)

- The six IEX requests each reported a rate limit of 200 and had at least
  199 remaining in the response. Alpaca documents 200 historical calls
  per minute for Basic. The sample establishes the historical endpoint's
  advertised limit and observed response headers. The existing production
  workload was measured separately below.
  [Alpaca Basic limits](https://docs.alpaca.markets/us/docs/about-market-data-api)
- Three Kraken OHLC requests succeeded at least two seconds apart. The
  sample returned no numeric rate headers. Kraken documents up to one
  public request per second as a working frequency and distinguishes
  OHLC per-IP-and-pair limits from the ticker IP limit. The bounded
  production request envelope is checked below.
  [Kraken API limits](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-)

Sanitized receipt SHA-256 `59be846219338e39682195fcc12adea6c24c26c83b7204e1c03db73c12770781`.

## Shared request budget

A read-only production observation started at 07:36 UTC on 2026-11-27.
The dedicated scheduler had a 60-second cadence for Kraken Ticker, Alpaca
quotes and corporate actions. It had 15 active crypto pairs and an
effective Alpaca ceiling of 20 attempts per rolling minute. Across 66
one-second samples of the shared Redis counter, between zero and two
attempts fell in a rolling minute. No chart scope was loaded.

- **Alpaca.** Use the lower internal ceiling of 20 measured on the
  running configuration. History preserves half of that ceiling for
  quotes and actions, shares the existing rolling counter, and has
  a separate ceiling of four attempts per minute. The observed workload
  left room for all four. This is a point-in-time measurement. The
  scheduler rechecks current capacity before each page.
- **Kraken.** One 60-second ticker cycle can consume at most 18 requests
  for the batch, its retries and 15 pair fallbacks. The chart code
  counts actual attempts still in the rolling minute and reserves
  future ticker work. Under Kraken's published one-request-per-second
  guidance, the chart cap is six per minute with a separate one-second
  spacing check. History defers during a ticker cycle, near its next
  run, and for one second after any ticker attempt, including a
  fallback for a different pair. The workload measurement establishes
  configuration and the code enforces the request budget at runtime.
  The live sample was below provider limits and did not exercise
  throttling.

The combined-rate guard and the affected chart, ticker and stock schedulers
passed 141 isolated tests. Production still has no chart scope.

**CHART-04 remains open for live chart deployment.** Coverage, freshness
and the shared request budget are documented. Multi-user display, derived
changes and temporary cache scope remain unverified in the source evidence.
