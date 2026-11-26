# Phase 23 historical source qualification

Reviewed public provider documentation on 2026-11-26. Both candidates remain
unqualified for live history. Historical source generation, validity, and any
account or server binding remain unset. Prior live quote evidence applies to
that product and supplies no historical collection or display evidence.

| Candidate | Proposed windows and sample | Published technical coverage | Measured result |
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
