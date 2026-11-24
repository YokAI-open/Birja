# Phase 18 source decision

Decision: qualified

Policy: reported-halt simulator

The owner revised SX-02 on November 24 after reviewing the incomplete free
coverage. Nasdaq is admitted as the public candidate for **reported halts** only.
Current report receipt requires HTTP 200, time-bounded Last-Modified, bounded
well-formed RSS with consistent item count, and valid Eastern halt/resumption
fields. Block rows with no elapsed trade resumption time, and block the whole
market if the report carries an active market-wide code. Overlapping records
remain halted while any active notice remains. Use on-demand IEX quotes under
120 seconds, and disclose possible late or missing exchange reports. This
revises the previous complete-coverage requirement.

## IEX quotes

The existing account and adapter worked during the November 24 regular
session. One quote-only live batch returned 20 valid positive two-sided prices
aged at most eight seconds. The adapter accepted 20 in a separate run. The
18-01 execution reused the [dated live receipt](../../quick/20261124-stock-activation/SUMMARY.md).
Alpaca documents IEX on Basic and the latest quote endpoint's quota headers.
Actual header limits were not recorded in that receipt. The existing rolling
Redis limiter still caps the combined quote/action attempt rate to the
minimum of configured and permitted rates, normally at most 20 per minute.
Phase 7 retains the [owner attestation](../07-permitted-stock-discovery/07-OWNER-CLOSURE.md)
for the original 20. No broadened use or new rights are inferred.
[Alpaca Basic](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api) ·
[Latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1)

## Official halt reports

One read of each public source at 16:42:57 UTC on November 24 returned:

| Source | Sample | Timing evidence |
|---|---|---|
| [Nasdaq current RSS](https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts) | 53 rows, 13 without trade resumption | `Last-Modified` 16:42:20 UTC, channel `pubDate` 16:42:21 UTC, no `lastBuildDate` |
| [NYSE current CSV](https://www.nyse.com/api/trade-halts/current/download) | 51 rows, 14 without `NYSE Resume Time` | `Last-Modified` 16:42:27 UTC, `Age: 30`, `max-age=300`, no explicit dataset publication or completeness field |

The counts represent different response views. They do not establish a
complete combined snapshot or prove specific differences in halt status.
Nasdaq asks clients to poll no more often than once a minute. The documented
March 16, 2020 historical RSS query returned 820 rows with no explicit
market-wide breaker codes, although the exchange working group confirms a
market-wide halt that day. Its `pubDate` showed the current request day.
Current HTTP dates support local retrieval checks but do not prove underlying
completeness, market-wide coverage or authoritative source data age. NYSE
archives document one year for news and individual LULD events. The working
group describes CTA and UTP operational market-wide messages and exchange
notices. Free, current machine-readable access with full scope and usable
freshness was not established in this pass. [Nasdaq RSS scope and cadence](https://beta.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) ·
[NYSE halt page](https://www.nyse.com/trade/trading-halts) ·
[Exchange working group report](https://www.nyse.com/publicdocs/nyse/markets/nyse/Report_of_the_Market-Wide_Circuit_Breaker_Working_Group.pdf)

## Execution disposition

The historical complete-coverage disposition was blocked. The current decision
qualifies the documented feeds for the narrower owner-approved simulator scope.
See the [live receipt](18-LIVE-RECEIPT.md) for the observed report and trade results.
