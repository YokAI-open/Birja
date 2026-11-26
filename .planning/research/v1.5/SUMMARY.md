# v1.5 chart feasibility

2026-11-26. Repository and public documentation review from integration
baseline `81a930e`.

## Historical market prices

The crypto [price model](../../../backend/app/models/price.py) retains one
latest mid per asset. The [prices API](../../../backend/app/api/v1/prices.py)
serves that value and its age. Markets already has a catalog selection path,
and current quote validation and order execution have their own contracts.
Historic closes need a separate read path and must never become executable
prices.

Alpaca documents stock bars with an explicit IEX feed, timeframes, adjustment
modes and pagination. Kraken documents a public spot OHLC endpoint that
returns up to 720 recent entries and includes the current unfinished
interval. Use these as candidates and qualify the actual coverage and
applicable display, caching and retention scope before enabling history.
Choose intervals that fit the bounded windows. Use real source timestamps
and exchange sessions for US stocks, and treat sparse or incomplete coverage
explicitly. Decide how splits, symbol changes and open intervals are
represented before labeling a change figure as day or period performance.
Reuse the existing provider mappings and free-tier request budgets. Fetch by
selected instrument and range with bounded caching and shared requests.
[Alpaca historical bars](https://docs.alpaca.markets/us/reference/stockbars) ·
[Kraken OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data)

## Portfolio history

The [portfolio service](../../../backend/app/services/portfolio.py) calculates
the current value with per-holding eligibility and the original funding
baseline. The project has no portfolio value-over-time series. The proposed
first version records daily, owner-scoped value snapshots for active
portfolios from the rollout forward. Use the exact existing valuation and
retain missing marks as an incomplete observation. Snapshot retries must
not create duplicate points, and the capture path must respect portfolio
closure. A new or existing portfolio without enough points still shows its
current total and return.

Prefer a small, accessible line chart in the existing frontend stack. Select
the rendering approach in the phase plan after testing keyboard access,
readable time and price labels, and responsive rendering. Reuse the existing
PostgreSQL recovery process for any durable snapshot schema.

## Build order

First adopt the Markets workspace and navigation over the working APIs.
Then add the market price-history path, the private portfolio trends, and the
remaining page refactor with integration acceptance. Keep historical series
failures out of the quote, search, preview and order paths.
