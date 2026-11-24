import { useEffect, type ReactNode } from "react";
import { focusManager, useQueryClient } from "@tanstack/react-query";
import { act, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CatalogQuoteView, StockCatalogItem } from "@/api/stockCatalog";
import type { StockItem } from "@/api/stocks";
import { renderWithClient } from "@/test/render";
import MarketsPage from "./MarketsPage";

const stockFixtures = vi.hoisted(() => ({ useStocks: vi.fn() }));
vi.mock("@/hooks/useStocks", () => stockFixtures);
beforeEach(() => {
  stockFixtures.useStocks.mockReturnValue({
    data: undefined,
    isPending: true,
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  focusManager.setFocused(undefined);
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

function SignedIn({ children }: { children: ReactNode }) {
  const client = useQueryClient();
  useEffect(() => {
    client.setQueryDefaults(["me"], { gcTime: Infinity });
    client.setQueryData(["me"], { email: "stocks@example.invalid" });
  }, [client]);
  return children;
}

const listing = (catalog_id = "9007199254740993", ticker = "FQA"): StockCatalogItem => ({
  catalog_id,
  ticker,
  listing_version: "17",
  company_name: "Fixture Company",
  listing_exchange: "NASDAQ",
  share_class: "A",
  state: "active",
  reason: "corroborated_share_class",
});

const catalog = (items: StockCatalogItem[], has_more = false) => ({
  state: "ready",
  generation_id: "11",
  published_at: "2026-11-24T00:00:00Z",
  has_more,
  items,
});

const iso = (value: number) => new Date(value).toISOString();

function displayed(item: StockCatalogItem, now: number, closed = false): CatalogQuoteView {
  const event = now - (closed ? 150_000 : 30_000);
  return {
    listing: item,
    reason: closed ? "market_closed" : "ready",
    read_only: true,
    execution_reason: closed ? "market_closed" : "read_only",
    session: {
      state: closed ? "closed" : "open",
      opens_at: iso(now - 600_000),
      closes_at: iso(closed ? now - 10_000 : now + 60_000),
      next_open_at: iso(now + 3_590_000),
    },
    quote: {
      bid: "10.1",
      ask: "10.3",
      mid: "10.20000000",
      event_at: iso(event),
      collected_at: iso(event + 1000),
      valid_until: iso(now + 3_000),
      source: "alpaca",
      feed: "iex",
      currency: "USD",
    },
  };
}

function catalogOk(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stockFetch(
  search: (term: string, init: RequestInit) => Response | Promise<Response>,
  quote: (path: string, init: RequestInit) => Response | Promise<Response> = () => {
    throw new Error("Unexpected automatic catalog price");
  },
) {
  return vi.fn(async (url: string, init: RequestInit) => {
    if (url === "/api/v1/auth/csrf") {
      document.cookie = "bj_csrf=fixture-token";
      return new Response(null, { status: 204 });
    }
    if (url.startsWith("/api/v1/stock-catalog/search"))
      return search(new URL(url, "https://fixture.invalid").searchParams.get("q") ?? "", init);
    if (url.startsWith("/api/v2/stock-catalog/")) return quote(url, init);
    return ok(payload());
  });
}

async function openCatalog(portfolioId?: string) {
  const rendered = renderWithClient(
    <SignedIn>
      <MarketsPage portfolioId={portfolioId} />
    </SignedIn>,
  );
  await rendered.user.click(screen.getByRole("button", { name: "US stocks" }));
  return { ...rendered, search: screen.getByRole("searchbox", { name: "Search stocks" }) };
}

describe("MarketsPage stock catalog", () => {
  it("prices only a keyboard-selected result and keeps its bigint identity in the owned route", async () => {
    const stock = listing();
    const request = vi.fn(() => catalogOk(displayed(stock, Date.now())));
    const search = vi.fn(() => catalogOk(catalog([stock])));
    const fetchMock = stockFetch(search, request);
    vi.stubGlobal("fetch", fetchMock);
    const page = await openCatalog("50");
    expect(search).not.toHaveBeenCalled();
    await page.user.type(page.search, "F");
    const row = await screen.findByRole("button", {
      name: /Fixture Company FQA · NASDAQ · Class A/,
    });
    expect(search).toHaveBeenCalledTimes(1);
    expect(search).toHaveBeenCalledWith("F", expect.anything());
    expect(request).not.toHaveBeenCalled();
    row.focus();
    await page.user.keyboard("{Enter}");
    expect(await screen.findByText("$10.20")).toBeVisible();
    expect(screen.getByText(/IEX midpoint/)).toBeVisible();
    expect(screen.getByRole("link", { name: "View details FQA" })).toHaveAttribute(
      "href",
      "/portfolios/50/trade/catalog/9007199254740993",
    );
    const [, init] = fetchMock.mock.calls.find(([url]) => url.endsWith("/quote"))!;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ listing_version: "17" }));
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("fixture-token");
  });

  it("waits for IME composition, limits the result list and shows settled empty feedback", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const rows = Array.from({ length: 20 }, (_, i) => listing(String(i + 1), `FQ${i}`));
    const search = vi.fn((term: string) =>
      catalogOk(catalog(term === "株" ? rows : [], term === "株")),
    );
    vi.stubGlobal("fetch", stockFetch(search));
    renderWithClient(
      <SignedIn>
        <MarketsPage />
      </SignedIn>,
    );
    fireEvent.click(screen.getByRole("button", { name: "US stocks" }));
    const input = screen.getByRole("searchbox", { name: "Search stocks" });
    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "株" } });
    await act(async () => vi.advanceTimersByTimeAsync(300));
    expect(search).not.toHaveBeenCalled();
    fireEvent.compositionEnd(input);
    await act(async () => vi.advanceTimersByTimeAsync(300));
    const results = await screen.findByRole("list", { name: "US stocks" });
    expect(within(results).getAllByRole("button")).toHaveLength(20);
    expect(screen.getByText("More than 20 stocks match. Refine your search.")).toBeVisible();
    expect(search).toHaveBeenCalledTimes(1);
    fireEvent.change(input, { target: { value: "missing" } });
    await act(async () => vi.advanceTimersByTimeAsync(300));
    expect(
      await screen.findByText("No matching stocks. Try another name or ticker."),
    ).toBeVisible();
  });

  it("offers Trade for the eligible listing only while its quote remains current", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const stock = listing();
    const request = vi.fn(() =>
      catalogOk({
        ...displayed(stock, Date.now()),
        read_only: false,
        execution_reason: "available",
      }),
    );
    vi.stubGlobal(
      "fetch",
      stockFetch(() => catalogOk(catalog([stock])), request),
    );
    renderWithClient(
      <SignedIn>
        <MarketsPage portfolioId="51" />
      </SignedIn>,
    );
    fireEvent.click(screen.getByRole("button", { name: "US stocks" }));
    fireEvent.change(screen.getByRole("searchbox", { name: "Search stocks" }), {
      target: { value: "FQA" },
    });
    await act(async () => vi.advanceTimersByTimeAsync(300));
    fireEvent.click(await screen.findByRole("button", { name: /FQA/ }));
    const href = "/portfolios/51/trade/catalog/9007199254740993";
    expect(await screen.findByRole("link", { name: "Trade FQA" })).toHaveAttribute("href", href);
    await act(async () => vi.advanceTimersByTimeAsync(4_000));
    expect(screen.queryByRole("link", { name: "Trade FQA" })).toBeNull();
    expect(screen.getByRole("link", { name: "View details FQA" })).toHaveAttribute("href", href);
  });

  it("cancels a previous quote and keeps the selected listing through provider failure", async () => {
    const first = listing("71", "FQA");
    const second = { ...listing("72", "FQB"), share_class: "B" };
    let completeFirst!: (value: Response) => void;
    let firstSignal: AbortSignal | null | undefined;
    const request = vi.fn((path: string, init: RequestInit) => {
      if (path.endsWith("/71/quote")) {
        firstSignal = init.signal;
        return new Promise<Response>((done) => {
          completeFirst = done;
        });
      }
      const view = displayed(second, Date.now());
      return catalogOk({ ...view, quote: null, reason: "source_error" });
    });
    vi.stubGlobal(
      "fetch",
      stockFetch(() => catalogOk(catalog([first, second])), request),
    );
    const page = await openCatalog();
    await page.user.type(page.search, "Fixture");
    await page.user.click(await screen.findByRole("button", { name: /FQA/ }));
    await vi.waitFor(() => expect(firstSignal).toBeDefined());
    expect(screen.queryByRole("link", { name: "View details FQA" })).toBeNull();
    await page.user.click(screen.getByRole("button", { name: /FQB/ }));
    expect(await screen.findByText("Couldn’t load this stock price.")).toBeVisible();
    expect(firstSignal?.aborted).toBe(true);
    await act(async () => completeFirst(catalogOk(displayed(first, Date.now()))));
    expect(screen.queryByText("$10.20")).toBeNull();
    expect(screen.getByRole("link", { name: "View details FQB" })).toHaveAttribute(
      "href",
      "/trade/catalog/72",
    );
    await page.user.click(screen.getByRole("button", { name: "Retry price" }));
    await vi.waitFor(() => expect(request).toHaveBeenCalledTimes(3));
    await page.user.click(screen.getByRole("button", { name: "Crypto" }));
    expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/trade/BTC",
    );
  });

  it("keeps a permitted cached mark while closed, clears it at the deadline and restores focus", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => ({ matches: true })),
    );
    const stock = listing();
    const request = vi.fn(() => catalogOk(displayed(stock, Date.now(), true)));
    vi.stubGlobal(
      "fetch",
      stockFetch(() => catalogOk(catalog([stock])), request),
    );
    renderWithClient(
      <SignedIn>
        <MarketsPage />
      </SignedIn>,
    );
    fireEvent.click(screen.getByRole("button", { name: "US stocks" }));
    const input = screen.getByRole("searchbox", { name: "Search stocks" });
    fireEvent.change(input, { target: { value: "FQA" } });
    await act(async () => vi.advanceTimersByTimeAsync(300));
    const row = await screen.findByRole("button", { name: /FQA/ });
    fireEvent.click(row);
    expect(await screen.findByText("Market closed")).toBeVisible();
    expect(screen.getByText("Opens in 1 hr")).toBeVisible();
    const price = screen.getByText("$10.20");
    expect(price).toBeVisible();
    expect(price.querySelector("time.sr-only")).toHaveAttribute("datetime", expect.any(String));
    expect(screen.queryByText(/IEX midpoint/)).toBeNull();
    await act(async () => vi.advanceTimersByTimeAsync(4_000));
    expect(screen.queryByText("$10.20")).toBeNull();
    expect(screen.getByText("Market closed")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Fixture Company" })).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "All assets" }));
    await act(async () => vi.advanceTimersByTimeAsync(32));
    expect(row).toHaveFocus();
    expect(input).toHaveValue("FQA");
    expect(request).toHaveBeenCalledTimes(1);
  });
});

