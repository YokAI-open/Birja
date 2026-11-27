import { guardedJsonRequest } from "./client";
import { isPortfolioId } from "./portfolios";
import { stockExact, stockRecord } from "./stockTrades";
import { stockTimestamp } from "./stocks";

export const PORTFOLIO_VALUE_DAYS = 30;
export const UTC_DAY_MS = 86_400_000;

export type PortfolioValuePoint = {
  utc_day: string;
  captured_at: string;
  total_value: string | null;
  valuation_complete: boolean;
};

export type PortfolioValueHistory = {
  start_day: string;
  end_day: string;
  portfolios: readonly {
    portfolio_id: string;
    points: readonly PortfolioValuePoint[];
  }[];
};

function isUtcDay(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !value.startsWith("0000-") &&
    stockTimestamp(`${value}T00:00:00Z`)
  );
}

function isValue(total: unknown, complete: unknown): boolean {
  if (complete === false) return total === null;
  return (
    complete === true && typeof total === "string" && /^(?:0|[1-9]\d{0,45})\.\d{2}$/.test(total)
  );
}

export function parsePortfolioValueHistory(
  value: unknown,
  expectedIds: readonly string[],
): PortfolioValueHistory {
  const invalid = (): never => {
    throw new Error("Unexpected portfolio value history");
  };
  if (
    !stockRecord(value) ||
    !stockExact(value, "start_day end_day portfolios") ||
    !isUtcDay(value.start_day) ||
    !isUtcDay(value.end_day) ||
    Date.parse(value.end_day) - Date.parse(value.start_day) !==
      (PORTFOLIO_VALUE_DAYS - 1) * UTC_DAY_MS ||
    !Array.isArray(value.portfolios) ||
    value.portfolios.length > 10 ||
    value.portfolios.length !== expectedIds.length
  )
    return invalid();
  const { start_day, end_day } = value;
  let previousId = 0n;
  const portfolios = value.portfolios.map((series: unknown, index) => {
    if (
      !stockRecord(series) ||
      !stockExact(series, "portfolio_id points") ||
      !isPortfolioId(series.portfolio_id) ||
      series.portfolio_id !== expectedIds[index] ||
      BigInt(series.portfolio_id) <= previousId ||
      !Array.isArray(series.points) ||
      series.points.length > PORTFOLIO_VALUE_DAYS
    )
      return invalid();
    previousId = BigInt(series.portfolio_id);
    let previousDay = "";
    const points = series.points.map((point: unknown): PortfolioValuePoint => {
      if (
        !stockRecord(point) ||
        !stockExact(point, "utc_day captured_at total_value valuation_complete") ||
        !isUtcDay(point.utc_day) ||
        point.utc_day <= previousDay ||
        point.utc_day < start_day ||
        point.utc_day > end_day ||
        !stockTimestamp(point.captured_at) ||
        point.captured_at.slice(0, 10) !== point.utc_day ||
        !isValue(point.total_value, point.valuation_complete)
      )
        return invalid();
      previousDay = point.utc_day;
      return Object.freeze(point as PortfolioValuePoint);
    });
    return Object.freeze({ portfolio_id: series.portfolio_id, points: Object.freeze(points) });
  });
  return Object.freeze({ start_day, end_day, portfolios: Object.freeze(portfolios) });
}

export async function fetchPortfolioValueHistory(
  expectedIds: readonly string[],
  signal: AbortSignal,
  isCurrent: () => boolean,
): Promise<PortfolioValueHistory> {
  const response = await guardedJsonRequest(
    "/api/v2/portfolios/value-history",
    { signal, cache: "no-store", credentials: "same-origin" },
    isCurrent,
  );
  return parsePortfolioValueHistory(response, expectedIds);
}
