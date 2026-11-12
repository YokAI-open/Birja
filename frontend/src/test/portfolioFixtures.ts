import type { Portfolio, PortfolioHolding } from "@/api/portfolio";
import { quoteFixture } from "./stockTradeFixtures";
export function cashPortfolio(): Portfolio {
  return {
    cash: "10000.00", starting_cash: "10000.00", total_value: "10000.00",
    total_pl: "0.00", total_pl_percent: "0.00", cash_allocation_percent: "100.00",
    valuation_complete: true, known_value: "10000.00", unvalued_holding_count: 0,
    class_values: { cash: "10000.00", stocks: "0.00", crypto: "0.00" },
    class_allocation_percent: { cash: "100.00", stocks: "0.00", crypto: "0.00" },
    valued_at: "2026-11-10T15:00:10Z", prices_as_of: null,
    fresh_seconds: 120, stale_seconds: 300, holdings: [],
  };
}
export function stockHolding(): PortfolioHolding {
  const q = quoteFixture();
  return {
    symbol: "AAPL", name: "Apple Inc.", coin_id: "16", provider_asset_id: "asset-aapl",
    asset_class: "stock", is_active: true, quantity: "2", cost_basis: "204.00",
    average_cost: "102.00000000", mid: "101.000000000", current_value: "202.00",
    unrealized_pl: "-2.00", unrealized_pl_percent: "-0.98", allocation_percent: "2.02",
    as_of: q.event_at, age_seconds: 10, status: "fresh",
    stock_mark: { mark_mode: "fresh", valuation_reason: "available", source: "alpaca", feed: "iex",
      event_at: q.event_at, collected_at: q.collected_at,
      historical_admission_until: "2026-11-10T16:00:00Z", retained_until: "2026-11-10T16:00:00Z",
      valid_until: "2026-11-10T15:01:00Z", authority: q.authority, units_safe: true },
  };
}
export function mixedPortfolio(): Portfolio {
  return { ...cashPortfolio(), cash: "9796.00", total_value: "9998.00", known_value: "9998.00",
    total_pl: "-2.00", total_pl_percent: "-0.02", cash_allocation_percent: "97.98",
    class_values: { cash: "9796.00", stocks: "202.00", crypto: "0.00" },
    class_allocation_percent: { cash: "97.98", stocks: "2.02", crypto: "0.00" },
    prices_as_of: "2026-11-10T15:00:00Z", holdings: [stockHolding()] };
}