it("keeps curated stock search and its own ticket when the catalog is unavailable", async () => {
  const closed: StockItem = {
    id: 1,
    symbol: "AAPL",
    company_name: "Apple",
    currency: "USD",
    listing_exchange: "NASDAQ",
    quote: null,
    session: {
      state: "closed",
      opens_at: null,
      closes_at: null,
      next_open_at: null,
      valid_until: null,
      timezone: "America/New_York",
    },
    status: { state: "unknown", observed_at: null, valid_until: null },
    action: { state: "current", reason: "none", epoch: 1, checked_at: null, valid_until: null },
    valuation_reason: "quote_unavailable",
    execution_reason: "market_closed",
    execution_enabled: false,
    quote_reason: "session_unavailable",
    session_reason: "closed",
    status_reason: "unknown",
  };
  stockFixtures.useStocks.mockReturnValue({
    data: { items: [closed], admission: { state: "approved" } },
    isPending: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  });
  const discovered = listing("400", "AAPL");
  const quote = vi.fn(() =>
    catalogOk({
      ...displayed(discovered, Date.now()),
      quote: null,
      reason: "mapping_review",
    }),
  );
  let admitted = false;
  const search = vi.fn(() =>
    catalogOk(
      admitted
        ? catalog([discovered])
        : {
            state: "unavailable",
            generation_id: null,
            published_at: null,
            items: [],
            has_more: false,
          },
    ),
  );
  vi.stubGlobal("fetch", stockFetch(search, quote));
  const page = await openCatalog();
  const original = screen.getByRole("link", { name: "View details AAPL" });
  expect(original).toHaveAttribute("href", "/trade/stocks/AAPL");
  expect(search).not.toHaveBeenCalled();
  await page.user.type(page.search, "Apple");
  expect(await screen.findByText(/Catalog search is unavailable/)).toBeVisible();
  expect(screen.getByRole("button", { name: /Apple AAPL/ })).toBeVisible();
  expect(screen.getByRole("link", { name: "View details AAPL" })).toHaveAttribute(
    "href",
    "/trade/stocks/AAPL",
  );
  expect(quote).not.toHaveBeenCalled();

  admitted = true;
  await page.user.click(screen.getByRole("button", { name: "Try stock search again" }));
  await page.user.click(await screen.findByRole("button", { name: /Fixture Company AAPL/ }));
  expect(await screen.findByText(/reference data is under review/)).toBeVisible();
  expect(screen.getByRole("link", { name: "View details AAPL" })).toHaveAttribute(
    "href",
    "/trade/catalog/400",
  );
  admitted = false;
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
  });
  expect(await screen.findByText(/Catalog search is unavailable/)).toBeVisible();
  expect(screen.queryByRole("link", { name: "View details AAPL" })).toBeNull();
  await page.user.click(screen.getByRole("button", { name: /Apple AAPL/ }));
  expect(screen.getByRole("link", { name: "View details AAPL" })).toHaveAttribute(
    "href",
    "/trade/stocks/AAPL",
  );
});
