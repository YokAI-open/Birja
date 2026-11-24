import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import App from "@/App";
import type { CatalogTradeContext } from "@/api/stockCatalog";
import { cashPortfolio } from "@/test/portfolioFixtures";

const catalogId = "9007199254741002";
const contextPath = (portfolioId: string) =>
  `/api/v2/portfolios/${portfolioId}/stock-catalog/${catalogId}/trade-context`;
const ticketPath = (portfolioId: string) => `/portfolios/${portfolioId}/trade/catalog/${catalogId}`;
const first = { id: "1", name: "My portfolio" };
const second = { id: "2", name: "Income portfolio" };
const now = Date.parse("2026-11-24T15:00:00Z");
const at = (seconds: number) => new Date(now + seconds * 1000).toISOString();

function ticket(portfolioId = "1"): CatalogTradeContext {
  return {
    portfolio_id: portfolioId,
    read_only: true,
    listing: {
      catalog_id: catalogId,
      listing_version: "9007199254741003",
      ticker: "FQA",
      company_name: "Fixture Aerospace",
      listing_exchange: "NASDAQ",
      share_class: "A",
      state: "active",
      reason: "corroborated_share_class",
    },
    session: {
      state: "open",
      opens_at: at(-1800),
      closes_at: at(7200),
      next_open_at: at(84600),
    },
    quote: {
      bid: "150.00",
      ask: "151.00",
      mid: "150.50",
      event_at: at(-8),
      collected_at: at(-7),
      valid_until: at(500),
      source: "alpaca",
      feed: "iex",
      currency: "USD",
    },
    reason: "ready",
  };
}

const clients: QueryClient[] = [];
function Location() {
  return <p data-testid="location">{useLocation().pathname}</p>;
}

function setup({
  route = ticketPath("1"),
  portfolios = [first, second],
  context = (id: string) => Response.json(ticket(id)),
}: {
  route?: string;
  portfolios?: (typeof first)[];
  context?: (id: string) => Response | Promise<Response>;
} = {}) {
  vi.spyOn(Date, "now").mockReturnValue(now);
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (init?.method && init.method !== "GET") return Response.json({}, { status: 405 });
    if (path === "/api/v2/me") return Response.json({ email: "owner@example.test" });
    if (path === "/api/v2/portfolios") return Response.json(portfolios);
    for (const portfolio of portfolios) {
      if (path === contextPath(portfolio.id)) return context(portfolio.id);
      if (path === `/api/v2/portfolios/${portfolio.id}`) {
        const cash = portfolio.id === "1" ? "10000.00" : "2500.00";
        return Response.json({
          ...cashPortfolio(),
          portfolio_id: portfolio.id,
          name: portfolio.name,
          cash,
          starting_cash: cash,
          total_value: cash,
          known_value: cash,
          class_values: { cash, stocks: "0.00", crypto: "0.00" },
          valued_at: at(0),
        });
      }
    }
    return Response.json({}, { status: 404 });
  });
  vi.stubGlobal("fetch", fetch);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <Location />
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { fetch, user: userEvent.setup() };
}

function readOnly(fetch: ReturnType<typeof setup>["fetch"]) {
  expect(
    screen.queryByRole("button", { name: /preview|confirm|buy|sell/i }),
  ).not.toBeInTheDocument();
  expect(fetch.mock.calls.every(([, init]) => !init?.method || init.method === "GET")).toBe(true);
  expect(fetch.mock.calls.some(([path]) => String(path).includes("/stock-trades"))).toBe(false);
}

afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

it("opens an explicit owned stock and keeps the exact listing on portfolio switch", async () => {
  const { user, fetch } = setup();
  const heading = await screen.findByRole("heading", { name: "Fixture Aerospace" });
  expect(heading).toHaveFocus();
  expect(screen.getByText("FQA · NASDAQ · Class A")).toBeVisible();
  expect(screen.getByText("$150.50")).toBeVisible();
  expect(screen.getByText(/IEX price/)).toContainElement(screen.getByTitle(at(-8)));
  expect(await screen.findAllByText("Cash available $10,000.00")).toHaveLength(1);
  const chooser = screen.getByRole("combobox", { name: "Trading portfolio" });
  expect(chooser).toHaveValue("1");
  await user.selectOptions(chooser, "2");
  expect(await screen.findByText("Cash available $2,500.00")).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("2"));
  expect(screen.queryByText("Cash available $10,000.00")).not.toBeInTheDocument();
  expect(fetch.mock.calls.map(([path]) => path)).toEqual(
    expect.arrayContaining([contextPath("1"), contextPath("2")]),
  );
  readOnly(fetch);
});

