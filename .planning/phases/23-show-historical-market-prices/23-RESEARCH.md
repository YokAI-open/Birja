# Phase 23 — Historical price research

Reviewed 2026-11-26 on local integration source `2b36bc1`.
Findings use published documentation and repository inspection.

## Data candidates and scope

Alpaca publishes historical aggregate bars with explicit `feed=iex`,
`adjustment=split`, as-of mapping and page tokens. Its Basic plan documents
200 historical requests/minute. The FAQ distinguishes IEX and SIP access.
A returned 200 does not establish applicable display or storage scope.
Qualify IEX latency, data gaps, symbol mapping and the actual account quota
before enabling stock history. No alternate feed or paid tier is selected.
[Alpaca bars](https://docs.alpaca.markets/us/reference/stockbars) ·
[Alpaca plan limits](https://docs.alpaca.markets/us/docs/about-market-data-api) ·
[Alpaca FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)

Kraken Spot OHLC retains its newest 720 intervals for each public pair.
Its trailing item is uncommitted. Its documentation subjects public data
to applicable terms. The existing Kraken ticker client uses decimal-aware
parsing and a separate refresh cycle. Qualify historical USD pairs and
display, cache and derived-value scope specifically.
[Kraken OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data) ·
[Kraken API terms introduction](https://docs-legacy.kraken.com/api/docs/guides/global-intro/)

Public descriptions and prior quote admissions are research inputs. Neither
constitutes a new historical-data qualification. Plan 23-01 records any
applicable written basis and a small approved sample or a precise blocker.
An unsupported source stays disabled while local fixture work can continue.

## Windows and calculations

| Range | Crypto | Equity |
|---|---|---|
| 1D | Last 24 hours, 5-minute Kraken close | Current or last regular exchange session, 5-minute IEX close |
| 1W | Last 7 days, 60-minute Kraken close | Last 7 calendar days through the reference session, 30-minute IEX close |
| 1M | Last 30 days, 240-minute Kraken close | Last 30 calendar days through the reference session, 30-minute IEX close |

Use provider interval start for validation and normalized interval end for
plotting. Equity filtering requires the entire bar inside a verified
regular session, including early closes. Use available admitted calendar rows
from `stock_sessions.py` and the matched calendar generation. Published
coverage is bounded and might omit historical dates. In that case show gaps
or report partial coverage. Windows seek the required previous session
baseline within that admitted coverage. Reject an interval crossing a ticker
version boundary unless mapping proves the same issue throughout it. Use
explicit split-adjusted IEX bars and clear price-only change labels. Kraken's
current unfinished bar and an unclosed IEX interval cannot become a point.

Use Decimal until rendering. For daily equity change compare the last observed
bar in the reference regular session with the last observed close in the
previous verified regular session. Require an observed final interval for
a completed comparison session and a consistent adjustment basis. Crypto day
compares completed closes exactly 24 hours apart on the same interval grid.
Period change requires comparable endpoints for the requested window.
Insufficient coverage yields no percentage. Keep partial points and gap
boundaries explicit. Never use current midpoint as a historical endpoint.

Report coverage and timeliness independently. Expose `as_of` for the
latest observed complete interval end and `expected_through_at` for the
latest completed bucket after a 60-second publication grace. Compute
the expectation from the crypto interval grid or the verified regular
exchange session, including the most recent session end when closed.
Use delayed if usable bars end before that expectation, on_time when
they reach it, and unknown when calendar or source coverage cannot
establish it. A delayed series can also be partial. Treat a missing
trailing IEX interval as data behind the regular-session grid without
asserting the cause. Keep timestamps and source delay separate from
current quote eligibility.

## Existing boundaries

- `backend/app/tasks/scheduler.py` owns Alpaca credentials. The API remains
  credential-free. Use its isolated background loop and
  `stock_scheduler.reserve_account_attempt` for stock history alongside a
  lower history-only cap. Preserve at least half the effective account
  ceiling for quotes and actions, taking the minimum of configured,
  admitted and observed ceilings. Qualify Kraken quota at the combined
  Ticker and OHLC public IP/pair scope and defer history when spare
  capacity cannot be established or ticker work is due.
- `stock_catalog_quotes.py` provides an existing verified mapping path.
  Catalog inputs are ID and listing version. Curated and crypto identities
  resolve server-side, using the existing instruments and Kraken pair.
  Map quote rights only as identity evidence. History authority has its own
  evidence validity, fields, cached-display and derivatives allowances.
- The production catalog cache is a separately configured memory-only Redis.
  Reuse this connection with a separate history namespace if qualifying
  evidence permits. When absent or unhealthy show a chart state, with no
  provider work from the API and no persistence. No migration, broker,
  package or new datastore is necessary. History never writes market quotes,
  trade tables or portfolio data.
- Reuse authenticated `api/client.ts`, existing CSRF handling, TanStack Query
  and account/session fencing. Open one request only for the selected
  instrument and range. Reuse display data for Day cells only where an
  already-held valid series supplies a comparable figure for that row.
  Do not fetch the whole list by default or fabricate a historical price.

## Validation Architecture

Use isolated pytest with fixed provider HTTP fixtures and actual Redis
for bounds, quota sharing and job identity. Test calendar closures, DST,
sparse bodies, ticker reuse, short pagination, stale and expired authority,
future/unfinished candles, split-adjusted changes and decimal rounding.
Vitest covers decoder, query identity and errors, visual chart controls,
text alternative, and trade independence. Playwright uses the real app
with deterministic chart data to compare wide and narrow ZIP references.
Record a dated live-source receipt only for actually authorized,
measured samples. Browser fixtures are separate evidence.
