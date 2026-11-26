import { describe, expect, it } from "vitest";
import { decodeMarketHistory, type HistoryInstrument, type HistoryResponse } from "./marketHistory";

const instrument = {
  kind: "catalog",
  catalog_id: "9007199254740993",
  listing_version: "2",
} as const;
const response: HistoryResponse = {
  instrument,
  range: "1W",
  state: "ready",
  series: {
    source: "alpaca_iex",
    currency: "USD",
    time_basis: "regular_session",
    adjustment: "split",
    interval_minutes: 30,
    start_at: "2026-11-23T14:30:00Z",
    end_at: "2026-11-24T15:00:00Z",
    expected_through_at: "2026-11-24T15:00:00Z",
    as_of: "2026-11-24T15:00:00Z",
    coverage: "complete",
    timeliness: "on_time",
    points: [
      {
        starts_at: "2026-11-23T14:30:00Z",
        ends_at: "2026-11-23T15:00:00Z",
        close: "0.000434005916",
        gap_before: null,
      },
      {
        starts_at: "2026-11-24T14:30:00Z",
        ends_at: "2026-11-24T15:00:00Z",
        close: "0.000441005916",
        gap_before: "closed",
      },
    ],
    day_change_pct: "1.61",
    period_change_pct: "1.61",
  },
};

describe("market history response", () => {
  it("preserves exact catalog identifiers and decimal closes", () => {
    expect(decodeMarketHistory(response, instrument, "1W")).toEqual(response);
  });

  it.each(["pending", "unavailable"])("accepts a null series in %s", (state) => {
    const pending = { instrument, range: "1D", state, series: null };
    expect(decodeMarketHistory(pending, instrument, "1D")).toEqual(pending);
  });

  it.each([
    { kind: "catalog", catalog_id: instrument.catalog_id, listing_version: "1" },
    { kind: "catalog", catalog_id: "9007199254740992", listing_version: "2" },
    { kind: "featured", symbol: "AAPL" },
    { kind: "crypto", symbol: "BTC" },
  ] satisfies HistoryInstrument[])("rejects a different instrument %j", (other) => {
    expect(() => decodeMarketHistory(response, other, "1W")).toThrow();
  });

  it("discards a different range and mismatched state/series", () => {
    expect(() => decodeMarketHistory(response, instrument, "1M")).toThrow();
    expect(() =>
      decodeMarketHistory({ ...response, state: "pending" }, instrument, "1W"),
    ).toThrow();
    expect(() => decodeMarketHistory({ ...response, series: null }, instrument, "1W")).toThrow();
  });

  it.each(["0", "0.0000", "-13", "1e12", "0.0000000000001", "1000000000000000000", 100])(
    "rejects a close outside the decimal contract %s",
    (invalidClose) => {
      const bad = {
        ...response,
        series: {
          ...response.series,
          points: [{ ...response.series.points[0], close: invalidClose }],
        },
      };
      expect(() => decodeMarketHistory(bad, instrument, "1W")).toThrow();
    },
  );

  it.each([
    { source: "kraken" },
    { currency: "EUR" },
    { adjustment: "raw" },
    { interval_minutes: 60 },
    { as_of: "2026-12-24T15:00:00Z" },
    { timeliness: "delayed" },
    { points: [...response.series.points].reverse() },
    { points: response.series.points.map((point) => ({ ...point, gap_before: null })) },
    { points: Array.from({ length: 513 }, () => response.series.points[0]) },
  ])("rejects incompatible bounds or data %j", (change) => {
    expect(() =>
      decodeMarketHistory(
        { ...response, series: { ...response.series, ...change } },
        instrument,
        "1W",
      ),
    ).toThrow();
  });
});
