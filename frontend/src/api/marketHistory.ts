import { guardedJsonRequest } from "./client";
import { isCanonicalUtcTimestamp as stamp, isCatalogId } from "./stockCatalog";

export const historyRanges = ["1D", "1W", "1M"] as const;
export type HistoryRange = (typeof historyRanges)[number];
export type HistoryInstrument =
  | { kind: "crypto" | "featured"; symbol: string }
  | { kind: "catalog"; catalog_id: string; listing_version: string };

export type HistoryPoint = {
  starts_at: string;
  ends_at: string;
  close: string;
  gap_before: "missing" | "closed" | null;
};

export type HistorySeries = {
  source: "kraken" | "alpaca_iex";
  currency: "USD";
  time_basis: "utc" | "regular_session";
  adjustment: "raw" | "split";
  interval_minutes: 5 | 30 | 60 | 240;
  start_at: string;
  end_at: string;
  expected_through_at: string | null;
  as_of: string | null;
  timeliness: "on_time" | "delayed" | "unknown";
  coverage: "complete" | "partial" | "empty";
  points: HistoryPoint[];
  day_change_pct: string | null;
  period_change_pct: string | null;
};

export type HistoryResponse = {
  instrument: HistoryInstrument;
  range: HistoryRange;
} & (
  | { state: "ready" | "partial" | "empty"; series: HistorySeries }
  | { state: "pending" | "unavailable"; series: null }
);

const cryptoIntervals = { "1D": 5, "1W": 60, "1M": 240 } as const;
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const keys = (value: Record<string, unknown>, ...fields: string[]) =>
  Object.keys(value).length === fields.length && fields.every((key) => Object.hasOwn(value, key));
const close = (value: unknown): value is string =>
  typeof value === "string" &&
  /^(?:0|[1-9]\d{0,17})(?:\.\d{1,12})?$/.test(value) &&
  /[1-9]/.test(value);
const percent = (value: unknown): value is string | null =>
  value === null || (typeof value === "string" && /^-?\d{1,32}(?:\.\d{1,2})?$/.test(value));

function isInstrument(value: unknown): value is HistoryInstrument {
  if (!record(value)) return false;
  if (value.kind === "catalog") {
    return (
      keys(value, "kind", "catalog_id", "listing_version") &&
      isCatalogId(value.catalog_id) &&
      isCatalogId(value.listing_version)
    );
  }
  return (
    (value.kind === "crypto" || value.kind === "featured") &&
    keys(value, "kind", "symbol") &&
    typeof value.symbol === "string" &&
    /^[A-Z0-9][A-Z0-9.\-/]{0,13}$/.test(value.symbol)
  );
}

export function historyInstrumentKey(instrument: HistoryInstrument): string {
  return instrument.kind === "catalog"
    ? `catalog:${instrument.catalog_id}:${instrument.listing_version}`
    : `${instrument.kind}:${instrument.symbol}`;
}

function isPoint(value: unknown): value is HistoryPoint {
  return (
    record(value) &&
    keys(value, "starts_at", "ends_at", "close", "gap_before") &&
    stamp(value.starts_at) &&
    stamp(value.ends_at) &&
    close(value.close) &&
    (value.gap_before === null || value.gap_before === "missing" || value.gap_before === "closed")
  );
}

function isSeries(
  value: unknown,
  instrument: HistoryInstrument,
  range: HistoryRange,
  coverage: HistorySeries["coverage"],
): value is HistorySeries {
  const crypto = instrument.kind === "crypto";
  const interval = crypto ? cryptoIntervals[range] : range === "1D" ? 5 : 30;
  if (
    !record(value) ||
    !keys(
      value,
      "source",
      "currency",
      "time_basis",
      "adjustment",
      "interval_minutes",
      "start_at",
      "end_at",
      "expected_through_at",
      "as_of",
      "timeliness",
      "coverage",
      "points",
      "day_change_pct",
      "period_change_pct",
    ) ||
    value.source !== (crypto ? "kraken" : "alpaca_iex") ||
    value.currency !== "USD" ||
    value.time_basis !== (crypto ? "utc" : "regular_session") ||
    value.adjustment !== (crypto ? "raw" : "split") ||
    value.interval_minutes !== interval ||
    value.coverage !== coverage ||
    !stamp(value.start_at) ||
    !stamp(value.end_at) ||
    (value.as_of !== null && !stamp(value.as_of)) ||
    (value.expected_through_at !== null && !stamp(value.expected_through_at)) ||
    !percent(value.day_change_pct) ||
    !percent(value.period_change_pct) ||
    !Array.isArray(value.points) ||
    value.points.length > 512 ||
    (value.points.length === 0) !== (coverage === "empty")
  )
    return false;

  const start = Date.parse(value.start_at);
  const end = Date.parse(value.end_at);
  const expected =
    value.expected_through_at === null ? null : Date.parse(value.expected_through_at);
  if (start > end || (expected !== null && (expected < start || expected > end))) return false;
  let previousEnd: number | null = null;
  for (const point of value.points as unknown[]) {
    if (!isPoint(point)) return false;
    const starts = Date.parse(point.starts_at);
    const ends = Date.parse(point.ends_at);
    if (
      starts < start ||
      ends > end ||
      ends - starts !== interval * 60_000 ||
      (crypto && point.gap_before === "closed") ||
      (point.gap_before === "missing" && coverage === "complete") ||
      (previousEnd !== null &&
        (starts < previousEnd || starts > previousEnd !== (point.gap_before !== null))) ||
      (previousEnd === null && point.gap_before === "closed")
    )
      return false;
    previousEnd = ends;
  }

  const asOf = value.as_of === null ? null : Date.parse(value.as_of);
  const timeliness =
    asOf === null || expected === null ? "unknown" : asOf < expected ? "delayed" : "on_time";
  return (
    previousEnd === asOf &&
    value.timeliness === timeliness &&
    (timeliness === "on_time" ||
      (value.day_change_pct === null && value.period_change_pct === null)) &&
    (coverage === "complete" || value.period_change_pct === null)
  );
}

export function decodeMarketHistory(
  value: unknown,
  instrument: HistoryInstrument,
  range: HistoryRange,
): HistoryResponse {
  if (
    record(value) &&
    keys(value, "instrument", "range", "state", "series") &&
    value.range === range &&
    isInstrument(value.instrument) &&
    historyInstrumentKey(value.instrument) === historyInstrumentKey(instrument)
  ) {
    const { state, series } = value;
    if ((state === "pending" || state === "unavailable") && series === null)
      return { instrument, range, state, series };
    if (state === "ready" || state === "partial" || state === "empty") {
      if (isSeries(series, instrument, range, state === "ready" ? "complete" : state))
        return { instrument, range, state, series };
    }
  }
  throw new Error("Unexpected market history response");
}

export async function requestMarketHistory(
  instrument: HistoryInstrument,
  range: HistoryRange,
  signal: AbortSignal,
  current: () => boolean,
) {
  if (!isInstrument(instrument)) throw new Error("Invalid market history instrument");
  const value = await new Promise<unknown>((resolve, reject) => {
    signal.throwIfAborted();
    // A chart can stop waiting while the shared session refresh finishes for other requests.
    const abort = () => reject(signal.reason);
    signal.addEventListener("abort", abort, { once: true });
    void guardedJsonRequest(
      "/api/v2/market-history/query",
      { method: "POST", body: JSON.stringify({ instrument, range }), signal },
      current,
    )
      .then(resolve, reject)
      .finally(() => signal.removeEventListener("abort", abort));
  });
  return decodeMarketHistory(value, instrument, range);
}
