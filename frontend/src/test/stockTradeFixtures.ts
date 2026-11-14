import type { StockTradeQuote, StockFill, StockContext } from "@/api/stockTrades";

export function quoteFixture(): StockTradeQuote {
  return {
    coin_id: "16",
    provider_asset_id: "asset-aapl",
    symbol: "AAPL",
    company_name: "Apple Inc.",
    listing_exchange: "NASDAQ",
    currency: "USD",
    side: "buy",
    quantity: "2.00000000",
    bid: "100.00000000",
    ask: "102.00000000",
    exact_mid: "101.000000000",
    exec_price: "102.00000000",
    source: "alpaca",
    feed: "iex",
    event_at: "2026-11-10T15:00:00Z",
    collected_at: "2026-11-10T15:00:01Z",
    observed_at: "2026-11-10T15:00:10Z",
    age_seconds: 10,
    notional: "204.00000000",
    fee: "0.00000000",
    cash_delta: "-204.00000000",
    cash_before: "10000.00000000",
    cash_after: "9796.00000000",
    held_before: "0.00000000",
    held_after: "2.00000000",
    session_date: "2026-11-10",
    session_opens_at: "2026-11-10T14:30:00Z",
    session_closes_at: "2026-11-10T21:00:00Z",
    valid_until: "2026-11-10T15:01:00Z",
    authority: {
      admissions: (["reference", "quotes", "actions", "status", "calendar"] as const).map(
        (product) => ({
          product,
          generation: 4,
          row_hash: "a".repeat(64),
          valid_until: "2026-11-10T16:00:00Z",
        }),
      ),
      calendar_generation: 4,
      safety_epoch: 2,
      unit_epoch: 0,
      status_admission_generation: 4,
      continuity_generation: 1,
      status_sequence: 12,
    },
  };
}
export function fillFixture(): StockFill {
  const { valid_until, ...facts } = quoteFixture();
  void valid_until;
  return {
    ...facts,
    schema_version: 1,
    trade_id: "9007199254740993",
    executed_at: "2026-11-10T15:00:09Z",
  };
}

export function contextFixture(): StockContext {
  const q = quoteFixture();
  return {
    coin_id: q.coin_id,
    provider_asset_id: q.provider_asset_id,
    symbol: q.symbol,
    company_name: q.company_name,
    listing_exchange: q.listing_exchange,
    observed_at: q.observed_at,
    cash: q.cash_before,
    held_quantity: q.held_before,
    buy_max_quantity: "98",
    quote: {
      bid: q.bid,
      ask: q.ask,
      exact_mid: q.exact_mid,
      source: "alpaca",
      feed: "iex",
      event_at: q.event_at,
      collected_at: q.collected_at,
      session_date: q.session_date,
      admission_generation: 4,
      unit_epoch: 0,
    },
    session: {
      state: "open",
      session_date: q.session_date,
      opens_at: q.session_opens_at,
      closes_at: q.session_closes_at,
      valid_until: "2026-11-10T16:00:00Z",
      next_open_at: null,
      timezone: "America/New_York",
    },
    status: {
      state: "normal",
      event_at: "2026-11-10T14:00:00Z",
      observed_at: "2026-11-10T15:00:05Z",
      valid_until: "2026-11-10T15:01:05Z",
      bootstrap_verified: true,
      continuity_current: true,
    },
    action: {
      state: "current",
      reason: "available",
      valid_until: "2026-11-10T16:00:00Z",
      next_blocking_at: null,
    },
    authority: q.authority,
    execution_enabled: true,
    execution_reason: "available",
    valid_until: q.valid_until,
  };
}
