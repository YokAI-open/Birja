import { act, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import MarketsPage from "./MarketsPage";

vi.mock("@/hooks/useStocks", () => ({
  useStocks: () => ({
    data: undefined,
    isPending: true,
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  }),
}));

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
  it("shows the curated coins in source order with formatted prices", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => ok(payload())),
    );
    renderWithClient(<MarketsPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
    const assets = await screen.findByRole("list", { name: "Crypto" });
    const rows = within(assets).getAllByRole("button");
    expect(rows).toHaveLength(15);
    expect(rows[0]).toHaveAccessibleName(/Bitcoin BTC.*81,042.35/);
    expect(rows[4]).toHaveAccessibleName(/Dogecoin DOGE.*0.07998/);
    expect(rows[11]).toHaveAccessibleName(/Cosmos ATOM.*1.01/);
    expect(rows[14]).toHaveAccessibleName(/Uniswap UNI/);
  });

  it("searches by name or symbol and only offers the selected asset action", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => ok(payload())),
    );
    const { user } = renderWithClient(<MarketsPage portfolioId="1" />);
    const search = screen.getByRole("searchbox", { name: "Search by name or symbol" });
    const trade = await screen.findByRole("link", { name: "Trade BTC" });
    expect(trade).toHaveAttribute("href", "/portfolios/1/trade/BTC");
    await user.type(search, "ethERE");
    const assets = screen.getByRole("list", { name: "Crypto" });
    expect(within(assets).getAllByRole("button")).toHaveLength(1);
    await user.click(within(assets).getByRole("button", { name: /Ethereum ETH/ }));
    expect(screen.getByRole("link", { name: "Trade ETH" })).toHaveAttribute(
      "href",
      "/portfolios/1/trade/ETH",
    );
    expect(screen.queryByRole("link", { name: "Trade BTC" })).toBeNull();
    await user.clear(search);
    await user.type(search, "DOGE");
    expect(within(assets).getByRole("button", { name: /Dogecoin DOGE/ })).toBeVisible();
    await user.type(search, "missing");
    expect(screen.getByText("No assets match your search.")).toBeVisible();
  });

  it("keeps asset intent in the unscoped trade route", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => ok(payload())),
    );
    renderWithClient(<MarketsPage />);
    expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/trade/BTC",
    );
  });

  it("shows a loading state while pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );
    renderWithClient(<MarketsPage />);
    expect(screen.getByText("Loading prices…")).toBeVisible();
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
    expect(await screen.findByText("Couldn’t load this market.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("list", { name: "Crypto" })).toBeVisible();
  });

  it("keeps the last prices with a warning when a background refetch fails", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let calls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => {
        calls += 1;
        return calls === 2 ? Promise.resolve(new Response("{}", { status: 502 })) : ok(payload());
      }),
    );
    renderWithClient(<MarketsPage />);
    await screen.findByRole("list", { name: "Crypto" });
    expect(screen.queryByText(/Couldn’t refresh/)).toBeNull();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(calls).toBe(2);
    expect(
      await screen.findByText("Couldn’t refresh. Showing the last available update."),
    ).toBeVisible();
    const table = screen.getByRole("list", { name: "Crypto" });
    expect(within(table).getAllByRole("button")).toHaveLength(15);
    expect(within(table).getByText("$81,042.35")).toBeVisible();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(calls).toBe(3);
    await vi.waitFor(() => {
      expect(screen.queryByText(/Couldn’t refresh/)).toBeNull();
    });
    expect(screen.getByRole("list", { name: "Crypto" })).toBeVisible();
  });

  it("shows only the full error, no refresh warning, when nothing ever loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response("{}", { status: 500 }))),
    );
    renderWithClient(<MarketsPage />);
    expect(await screen.findByText("Couldn’t load this market.")).toBeVisible();
    expect(screen.queryByText(/Couldn’t refresh/)).toBeNull();
    expect(screen.queryByRole("list", { name: "Crypto" })).toBeNull();
  });

  it("refetches every 30 seconds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const fetchMock = vi.fn(() => ok(payload()));
    vi.stubGlobal("fetch", fetchMock);
    renderWithClient(<MarketsPage />);
    await screen.findByRole("list", { name: "Crypto" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  describe("freshness", () => {
    const aged = (ages: [string, number, string][]) => ({
      server_time: "2026-10-28T10:00:00Z",
      fresh_seconds: 120,
      stale_seconds: 300,
      items: ages.map(([symbol, age, status]) => ({
        symbol,
        name: symbol,
        price: "1.00000000",
        as_of: "2026-10-28T09:59:50Z",
        age_seconds: age,
        status,
      })),
    });
    const tick = (ms: number) =>
      act(async () => {
        await vi.advanceTimersByTimeAsync(ms);
      });

    it("flags delayed and stale prices and shows selected freshness", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      vi.stubGlobal(
        "fetch",
        vi.fn(() =>
          ok(
            aged([
              ["BTC", 42, "fresh"],
              ["DOGE", 150, "aging"],
              ["ATOM", 420, "stale"],
            ]),
          ),
        ),
      );
      renderWithClient(<MarketsPage />);
      expect(await screen.findByText("Updated 42s ago")).toBeVisible();
      expect(screen.getByText("Delayed")).toBeVisible();
      expect(screen.getByText("Stale")).toBeVisible();
      expect(screen.getByRole("link", { name: "Trade BTC" })).toBeVisible();
    });

    it("ticks ages and recomputes status from API thresholds", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      vi.stubGlobal(
        "fetch",
        vi.fn(() =>
          ok(
            aged([
              ["BTC", 42, "fresh"],
              ["ETH", 115, "fresh"],
            ]),
          ),
        ),
      );
      renderWithClient(<MarketsPage />);
      await screen.findByText("Updated 42s ago");
      await tick(10_000);
      expect(screen.getByText("Updated 52s ago")).toBeVisible();
      expect(screen.getByText("Delayed")).toBeVisible();
    });

    it("resets after a refetch", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      let calls = 0;
      vi.stubGlobal(
        "fetch",
        vi.fn(() => {
          calls += 1;
          return ok(aged([["BTC", calls === 1 ? 42 : 3, "fresh"]]));
        }),
      );
      renderWithClient(<MarketsPage />);
      await screen.findByText("Updated 42s ago");
      await tick(30_000);
      expect(await screen.findByText(/^Updated [0-9]s ago$/)).toBeVisible();
    });
  });
});