it("leaves a new user with no active portfolio at the browse boundary", async () => {
  const { fetch } = setup({ route: `/trade/catalog/${catalogId}`, portfolios: [] });
  expect(await screen.findByRole("heading", { name: "No portfolio available" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Browse markets" })).toHaveAttribute("href", "/");
  expect(fetch.mock.calls.map(([path]) => String(path))).not.toContain(contextPath("1"));
  readOnly(fetch);
});

it("opens the only portfolio through its owned route", async () => {
  const { fetch } = setup({ route: `/trade/catalog/${catalogId}`, portfolios: [first] });
  expect(await screen.findByRole("heading", { name: "Fixture Aerospace" })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("1"));
  readOnly(fetch);
});

it("requires an explicit portfolio choice when more than one is active", async () => {
  const { user, fetch } = setup({ route: `/trade/catalog/${catalogId}` });
  expect(await screen.findByRole("heading", { name: "Portfolio required" })).toBeVisible();
  expect(fetch.mock.calls.map(([path]) => path)).not.toContain(contextPath("1"));
  expect(fetch.mock.calls.map(([path]) => path)).not.toContain(contextPath("2"));
  await user.selectOptions(screen.getByRole("combobox", { name: "Trading portfolio" }), "2");
  expect(await screen.findByRole("heading", { name: "Fixture Aerospace" })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("2"));
  readOnly(fetch);
});

it.each(["3", "4"])("refuses an inaccessible portfolio route scoped to %s", async (id) => {
  const { fetch } = setup({ route: ticketPath(id) });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath(id));
  expect(fetch.mock.calls.map(([path]) => path)).not.toContain(contextPath(id));
  readOnly(fetch);
});

it("keeps the owned URL when the portfolio closes before the server reads the ticket", async () => {
  const portfolios = [first, second];
  const { fetch } = setup({
    portfolios,
    context: () => {
      portfolios.shift();
      return Response.json({ detail: { code: "portfolio_unavailable" } }, { status: 404 });
    },
  });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("1"));
  expect(screen.queryByText("Cash available $10,000.00")).not.toBeInTheDocument();
  readOnly(fetch);
});

it("keeps a retired reused ticker on its original catalog link", async () => {
  const closed = ticket();
  closed.listing = {
    ...closed.listing,
    ticker: "AAPL",
    company_name: "Original Aerospace",
    state: "retired",
    reason: "verified_ticker_reuse",
  };
  closed.quote = null;
  closed.reason = "identity_review";
  const { fetch } = setup({ context: () => Response.json(closed) });
  expect(await screen.findByRole("heading", { name: "Original Aerospace" })).toBeVisible();
  expect(screen.getByText("This listing is no longer active.")).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("1"));
  readOnly(fetch);
});

it("shows a permitted closed-market mark and opening countdown", async () => {
  const closed = ticket();
  closed.session = {
    state: "closed",
    opens_at: at(-3600),
    closes_at: at(-120),
    next_open_at: at(6300),
  };
  closed.quote = {
    ...closed.quote!,
    event_at: at(-180),
    collected_at: at(-180),
    valid_until: at(60),
  };
  closed.reason = "market_closed";
  const { fetch } = setup({ context: () => Response.json(closed) });
  expect(await screen.findByText("Opens in 1 hr 45 min")).toBeVisible();
  expect(screen.getByText(/Market closed/)).toBeVisible();
  expect(screen.getByText("$150.50")).toBeVisible();
  expect(screen.queryByText(/IEX price/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Orders aren't available/)).not.toBeInTheDocument();
  readOnly(fetch);
});

it("hides a price after the display permission ends", async () => {
  const expired = ticket();
  expired.quote = { ...expired.quote!, valid_until: at(2) };
  const { fetch } = setup({ context: () => Response.json(expired) });
  expect(await screen.findByText("$150.50")).toBeVisible();
  vi.mocked(Date.now).mockReturnValue(now + 3000);
  await waitFor(() => expect(screen.queryByText("$150.50")).not.toBeInTheDocument(), {
    timeout: 2000,
  });
  expect(screen.queryByTitle(at(-8))).not.toBeInTheDocument();
  readOnly(fetch);
});

it("hides an open-session price that has passed its freshness window", async () => {
  const stale = ticket();
  stale.quote = {
    ...stale.quote!,
    event_at: at(-120),
    collected_at: at(-119),
    valid_until: at(60),
  };
  const { fetch } = setup({ context: () => Response.json(stale) });
  expect(await screen.findByRole("heading", { name: "Fixture Aerospace" })).toBeVisible();
  expect(screen.queryByText("$150.50")).not.toBeInTheDocument();
  expect(screen.queryByTitle(at(-120))).not.toBeInTheDocument();
  readOnly(fetch);
});

it("discards the former portfolio's late ticket response", async () => {
  let resolveFirst!: (response: Response) => void;
  const firstResponse = new Promise<Response>((resolve) => (resolveFirst = resolve));
  const { user, fetch } = setup({
    context: (id) => (id === "1" ? firstResponse : Response.json(ticket("2"))),
  });
  expect(await screen.findByText("Loading stock…")).toBeVisible();
  await waitFor(() => expect(fetch.mock.calls.map(([path]) => path)).toContain(contextPath("1")));
  await user.selectOptions(screen.getByRole("combobox", { name: "Trading portfolio" }), "2");
  expect(await screen.findByText("Cash available $2,500.00")).toBeVisible();
  const late = ticket();
  late.listing.company_name = "Obsolete listing response";
  await act(async () => resolveFirst(Response.json(late)));
  expect(screen.getByRole("heading", { name: "Fixture Aerospace" })).toBeVisible();
  expect(screen.queryByText("Obsolete listing response")).not.toBeInTheDocument();
  expect(screen.getByTestId("location")).toHaveTextContent(ticketPath("2"));
  readOnly(fetch);
});
