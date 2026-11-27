import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import App from "@/App";
import type { CatalogFill, CatalogPreview, CatalogTradeContext } from "@/api/stockCatalog";
import { cashPortfolio } from "@/test/portfolioFixtures";

const catalogId = "9007199254741002";
const contextPath = (portfolioId: string) =>
  `/api/v2/portfolios/${portfolioId}/stock-catalog/${catalogId}/trade-context`;
const ticketPath = (portfolioId: string) => `/portfolios/${portfolioId}/trade/catalog/${catalogId}`;
const orderPath = (portfolioId: string, action: string) =>
  `/api/v2/portfolios/${portfolioId}/stock-catalog/${catalogId}/${action}`;
const first = { id: "1", name: "My portfolio" };
const second = { id: "2", name: "Income portfolio" };
const now = Date.parse("2026-11-24T15:00:00Z");
const at = (seconds: number) => new Date(now + seconds * 1000).toISOString();

function ticket(portfolioId = "1"): CatalogTradeContext {
  return {
    portfolio_id: portfolioId,
    read_only: true,
    execution_reason: "read_only",
    cash: portfolioId === "1" ? "10000.00" : "2500.00",
    held_quantity: "0",
    buy_max_quantity: "0",
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
  order,
}: {
  route?: string;
  portfolios?: (typeof first)[];
  context?: (id: string) => Response | Promise<Response>;
  order?: (path: string, body: Record<string, unknown>) => Response | Promise<Response>;
} = {}) {
  vi.spyOn(Date, "now").mockReturnValue(now);
  if (order) document.cookie = "bj_csrf=test; path=/";
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (init?.method === "POST" && order && path.startsWith("/api/v2/"))
      return order(path, JSON.parse(String(init.body)));
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
  return { client, fetch, user: userEvent.setup() };
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
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
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
  expect(screen.getAllByRole("combobox")).toEqual([chooser]);
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

it("refuses ticket data for another listing even when it has the same ticker", async () => {
  const sameTicker = ticket();
  sameTicker.listing.catalog_id = "9007199254741012";
  const { fetch } = setup({ context: () => Response.json(sameTicker) });
  expect(await screen.findByRole("heading", { name: "Stock unavailable" })).toBeVisible();
  expect(screen.queryByText("Fixture Aerospace")).not.toBeInTheDocument();
  expect(screen.queryByText("Cash available $10,000.00")).not.toBeInTheDocument();
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
  const { fetch, user } = setup({ context: () => Response.json(closed) });
  expect(await screen.findByText("Opens in 1 hr 45 min")).toBeVisible();
  expect(screen.getByText(/Market closed/)).toBeVisible();
  expect(screen.getByText("$150.50")).toBeVisible();
  expect(screen.queryByText(/IEX price/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Orders aren't available/)).not.toBeInTheDocument();
  const quantity = screen.getByLabelText("Whole-share quantity");
  await user.type(quantity, "3");
  expect(quantity).toHaveValue("3");
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

function openTicket(): CatalogTradeContext {
  return { ...ticket(), read_only: false, execution_reason: "available", buy_max_quantity: "66" };
}

function preview(repriced = false): CatalogPreview {
  return {
    portfolio_id: "1",
    catalog_id: catalogId,
    listing_version: ticket().listing.listing_version,
    symbol: "FQA",
    company_name: "Fixture Aerospace",
    listing_exchange: "NASDAQ",
    currency: "USD",
    side: "buy",
    quantity: "2",
    bid: "150.00",
    ask: repriced ? "151.125" : "151.00",
    exact_mid: repriced ? "150.5625" : "150.50",
    exec_price: repriced ? "151.125" : "151.00",
    source: "alpaca",
    feed: "iex",
    event_at: at(-8),
    collected_at: at(-7),
    observed_at: at(0),
    age_seconds: 8,
    notional: repriced ? "302.25" : "302.00",
    fee: "0",
    cash_delta: repriced ? "-302.25" : "-302.00",
    cash_before: "10000.00",
    cash_after: repriced ? "9697.75" : "9698.00",
    held_before: "0",
    held_after: "2",
    session_date: "2026-11-24",
    session_opens_at: at(-1800),
    session_closes_at: at(7200),
    valid_until: at(45),
    preview_token: "1795532445000000.0." + (repriced ? "b" : "a").repeat(64),
  };
}

function fill(repriced = false): CatalogFill {
  const { valid_until, preview_token, ...values } = preview(repriced);
  void [valid_until, preview_token];
  return {
    ...values,
    observed_at: at(-5),
    age_seconds: 3,
    schema_version: 1,
    trade_id: "9007199254741004",
    executed_at: at(1),
  };
}

it("uses the existing ticket controls, explicitly reviews repricing, and focuses a 201 receipt", async () => {
  const confirmations: Record<string, unknown>[] = [];
  const { user } = setup({
    context: () => Response.json(openTicket()),
    order: (path, body) => {
      if (path.endsWith("/preview")) {
        expect(path).toBe(orderPath("1", "preview"));
        expect(body).toEqual({
          listing_version: ticket().listing.listing_version,
          side: "buy",
          quantity: "2",
        });
        return Response.json(preview());
      }
      expect(path).toBe(orderPath("1", "confirm"));
      confirmations.push(body);
      if (confirmations.length === 1)
        return Response.json(
          {
            detail: {
              code: "price_changed",
              previous_exec_price: "151.00",
              previous_cash_delta: "-302.00",
              exec_price_change: "0.125",
              cash_delta_change: "-0.25",
              quote: preview(true),
            },
          },
          { status: 409 },
        );
      return Response.json(fill(true), { status: 201 });
    },
  });
  const quantity = await screen.findByLabelText("Whole-share quantity");
  const activeTicket = within(screen.getByRole("region", { name: "Trade ticket" }));
  const status = screen.getByRole("status");
  expect(status).toHaveClass("sr-only");
  expect(activeTicket.getByText("Cash available $10,000.00")).toBeVisible();
  expect(activeTicket.getByText("Shares owned 0")).toBeVisible();
  await user.click(activeTicket.getByRole("radio", { name: "Sell" }));
  expect(activeTicket.getByText("Cash available $10,000.00")).toBeVisible();
  expect(activeTicket.getByText("Shares owned 0")).toBeVisible();
  await user.click(activeTicket.getByRole("radio", { name: "Buy" }));
  await user.click(screen.getByRole("button", { name: "Buy max" }));
  expect(quantity).toHaveValue("66");
  await user.clear(quantity);
  await user.type(quantity, "1.5");
  expect(quantity).toHaveAccessibleDescription("Enter a whole number greater than 0.");
  expect(screen.getByRole("button", { name: "Preview trade" })).toBeDisabled();
  await user.clear(quantity);
  await user.type(quantity, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  expect(confirmations).toHaveLength(0);
  const confirm = await screen.findByRole("button", { name: "Confirm buy" });
  expect(status).toHaveTextContent("Preview ready. Review before confirming.");
  await user.click(confirm);
  expect(await screen.findByText(/Price updated/)).toBeVisible();
  expect(status).toHaveTextContent("Price changed. Review the updated preview and confirm again.");
  expect(screen.getAllByRole("status")).toEqual([status]);
  expect(screen.getAllByText("$151.125").length).toBeGreaterThan(0);
  expect(confirmations).toHaveLength(1);
  await user.click(screen.getByRole("button", { name: "Confirm buy" }));
  expect(await screen.findByRole("heading", { name: "Order filled" })).toHaveFocus();
  expect(screen.getByRole("link", { name: /^Portfolio$/ })).toHaveAttribute(
    "href",
    "/portfolios/1",
  );
  expect(confirmations.map((order) => order.expected_exec_price)).toEqual(["151.00", "151.125"]);
  expect(confirmations.map((order) => order.preview_token)).toEqual([
    preview().preview_token,
    preview(true).preview_token,
  ]);
  expect(confirmations[1].idempotency_key).not.toBe(confirmations[0].idempotency_key);
  expect(screen.getAllByText("My portfolio")).toEqual([
    screen.getByRole("option", { name: "My portfolio" }),
  ]);
});

it("keeps quantity across a hold and closure, without offering an expired confirmation", async () => {
  let active = openTicket();
  const { user, client, fetch } = setup({
    context: () => Response.json(active),
    order: (path) => (path.endsWith("/quote") ? Response.json(active) : Response.json(preview())),
  });
  const quantity = await screen.findByLabelText("Whole-share quantity");
  await user.type(quantity, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  expect(await screen.findByRole("button", { name: "Confirm buy" })).toBeEnabled();
  active = {
    ...active,
    read_only: true,
    execution_reason: "action_unavailable",
    quote: null,
    reason: "quote_unavailable",
    buy_max_quantity: "0",
  };
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["stockCatalogTradeContext"] });
  });
  expect(await screen.findByText("Trading paused for corporate-action review.")).toBeVisible();
  await waitFor(() => {
    expect(fetch.mock.calls.filter(([path]) => String(path).endsWith("/quote"))).toHaveLength(1);
  });
  expect(screen.getByLabelText("Whole-share quantity")).toHaveValue("2");
  expect(screen.queryByRole("button", { name: "Confirm buy" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Preview trade" })).toBeDisabled();

  active = {
    ...active,
    session: { state: "closed", opens_at: at(-3600), closes_at: at(-20), next_open_at: at(7200) },
    quote: { ...ticket().quote!, event_at: at(-30), collected_at: at(-29), valid_until: at(7200) },
    execution_reason: "market_closed",
    reason: "market_closed",
  };
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["stockCatalogTradeContext"] });
  });
  expect(await screen.findByText("Opens in 2 hr")).toBeVisible();
  expect(screen.getByText("$150.50")).toBeVisible();
  expect(screen.getByLabelText("Whole-share quantity")).toHaveValue("2");
  expect(screen.queryByRole("button", { name: "Preview trade" })).not.toBeInTheDocument();
});

it("checks the exact saved attempt after the listing is renamed and the session closes", async () => {
  const tries: { path: string; body: Record<string, unknown> }[] = [];
  let active = openTicket();
  const { user, client } = setup({
    context: () => Response.json(active),
    order: (path, body) => {
      if (path.endsWith("/preview")) return Response.json(preview());
      const action = path.split("/").at(-1);
      tries.push({ path, body });
      if (action === "confirm")
        return Response.json({ detail: { code: "service_unavailable" } }, { status: 503 });
      if (tries.length === 2)
        return Response.json({ detail: { code: "receipt_unavailable" } }, { status: 409 });
      return Response.json(fill(), { status: 200 });
    },
  });
  await user.type(await screen.findByLabelText("Whole-share quantity"), "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  await user.click(await screen.findByRole("button", { name: "Confirm buy" }));
  expect(await screen.findByRole("button", { name: "Check order result" })).toBeEnabled();
  active = {
    ...active,
    session: { state: "closed", opens_at: at(-3600), closes_at: at(-20), next_open_at: at(7200) },
    read_only: true,
    execution_reason: "market_closed",
    quote: null,
    reason: "market_closed",
    buy_max_quantity: "0",
    listing: {
      ...active.listing,
      ticker: "NEWF",
      company_name: "Renamed Aerospace",
      listing_version: "9007199254741005",
    },
  };
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["stockCatalogTradeContext"] });
  });
  expect(await screen.findByRole("heading", { name: "Renamed Aerospace" })).toBeVisible();
  expect(screen.getByText("Opens in 2 hr")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Preview trade" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Check order result" }));
  expect(await screen.findByRole("button", { name: "Check order result" })).toBeEnabled();
  expect(screen.queryByRole("button", { name: "Confirm buy" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Check order result" }));
  expect(await screen.findByRole("heading", { name: "Order filled" })).toHaveFocus();
  expect(screen.getByText(/Fixture Aerospace · FQA/)).toBeVisible();
  expect(tries.map(({ path }) => path)).toEqual([
    orderPath("1", "confirm"),
    orderPath("1", "receipt"),
    orderPath("1", "receipt"),
  ]);
  expect(tries.map(({ body }) => body)).toEqual([tries[0].body, tries[0].body, tries[0].body]);
});

it("retains the draft when the preview deadline passes without sending a confirmation", async () => {
  const { user, fetch } = setup({
    context: () => Response.json(openTicket()),
    order: () => Response.json(preview()),
  });
  const quantity = await screen.findByLabelText("Whole-share quantity");
  await user.type(quantity, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  expect(await screen.findByRole("button", { name: "Confirm buy" })).toBeEnabled();
  vi.mocked(Date.now).mockReturnValue(now + 46_000);
  await waitFor(() => expect(screen.queryByRole("button", { name: "Confirm buy" })).toBeNull(), {
    timeout: 2000,
  });
  expect(quantity).toHaveValue("2");
  expect(fetch.mock.calls.some(([path]) => String(path).endsWith("/confirm"))).toBe(false);
});

it("uses the terminal no-fill lookup to restore the quantity draft without submitting", async () => {
  const attempts: { action: string | undefined; body: Record<string, unknown> }[] = [];
  const { user } = setup({
    context: () => Response.json(openTicket()),
    order: (path, body) => {
      const action = path.split("/").at(-1);
      attempts.push({ action, body });
      if (action === "preview") return Response.json(preview());
      if (action === "confirm") return Response.json({}, { status: 503 });
      return Response.json({ detail: { code: "receipt_missing" } }, { status: 409 });
    },
  });
  await user.type(await screen.findByLabelText("Whole-share quantity"), "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  await user.click(await screen.findByRole("button", { name: "Confirm buy" }));
  await user.click(await screen.findByRole("button", { name: "Check order result" }));
  expect(
    await screen.findByText("This order didn’t fill. Preview again to place a new order."),
  ).toBeVisible();
  expect(screen.getByLabelText("Whole-share quantity")).toHaveValue("2");
  expect(screen.queryByRole("button", { name: "Confirm buy" })).not.toBeInTheDocument();
  expect(attempts.map(({ action }) => action)).toEqual(["preview", "confirm", "receipt"]);
  expect(attempts[2].body).toEqual(attempts[1].body);
  expect(attempts[2].body.preview_token).toBe(preview().preview_token);
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  expect(await screen.findByRole("button", { name: "Confirm buy" })).toBeEnabled();
  expect(attempts.map(({ action }) => action)).toEqual([
    "preview",
    "confirm",
    "receipt",
    "preview",
  ]);
});

it("requests a quote again after reopening with new units and stays idle while closed", async () => {
  let view: CatalogTradeContext = {
    ...ticket(),
    execution_reason: "status_unavailable",
    quote: null,
    reason: "quote_unavailable",
  };
  const { client, fetch } = setup({
    context: () => Response.json(view),
    order: (path, body) => {
      expect(path).toBe(`/api/v2/stock-catalog/${catalogId}/quote`);
      expect(body).toEqual({ listing_version: view.listing.listing_version });
      view = openTicket();
      const { portfolio_id, cash, held_quantity, buy_max_quantity, ...price } = view;
      void [portfolio_id, cash, held_quantity, buy_max_quantity];
      return Response.json(price);
    },
  });
  expect(await screen.findByLabelText("Whole-share quantity")).toBeVisible();
  const requests = () => fetch.mock.calls.filter(([path]) => String(path).endsWith("/quote"));
  expect(requests()).toHaveLength(1);
  view = {
    ...view,
    read_only: true,
    buy_max_quantity: "0",
    execution_reason: "market_closed",
    session: { state: "closed", opens_at: at(-7200), closes_at: at(-20), next_open_at: at(60) },
    quote: null,
    reason: "market_closed",
  };
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["stockCatalogTradeContext"] });
  });
  expect(await screen.findByText(/Market closed/)).toBeVisible();
  expect(requests()).toHaveLength(1);
  vi.mocked(Date.now).mockReturnValue(now + 61_000);
  view = {
    ...ticket(),
    execution_reason: "units_changed",
    quote: null,
    reason: "quote_unavailable",
  };
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["stockCatalogTradeContext"] });
  });
  await waitFor(() => {
    expect(requests()).toHaveLength(2);
    expect(screen.getByLabelText("Whole-share quantity")).toBeVisible();
  });
});
