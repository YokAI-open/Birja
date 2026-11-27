import { expect, it, vi } from "vitest";
import { fetchPortfolioValueHistory, parsePortfolioValueHistory } from "./portfolioValueHistory";

const ids = ["2", "9007199254740993"];
const point = (day: string, total_value: string | null) => ({
  utc_day: day,
  captured_at: `${day}T22:00:00.123456Z`,
  total_value,
  valuation_complete: total_value !== null,
});
const payload = () => ({
  start_day: "2026-02-19",
  end_day: "2026-03-20",
  portfolios: [
    {
      portfolio_id: ids[0],
      points: [point("2026-02-19", "9007199254740993.01"), point("2026-02-21", null)],
    },
    { portfolio_id: ids[1], points: [point("2026-03-20", "0.00")] },
  ],
});

it("preserves exact owner IDs and prices, missing days and explicit null observations", () => {
  const value = payload();
  const decoded = parsePortfolioValueHistory(value, ids);
  expect(decoded).toEqual(value);
  expect(decoded.portfolios[0].points).toHaveLength(2);
});

it("rejects incorrect bounds, civil dates, membership and extra data", () => {
  const value = payload();
  const [first, second] = value.portfolios;
  const invalid = [
    { ...value, start_day: "2026-02-20" },
    { ...value, end_day: "2026-02-30" },
    { ...value, portfolios: [second, first] },
    { ...value, portfolios: [first, first] },
    { ...value, portfolios: [first] },
    { ...value, portfolios: [first, { ...second, portfolio_id: "9007199254740994" }] },
    { ...value, portfolios: [first, { ...second, portfolio_id: "09007199254740993" }] },
    {
      ...value,
      portfolios: Array.from({ length: 11 }, (_, index) => ({
        portfolio_id: String(index + 1),
        points: [],
      })),
    },
    { ...value, extra: true },
  ];
  for (const body of invalid) expect(() => parsePortfolioValueHistory(body, ids)).toThrow();
});

it("rejects impossible, duplicated, unordered, outside and oversized points", () => {
  const value = payload();
  const [first, second] = value.portfolios;
  const [p1, p2] = first.points;
  const invalid = [
    [p2, p1],
    [p1, p1],
    [point("2026-02-30", null)],
    [point("2026-02-18", null)],
    Array.from({ length: 31 }, () => p1),
    [{ ...p1, captured_at: "2026-02-20T00:01:00Z" }],
    [{ ...p1, captured_at: "2026-02-19T22:60:00Z" }],
    [{ ...p1, total_value: "2.000" }],
    [{ ...p1, total_value: "01.80" }],
    [{ ...p1, total_value: "-1.00" }],
    [{ ...p1, total_value: 1.0 }],
    [{ ...p1, total_value: null }],
    [{ ...p2, total_value: "1.00" }],
    [{ ...p2, valuation_complete: "false" }],
  ];
  for (const points of invalid)
    expect(() =>
      parsePortfolioValueHistory({ ...value, portfolios: [{ ...first, points }, second] }, ids),
    ).toThrow();
});

it("uses only the private history route and refuses a response after its scope expires", async () => {
  const response = Response.json(payload());
  let current = true;
  const fetch = vi.fn(async () => {
    current = false;
    return response;
  });
  vi.stubGlobal("fetch", fetch);
  try {
    const { signal } = new AbortController();
    await expect(fetchPortfolioValueHistory(ids, signal, () => current)).rejects.toMatchObject({
      name: "AbortError",
    });
    expect(fetch).toHaveBeenCalledWith(
      "/api/v2/portfolios/value-history",
      expect.objectContaining({ signal, cache: "no-store", credentials: "same-origin" }),
    );
    expect(response.bodyUsed).toBe(false);
  } finally {
    vi.unstubAllGlobals();
  }
});
