import { act, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import MarketsPage from "./MarketsPage";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const COINS: [string, string, string][] = [
  ["BTC", "Bitcoin", "81042.35000000"],
  ["ETH", "Ethereum", "3200.10000000"],
  ["SOL", "Solana", "150.00000000"],
  ["XRP", "XRP", "0.52000000"],
  ["DOGE", "Dogecoin", "0.07998070"],
  ["ADA", "Cardano", "0.33080000"],
  ["AVAX", "Avalanche", "35.40000000"],
  ["DOT", "Polkadot", "6.01000000"],
  ["LINK", "Chainlink", "14.20000000"],
  ["LTC", "Litecoin", "70.00000000"],
  ["BCH", "Bitcoin Cash", "400.00000000"],
  ["ATOM", "Cosmos", "1.00800000"],
  ["XLM", "Stellar", "0.20663000"],
  ["TRX", "TRON", "0.12000000"],
  ["UNI", "Uniswap", "8.00000000"],
];

const payload = (items = COINS) => ({
  server_time: "2026-10-28T10:00:00Z",
  fresh_seconds: 90,
  stale_seconds: 300,
  items: items.map(([symbol, name, price]) => ({
    symbol,
    name,
    price,
    as_of: "2026-10-28T09:59:50Z",
    age_seconds: 10,
    status: "fresh",
  })),
});

const ok = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body)));

describe("MarketsPage", () => {
  it("renders one row per coin in order with formatted prices", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => ok(payload())),
    );
    renderWithClient(<MarketsPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
    const table = await screen.findByRole("table", { name: "Markets" });
    const rows = within(table).getAllByRole("row").slice(1);
    expect(rows).toHaveLength(15);
    expect(within(rows[0]!).getByText("BTC")).toBeVisible();
    expect(within(rows[0]!).getByText("Bitcoin")).toBeVisible();
    expect(within(rows[0]!).getByText("$81,042.35")).toBeVisible();
    expect(within(rows[4]!).getByText("$0.07998")).toBeVisible();
    expect(within(rows[11]!).getByText("$1.01")).toBeVisible();
    expect(within(rows[14]!).getByText("UNI")).toBeVisible();
  });

  it("shows a loading state while pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );
    renderWithClient(<MarketsPage />);
    expect(screen.getByRole("status", { name: "Loading prices" })).toBeVisible();
  });

  it("shows the empty message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => ok(payload([]))),
    );
    renderWithClient(<MarketsPage />);
    expect(
      await screen.findByText("Prices are loading. They appear within a minute."),
    ).toBeVisible();
  });

  it("shows an error and retries", async () => {
    let calls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => {
        calls += 1;
        return calls === 1 ? Promise.resolve(new Response("{}", { status: 500 })) : ok(payload());
      }),
    );
    const { user } = renderWithClient(<MarketsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Can't load prices right now.");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("table", { name: "Markets" })).toBeVisible();
  });

  it("refetches every 30 seconds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi.fn(() => ok(payload()));
    vi.stubGlobal("fetch", fetchMock);
    renderWithClient(<MarketsPage />);
    await screen.findByRole("table", { name: "Markets" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
