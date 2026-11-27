import { writeFile } from "node:fs/promises";
import { expect, type Page, type TestInfo } from "@playwright/test";

export const historyPath = "/api/v2/market-history/query";
export type HistoryQuery = {
  instrument:
    | { kind: "featured" | "crypto"; symbol: string }
    | { kind: "catalog"; catalog_id: string; listing_version: string };
  range: "1D" | "1W" | "1M";
};
type HistoryPoint = {
  starts_at: string;
  ends_at: string;
  close: string;
  gap_before: "closed" | "missing" | null;
};

const day = 86_400_000;
const epoch = Date.UTC(2026, 10, 25);
const days = { "1D": 1, "1W": 7, "1M": 30 };
const coinInterval = { "1D": 5, "1W": 60, "1M": 240 } as const;
const iso = (value: number) => new Date(value).toISOString();

export function historyReply(
  query: HistoryQuery,
  state: "ready" | "delayed" | "unavailable" = "ready",
) {
  if (state === "unavailable") return { ...query, state, series: null };
  const { instrument, range } = query;
  const crypto = instrument.kind === "crypto";
  const interval = crypto ? coinInterval[range] : range === "1D" ? 5 : 30;
  const step = interval * 60_000;
  const end = crypto ? epoch + day : epoch + 21 * 3_600_000;
  const start = crypto ? end - days[range] * day : epoch - (days[range] - 1) * day;
  const points: HistoryPoint[] = [];
  const base = crypto ? 66_000 : instrument.kind === "catalog" ? 200 : 84;
  function add(from: number, until: number, firstGap: HistoryPoint["gap_before"]) {
    for (let at = from; at + step <= until; at += step) {
      const change = points.length * 0.03 + Math.sin(points.length / 4);
      points.push({
        starts_at: iso(at),
        ends_at: iso(at + step),
        close: (base + change).toFixed(2),
        gap_before: at === from ? firstGap : null,
      });
    }
  }
  if (crypto) {
    add(start, end, null);
  } else {
    for (let session = start; session <= epoch; session += day) {
      const weekday = new Date(session).getUTCDay();
      if (weekday === 0 || weekday === 6) continue;
      const closeHour = session < Date.UTC(2026, 10, 1) ? 20 : 21;
      const close = session + closeHour * 3_600_000;
      add(close - 6.5 * 3_600_000, close, points.length ? "closed" : null);
    }
  }
  const delayed = state === "delayed";
  if (delayed) {
    points.splice(4, 1);
    points[4].gap_before = "missing";
    points.pop();
  }
  return {
    ...query,
    state: delayed ? "partial" : "ready",
    series: {
      source: crypto ? "kraken" : "alpaca_iex",
      currency: "USD",
      time_basis: crypto ? "utc" : "regular_session",
      adjustment: crypto ? "raw" : "split",
      interval_minutes: interval,
      start_at: iso(start),
      end_at: iso(end),
      expected_through_at: iso(end),
      as_of: points.at(-1)!.ends_at,
      timeliness: delayed ? "delayed" : "on_time",
      coverage: delayed ? "partial" : "complete",
      points,
      day_change_pct: delayed ? null : "1.96",
      period_change_pct: delayed ? null : "4.32",
    },
  };
}

export async function expectChartRange(page: Page, query: HistoryQuery) {
  const chart = page.getByRole("region", { name: "Price history" });
  const selected = chart.getByRole("button", { name: query.range, exact: true });
  await expect(selected).toHaveAttribute("aria-pressed", "true");
  const disclosure = chart.getByText("Price data", { exact: true });
  await expect(disclosure).toBeVisible();
  await disclosure.focus();
  await expect(disclosure).toBeFocused();
  await disclosure.press("Enter");
  const { series } = historyReply(query);
  const points = series!.points;
  const table = chart.getByRole("table");
  await expect(table.getByRole("row")).toHaveCount(points.length + 1);
  const last = table.getByRole("row").last();
  await expect(last.locator("time")).toHaveAttribute("datetime", points.at(-1)!.ends_at);
  await expect(last.getByRole("cell").last()).toHaveText(
    `$${Number(points.at(-1)!.close).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  );
  await disclosure.press("Enter");
}

export async function captureMarkets(page: Page, info: TestInfo, name: string) {
  await page.evaluate("document.fonts.ready.then(() => window.scrollTo(0, 0))");
  if (page.viewportSize()?.width === 1440) {
    const overflow = await page.evaluate<number>(
      "document.documentElement.scrollHeight - window.innerHeight",
    );
    expect(overflow).toBeLessThanOrEqual(1);
  }
  const selectors = [
    ".market-toolbar",
    ".market-workspace",
    ".market-list",
    ".market-stamp",
    ".market-detail",
    ".market-detail-heading",
    ".market-main-price",
    ".market-history-toolbar",
    ".market-history-plot",
    ".market-action-row",
    ".market-action-row a",
  ];
  const boxes = await Promise.all(
    selectors.map((selector) => page.locator(selector).first().boundingBox()),
  );
  expect(boxes.every(Boolean)).toBe(true);
  await writeFile(
    info.outputPath(`${name}.json`),
    JSON.stringify(
      Object.fromEntries(selectors.map((selector, index) => [selector, boxes[index]])),
      null,
      2,
    ),
  );
  await page.screenshot({
    path: info.outputPath(`${name}.png`),
    fullPage: true,
    animations: "disabled",
  });
}
