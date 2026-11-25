---
status: incomplete
date: 2026-11-24
---

# Stock activation verification

Production was checked at deployed commit `07d3aa5`. It served the 20-stock
catalogue with no quotes, unknown trading statuses and no executable stocks.
Quote and corporate-action collection are disabled. The scheduler's status
cycle has a test-only input and no live transport. Phase 7 owner acceptance is
already [recorded](../../phases/07-permitted-stock-discovery/07-OWNER-CLOSURE.md).

## Read-only Alpaca checks

During the regular session, starting at 16:58 Amsterdam time on November 24:

| Check | Result |
| --- | --- |
| IEX WebSocket `statuses` for the catalogue | Authenticated and acknowledged all 20 symbols. Zero status messages during the 25-second probe. |
| Latest IEX quotes | HTTP 200. One batch returned all 20 symbols with positive bid and ask and source timestamps at most eight seconds old. |
| Corporate actions REST | HTTP 200. Four records for the November-to-date sample, with no further page indicated. |
| Corporate-action SSE replay | HTTP 200 with an event-stream response for a bounded past interval. Replay completeness and event latency were outside this access check. |

The status probe did not establish whether the account receives future
halt/resume events. Alpaca documents a status channel but its public schema
does not specify a startup snapshot or a replay cursor. The stock snapshot
endpoint documents pricing fields. The API keys, returned quotes and action
payloads were excluded from this report. [Status channel][status] ·
[Stock snapshot][snapshot] · [Action replay][actions].

## Existing adapters and live display rehearsal

- Birja's own quote adapter accepted all 20 stocks in a separate live batch.
- The corporate-action adapter read a complete November-to-date REST sample
  with four normalized records. Its finite SSE replay reached a clean end for
  the selected one-minute window, which contained no events. This verifies
  endpoint and parser behavior for those samples. Action history and ongoing
  monitoring still need qualification against production admission rules.
- On a disposable PostgreSQL and Redis stack, one real scheduler cycle
  accepted and persisted 19 of 20 live quotes. The Markets response displayed
  all 19 persisted quotes and marked zero stocks executable. Verified test
  fixture admissions and action coverage were scoped to the disposable stack.
  The first attempt's assertions succeeded but fixture teardown failed due to
  event loop settings. The rerun using the project's settings passed and its
  containers were removed.

## Status source decision still open

A public Nasdaq Trader RSS sample returned a published timestamp and 45 halt
records, including older halts. That feed covers reported halts and pauses for
Nasdaq and other listings, updates once a minute, and requests polling at most
once a minute. The documented coverage does not establish venue-specific IEX
operational status. Birja's 60-second lease would also expire between polls
when refresh or delivery slips. Treat this as a useful source of reported
halts. Using it as execution authority would require an explicit decision on
coverage, evidence freshness and permitted use. [Nasdaq halt feed][nasdaq].

On the deployed source tree, all 79 trading-rule tests and 31 selected status
rule cases passed as standalone unit tests. The default integration harness
could not open its local test database socket in the sandbox. The live-source
buy and sell remain pending.

No application change or production activation was performed. Once a source
can establish current status on startup and recovery, resume the plan at
scheduler integration and isolated buy/sell verification.

The owner chose to continue without contacting Alpaca. IEX documents dedicated
snapshot feeds, and Intrinio documents a per-symbol current-status API for
selected sources. Neither was verified to be available for this deployment at
no cost. [IEX feed specifications][iex] · [Intrinio status API][intrinio] ·
[Intrinio pricing][pricing].

[status]: https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data#trading-status
[snapshot]: https://docs.alpaca.markets/us/reference/stocksnapshotsingle
[actions]: https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse
[nasdaq]: https://beta.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS
[iex]: https://www.iex.io/resources/trading/market-data
[intrinio]: https://data.intrinio.com/documentation/web_api/get_security_trading_status_v2
[pricing]: https://intrinio.com/pricing
