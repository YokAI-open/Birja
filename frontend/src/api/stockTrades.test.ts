import { describe, expect, it } from "vitest";
import { isStockFill, isStockTradeQuote, type StockTradeQuote, type StockFill } from "./stockTrades";

export function quoteFixture(): StockTradeQuote {
  return {
    coin_id:"16",provider_asset_id:"asset-aapl",symbol:"AAPL",company_name:"Apple Inc.",
    listing_exchange:"NASDAQ",currency:"USD",side:"buy",quantity:"2.00000000",
    bid:"100.00000000",ask:"102.00000000",exact_mid:"101.000000000",exec_price:"102.00000000",
    source:"alpaca",feed:"iex",event_at:"2026-11-10T15:00:00Z",collected_at:"2026-11-10T15:00:01Z",
    observed_at:"2026-11-10T15:00:10Z",age_seconds:10,notional:"204.00000000",fee:"0.00000000",
    cash_delta:"-204.00000000",cash_before:"10000.00000000",cash_after:"9796.00000000",
    held_before:"0.00000000",held_after:"2.00000000",session_date:"2026-11-10",
    session_opens_at:"2026-11-10T14:30:00Z",session_closes_at:"2026-11-10T21:00:00Z",
    valid_until:"2026-11-10T15:01:00Z",
    authority:{
      admissions:(["reference","quotes","actions","status","calendar"] as const).map(product=>({
        product,generation:4,row_hash:"a".repeat(64),valid_until:"2026-11-10T16:00:00Z",
      })),calendar_generation:4,safety_epoch:2,unit_epoch:0,status_admission_generation:4,
      continuity_generation:1,status_sequence:12,
    },
  };
}
export function fillFixture(): StockFill {
  const {valid_until: _unused,...facts}=quoteFixture();
  return {...facts,schema_version:1,trade_id:"9007199254740993",executed_at:"2026-11-10T15:00:09Z"};
}

describe("stock money and immutable receipt boundary",()=>{
  it("accepts exact fee-free economics and saved bigint IDs without renewing old receipts",()=>{
    expect(isStockTradeQuote(quoteFixture())).toBe(true);
    expect(isStockFill(fillFixture())).toBe(true);
  });
});
