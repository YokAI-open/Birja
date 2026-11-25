import { act, screen, within, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Link, MemoryRouter, Route, Routes } from "react-router";
import { render, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PortfolioPage from "./PortfolioPage";
import { PortfolioAllocation } from "@/components/PortfolioAllocation";
import { cashPortfolio, mixedPortfolio, stockHolding } from "@/test/portfolioFixtures";
import type { Portfolio } from "@/api/portfolio";
import { PortfolioTargetBoundary } from "@/components/PortfolioTargetBoundary";
import type { PortfolioSummary } from "@/api/portfolios";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";
import { PortfolioRoute } from "@/App";

const clients: QueryClient[] = [];
it.each(["reject-abort", "late-response", "late-response-new-save", "late-response-logout"])(
  "interrupts a routed pending PATCH for review without accepting its obsolete outcome (%s)",
  async (mode) => {
    const management = { id: "1", name: "My portfolio", description: "Original" };
    const metadata = [{ id: "1", name: "My portfolio" }];
    let deferDiscovery = false;
    let releaseDiscovery!: (response: Response) => void;
    const discovery = new Promise<Response>((resolve) => {
      releaseDiscovery = resolve;
    });
    let releasePatch!: (response: Response) => void;
    let releaseNewPatch!: (response: Response) => void;
    let signal: AbortSignal | undefined;
    let patches = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method === "PATCH") {
          patches++;
          signal = init.signal as AbortSignal;
          return new Promise<Response>((resolve, reject) => {
            if (patches === 1) releasePatch = resolve;
            else releaseNewPatch = resolve;
            if (mode === "reject-abort")
              signal!.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
              );
          });
        }
        return Promise.resolve(
          new Response(JSON.stringify({ ...cashPortfolio(), name: management.name })),
        );
      }),
    );
    const { user, client } = mount({
      metadata,
      management,
      discovery: () =>
        deferDiscovery
          ? discovery.then((response) => response.clone())
          : Promise.resolve(new Response(JSON.stringify(metadata))),
    });
    await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
    await user.clear(screen.getByLabelText("Description (optional)"));
    await user.type(screen.getByLabelText("Description (optional)"), "My pending draft");
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    await waitFor(() => expect(patches).toBe(1));
    management.description = "Latest other-tab metadata";
    deferDiscovery = true;
    act(() => broadcastMetadataChange("1"));
    await screen.findByLabelText("Loading portfolio");
    await waitFor(() => expect(signal?.aborted).toBe(true));
    await new Promise((resolve) => setTimeout(resolve, 25));
    if (mode === "late-response-logout") act(() => client.setQueryData(["me"], null));
    await act(async () => releaseDiscovery(new Response(JSON.stringify(metadata))));
    if (mode === "late-response-logout") {
      await act(async () =>
        releasePatch(
          new Response(JSON.stringify({ ...management, description: "Obsolete reply" })),
        ),
      );
      expect(screen.queryByDisplayValue("My pending draft")).toBeNull();
      expect(screen.queryByText("Portfolio updated.")).toBeNull();
      expect(
        client
          .getQueryCache()
          .findAll({ queryKey: ["portfolioMetadataDraft", "first@example.test"] }),
      ).toHaveLength(0);
      return;
    }
    expect(await screen.findByLabelText("Description (optional)")).toHaveValue("My pending draft");
    expect(screen.getByText(/Latest description/)).toHaveTextContent("Latest other-tab metadata");
    const review = screen.getByRole("button", { name: "I have reviewed the latest details" });
    expect(review).toBeEnabled();
    expect(screen.getByRole("button", { name: "Discard changes" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
    if (mode === "late-response")
      await act(async () =>
        releasePatch(
          new Response(JSON.stringify({ ...management, description: "Obsolete reply" })),
        ),
      );
    expect(screen.queryByText("Portfolio updated.")).toBeNull();
    expect(screen.getByLabelText("Description (optional)")).toHaveValue("My pending draft");
    expect(patches).toBe(1);
    await user.click(review);
    expect(screen.getByRole("button", { name: "Save changes" })).toBeEnabled();
    if (mode === "late-response-new-save") {
      await user.click(screen.getByRole("button", { name: "Save changes" }));
      await waitFor(() => expect(patches).toBe(2));
      await act(async () =>
        releasePatch(
          new Response(JSON.stringify({ ...management, description: "Obsolete reply" })),
        ),
      );
      expect(screen.getByRole("button", { name: "Saving changes…" })).toBeDisabled();
      expect(screen.getByLabelText("Description (optional)")).toHaveValue("My pending draft");
      expect(screen.queryByText("Portfolio updated.")).toBeNull();
      management.description = "My pending draft";
      await act(async () => releaseNewPatch(new Response(JSON.stringify(management))));
      expect(await screen.findByText("Portfolio updated.")).toBeInTheDocument();
      return;
    }
    await user.click(screen.getByRole("button", { name: "Discard changes" }));
    expect(screen.getByText("Latest other-tab metadata")).toBeInTheDocument();
  },
);
it.each(["logout", "root", "route", "unavailable"])(
  "clears a routed private draft on %s during deferred revalidation",
  async (departure) => {
    const management = { id: "1", name: "My portfolio", description: "Original" };
    const metadata = [
      { id: "1", name: "My portfolio" },
      { id: "2", name: "Sibling" },
    ];
    let defer = false;
    let release!: (response: Response) => void;
    const deferred = new Promise<Response>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify(cashPortfolio())))),
    );
    const { user, client } = mount({
      metadata,
      management,
      discovery: () => (defer ? deferred : Promise.resolve(new Response(JSON.stringify(metadata)))),
    });
    await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
    await user.clear(screen.getByLabelText("Description (optional)"));
    await user.type(screen.getByLabelText("Description (optional)"), "Private description draft");
    defer = true;
    act(() => broadcastMetadataChange("1"));
    await screen.findByLabelText("Loading portfolio");
    await new Promise((resolve) => setTimeout(resolve, 25));
    if (departure === "logout") act(() => client.setQueryData(["me"], null));
    if (departure === "root") await user.click(screen.getByRole("link", { name: "Open sibling" }));
    if (departure === "route")
      await user.click(screen.getByRole("link", { name: "Open History route" }));
    await act(async () =>
      release(new Response(JSON.stringify(departure === "unavailable" ? [metadata[1]] : metadata))),
    );
    await waitFor(() =>
      expect(
        client
          .getQueryCache()
          .findAll({ queryKey: ["portfolioMetadataDraft", "first@example.test", "1"] })
          .every(
            (q) =>
              !(q.state.data as { draft?: unknown; saved?: boolean })?.draft &&
              !(q.state.data as { saved?: boolean })?.saved,
          ),
      ).toBe(true),
    );
    expect(screen.queryByDisplayValue("Private description draft")).toBeNull();
    expect(screen.queryByText("Portfolio updated.")).toBeNull();
    if (departure === "unavailable")
      expect(
        await screen.findByRole("heading", { name: "Portfolio unavailable" }),
      ).toBeInTheDocument();
  },
);
it.each(["cross-tab", "focus"])(
  "retains a dirty routed metadata draft through deferred %s discovery",
  async (change) => {
    const management = { id: "1", name: "My portfolio", description: "Original description" };
    const metadata = [{ id: "1", name: "My portfolio" }];
    let defer = false;
    let release!: (response: Response) => void;
    const deferred = new Promise<Response>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify(cashPortfolio())))),
    );
    const { user, client } = mount({
      metadata,
      management,
      discovery: () => (defer ? deferred : Promise.resolve(new Response(JSON.stringify(metadata)))),
    });
    await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
    await user.clear(screen.getByLabelText("Portfolio name"));
    await user.type(screen.getByLabelText("Portfolio name"), "Private dirty draft");
    await user.clear(screen.getByLabelText("Description (optional)"));
    await user.type(screen.getByLabelText("Description (optional)"), "Keep my description");
    management.name = "Latest authoritative";
    management.description = "Other tab description";
    metadata[0].name = management.name;
    defer = true;
    act(() => {
      if (change === "cross-tab") broadcastMetadataChange("1");
      else {
        window.dispatchEvent(new Event("focus"));
        void client.invalidateQueries({ queryKey: ["portfolios", "first@example.test"] });
      }
    });
    await screen.findByLabelText("Loading portfolio");
    expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
    await new Promise((resolve) => setTimeout(resolve, 25));
    await act(async () => release(new Response(JSON.stringify(metadata))));
    expect(await screen.findByLabelText("Portfolio name")).toHaveValue("Private dirty draft");
    expect(screen.getByLabelText("Description (optional)")).toHaveValue("Keep my description");
    expect(screen.getByText(/Latest portfolio name/)).toHaveTextContent("Latest authoritative");
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "I have reviewed the latest details" }));
    expect(screen.getByRole("button", { name: "Save changes" })).toBeEnabled();
    act(() => client.setQueryData(["me"], null));
    expect(screen.queryByText("Private dirty draft")).toBeNull();
    expect(screen.queryByDisplayValue("Private dirty draft")).toBeNull();
  },
);
it.each(["stay", "logout", "owner", "logout-return"])(
  "retains routed save feedback only for the current session after deferred discovery (%s)",
  async (departure) => {
    const management = { id: "1", name: "My portfolio", description: "Original" };
    const metadata = [{ id: "1", name: "My portfolio" }];
    let defer = false;
    let release!: (response: Response) => void;
    const deferred = new Promise<Response>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method === "PATCH") {
          Object.assign(management, JSON.parse(String(init.body)));
          metadata[0].name = management.name;
          defer = true;
          return Promise.resolve(new Response(JSON.stringify(management)));
        }
        return Promise.resolve(
          new Response(JSON.stringify({ ...cashPortfolio(), name: management.name })),
        );
      }),
    );
    const { user, client } = mount({
      metadata,
      management,
      discovery: () =>
        defer
          ? deferred.then((response) => response.clone())
          : Promise.resolve(new Response(JSON.stringify(metadata))),
    });
    await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
    await user.clear(screen.getByLabelText("Description (optional)"));
    await user.type(screen.getByLabelText("Description (optional)"), "Updated");
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    await screen.findByLabelText("Loading portfolio");
    await new Promise((resolve) => setTimeout(resolve, 25));
    if (departure !== "stay")
      act(() => {
        client.setQueryData(["me"], null);
        if (departure !== "logout")
          client.setQueryData(["me"], {
            email: departure === "owner" ? "new@example.test" : "first@example.test",
          });
      });
    await act(async () => release(new Response(JSON.stringify(metadata))));
    if (departure !== "stay") {
      expect(screen.queryByText("Portfolio updated.")).toBeNull();
      expect(
        client
          .getQueryCache()
          .findAll({ queryKey: ["portfolioMetadataDraft"] })
          .every((q) => !(q.state.data as { saved?: boolean })?.saved),
      ).toBe(true);
      return;
    }
    expect(await screen.findByText("Portfolio updated.")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Edit portfolio" })).toHaveFocus(),
    );
    expect(screen.getByText("Updated")).toBeInTheDocument();
  },
);
it("cancels a pending original-name financial refresh before accepting a rename", async () => {
  const management = { id: "1", name: "My portfolio", description: "Plan" };
  const metadata = [{ id: "1", name: "My portfolio" }];
  let defer = false;
  let release!: (response: Response) => void;
  let oldSignal: AbortSignal | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v2/portfolios/1" && init?.method === "PATCH") {
        Object.assign(management, JSON.parse(String(init.body)));
        metadata[0].name = management.name;
        return Promise.resolve(new Response(JSON.stringify(management)));
      }
      if (defer) {
        defer = false;
        oldSignal = init?.signal as AbortSignal;
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      }
      return Promise.resolve(
        new Response(JSON.stringify({ ...cashPortfolio(), name: management.name })),
      );
    }),
  );
  const { user, client } = mount({ metadata, management });
  await screen.findByRole("region", { name: "Cash" });
  defer = true;
  await user.click(screen.getByRole("button", { name: "Update portfolio" }));
  await waitFor(() => expect(release).toBeTypeOf("function"));
  await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
  await user.clear(screen.getByLabelText("Portfolio name"));
  await user.type(screen.getByLabelText("Portfolio name"), "New plan");
  await user.click(screen.getByRole("button", { name: "Save changes" }));
  await screen.findByText("Portfolio updated.");
  expect(oldSignal?.aborted).toBe(true);
  await act(async () => release(new Response(JSON.stringify(cashPortfolio()))));
  await waitFor(() =>
    expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$10,000.00"),
  );
  expect(
    client
      .getQueryCache()
      .getAll()
      .filter((q) => q.queryKey[0] === "portfolio")
      .every((q) => q.state.error === null),
  ).toBe(true);
  await user.click(screen.getByRole("button", { name: "Update portfolio" }));
  await waitFor(() =>
    expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$10,000.00"),
  );
});
it("renames and clears descriptions through actual management hooks without altering finances", async () => {
  const management = { id: "1", name: "My portfolio", description: "Keep this strategy" };
  const metadata = [{ id: "1", name: "My portfolio" }];
  const patches: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) === "/api/v2/portfolios/1" && init?.method === "PATCH") {
        const patch = JSON.parse(String(init.body)) as Record<string, string>;
        patches.push(patch);
        Object.assign(management, patch);
        metadata[0].name = management.name;
        return Promise.resolve(new Response(JSON.stringify(management)));
      }
      return Promise.resolve(
        new Response(JSON.stringify({ ...cashPortfolio(), name: management.name })),
      );
    }),
  );
  const { user } = mount({ metadata, management });
  await user.click(await screen.findByRole("button", { name: "Edit portfolio" }));
  await user.clear(screen.getByLabelText("Portfolio name"));
  await user.type(screen.getByLabelText("Portfolio name"), "Long-term <b>plan</b>");
  await user.clear(screen.getByLabelText("Description (optional)"));
  await user.click(screen.getByRole("button", { name: "Save changes" }));
  expect(await screen.findByText("Portfolio updated.")).toBeInTheDocument();
  expect(patches).toEqual([{ name: "Long-term <b>plan</b>", description: "" }]);
  expect(screen.getByRole("button", { name: "Edit portfolio" })).toHaveFocus();
  expect(screen.queryByText("No description.")).toBeNull();
  expect(screen.getByRole("heading", { name: "Long-term <b>plan</b>" })).toBeInTheDocument();
  expect(document.querySelector("b")).toBeNull();
  expect(await screen.findByRole("region", { name: "Cash" })).toHaveTextContent("$10,000.00");
  expect(screen.getByRole("region", { name: "Total portfolio value" })).toHaveTextContent(
    "$10,000.00",
  );
});
it("adds authoritative metadata editing beside unchanged cash and valuation", async () => {
  const { user } = show(cashPortfolio());
  expect(await screen.findByText("A plain-text strategy.")).toBeInTheDocument();
  const cash = await screen.findByRole("region", { name: "Cash" });
  expect(cash).toHaveTextContent("$10,000.00");
  await user.click(screen.getByRole("button", { name: "Edit portfolio" }));
  await user.clear(screen.getByLabelText("Description (optional)"));
  expect(cash).toHaveTextContent("$10,000.00");
  await user.click(screen.getByRole("button", { name: "Discard changes" }));
  expect(screen.getByRole("button", { name: "Edit portfolio" })).toHaveFocus();
});
function show(body = mixedPortfolio()) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(body)))),
  );
  return mount();
}
function mount({
  route = "/portfolios/1",
  metadata = [{ id: "1", name: "My portfolio" }],
  management,
  discovery,
}: {
  route?: string;
  metadata?: PortfolioSummary[];
  management?: { id: string; name: string; description: string };
  discovery?: () => Promise<Response>;
} = {}) {
  const financialFetch = globalThis.fetch;
  vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) => {
    if (String(input) === "/api/v2/portfolios")
      return discovery ? discovery() : Promise.resolve(new Response(JSON.stringify(metadata)));
    if (String(input) === "/api/v2/me")
      return Promise.resolve(new Response(JSON.stringify({ email: "first@example.test" })));
    if (String(input).endsWith("/metadata")) {
      const id = String(input).split("/").at(-2);
      const portfolio = metadata.find((row) => row.id === id);
      return Promise.resolve(
        new Response(
          JSON.stringify(
            management?.id === id
              ? management
              : portfolio
                ? { ...portfolio, description: "A plain-text strategy." }
                : {},
          ),
          { status: portfolio ? 200 : 404 },
        ),
      );
    }
    return financialFetch(input, init);
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test" });
  const user = userEvent.setup();
  return {
    user,
    client,
    ...render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[route]}>
          <Link to="/portfolios/2">Open sibling</Link>
          <Link to="/portfolios/1/history">Open History route</Link>
          <Routes>
            <Route path="/portfolios/:portfolioId" element={<PortfolioRoute />}>
              <Route index element={<PortfolioPage />} />
              <Route path="history" element={<h1>History route</h1>} />
            </Route>
            <Route
              path="/portfolio"
              element={<PortfolioTargetBoundary legacyDestination={(id) => `/portfolios/${id}`} />}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  };
}
function incomplete(): Portfolio {
  const p = mixedPortfolio();
  Object.assign(p, {
    valuation_complete: false,
    known_value: p.cash,
    unvalued_holding_count: 1,
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    cash_allocation_percent: null,
    class_values: { cash: p.cash, stocks: null, crypto: "0" },
    class_allocation_percent: { cash: null, stocks: null, crypto: null },
  });
  Object.assign(p.holdings[0], {
    mid: null,
    current_value: null,
    unrealized_pl: null,
    unrealized_pl_percent: null,
    allocation_percent: null,
    as_of: null,
    age_seconds: null,
    status: "unpriced",
    average_cost: null,
    stock_mark: {
      mark_mode: "unavailable",
      valuation_reason: "action_unavailable",
      source: null,
      feed: null,
      event_at: null,
      collected_at: null,
      historical_admission_until: null,
      retained_until: null,
      valid_until: null,
      authority: null,
      units_safe: false,
    },
  });
  return p;
}
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
});
it("shows stock identity, quantity, value, return and the scoped trade action on the card", async () => {
  const { user } = show();
  const cards = await screen.findByRole("list", { name: "Holdings" });
  const stockCard = within(cards).getByText("Apple Inc.").closest("li")!;
  const cost = within(stockCard).getByText("Average cost");
  expect(cost).not.toBeVisible();
  const details = stockCard.querySelector("summary")!;
  await user.click(details);
  expect(cost).toBeVisible();
  expect(within(stockCard).getByText("Cost basis")).toBeVisible();
  for (const text of ["Apple Inc.", "2 AAPL", "$202.00", "−$2.00", "−0.98%"]) {
    expect(cards).toHaveTextContent(text);
  }
  expect(within(cards).getByRole("link", { name: "Trade AAPL" })).toHaveAttribute(
    "href",
    "/portfolios/1/trade/stocks/AAPL",
  );
  expect(cards.querySelector("time")).toHaveAttribute("datetime", "2026-11-10T15:00:00Z");
  expect(screen.getByRole("note", { name: "Stock valuation price source" })).toHaveTextContent(
    "IEX prices",
  );
});
it("shows exact server incomplete subtotal with no allocation fills or overall returns", async () => {
  show(incomplete());
  expect(await screen.findByText("Known value: $9,796.00 — incomplete")).toBeVisible();
  expect(
    screen.getByText(
      "1 holding cannot be valued. Overall gain/loss and allocation are unavailable.",
    ),
  ).toBeVisible();
  const summary = screen.getByRole("region", { name: "Total portfolio value" });
  expect(summary).not.toHaveTextContent("−$2.00");
  const table = screen.getByRole("list", { name: "Holdings" });
  expect(table).toHaveTextContent("Suspended for corporate-action review");
  expect(table).not.toHaveTextContent("$102.00");
  expect(table).toHaveTextContent("Quantity unavailable");
  expect(document.querySelector("[data-allocation-fill]")).toBeNull();
  expect(screen.getAllByRole("status")).toHaveLength(1);
});

const catalogId = "9007199254740993";

it.each(["closed", "halted"] as const)(
  "keeps a dated %s catalog mark and stable ticket distinct from same-ticker crypto",
  async (mode) => {
    const p = mixedPortfolio();
    const stock = {
      ...stockHolding(),
      symbol: "BTC",
      name: "BTC Fixture Stock",
      catalog_id: catalogId,
      listing_exchange: "NYSE" as const,
      provider_asset_id: null,
      stock_mark: { ...p.holdings[0].stock_mark!, mark_mode: mode, authority: null },
    };
    p.holdings = [
      stock,
      {
        ...stock,
        name: "Bitcoin",
        catalog_id: undefined,
        listing_exchange: undefined,
        coin_id: "1",
        asset_class: "crypto",
        stock_mark: null,
        quantity: "0.12345678",
        current_value: "300.00",
      },
    ];
    const { client } = show(p);
    client.setQueryData(["stocks", "first@example.test"], { admission: { state: "unavailable" } });
    const cards = await screen.findByRole("list", { name: "Holdings" });
    const stockCard = within(cards).getByText("BTC Fixture Stock").closest("li")!;
    expect(stockCard).toHaveTextContent("$202.00");
    expect(stockCard).toHaveTextContent(mode === "halted" ? "Halted" : "Market closed");
    expect(stockCard.querySelector("time")).toHaveAttribute("datetime", "2026-11-10T15:00:00Z");
    expect(within(stockCard).getByRole("link", { name: "View details BTC stock" })).toHaveAttribute(
      "href",
      `/portfolios/1/trade/catalog/${catalogId}`,
    );
    expect(within(cards).getByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/portfolios/1/trade/BTC",
    );
  },
);

it("keeps a restricted catalog holding in an incomplete portfolio without a private link", async () => {
  const p = incomplete();
  Object.assign(p.holdings[0], {
    catalog_id: catalogId,
    is_active: false,
    provider_asset_id: null,
    symbol: "STOCK",
    name: "Restricted stock",
  });
  show(p);
  expect(await screen.findByText("Known value: $9,796.00 — incomplete")).toBeVisible();
  const cards = screen.getByRole("list", { name: "Holdings" });
  expect(cards).toHaveTextContent("Restricted stock");
  expect(cards).not.toHaveTextContent("Apple Inc.");
  expect(within(cards).queryByRole("link")).toBeNull();
});
it.each(["closed", "halted"] as const)(
  "shows dated %s marks without calling them live",
  async (mode) => {
    const p = mixedPortfolio();
    p.holdings[0].stock_mark!.mark_mode = mode;
    show(p);
    const table = await screen.findByRole("list", { name: "Holdings" });
    expect(table).toHaveTextContent(mode === "closed" ? "Market closed" : "Halted");
    expect(table).toHaveTextContent("Last verified midpoint");
    expect(table).not.toHaveTextContent("Live");
    expect(table.querySelector("time")?.getAttribute("title")).toMatch(/2026/);
  },
);
it("uses exactly three server allocation bars and no balancing arithmetic", async () => {
  show();
  const list = await screen.findByRole("list", { name: "Allocation" });
  const rows = within(list).getAllByRole("listitem");
  expect(rows).toHaveLength(3);
  for (const [i, label, percent] of [
    [0, "Cash", "97.98"],
    [1, "Crypto", "0.00"],
    [2, "Stocks", "2.02"],
  ] as const) {
    expect(rows[i]).toHaveTextContent(label + percent + "%");
    expect(rows[i].querySelector("[data-allocation-fill]")).toHaveStyle({ width: percent + "%" });
  }
});
it("keeps crypto fees, fractional units and route independent, with alphabetical identities", async () => {
  const p = mixedPortfolio(),
    crypto = {
      ...stockHolding(),
      symbol: "BTC",
      name: "Bitcoin",
      coin_id: "1",
      asset_class: "crypto" as const,
      provider_asset_id: null,
      stock_mark: null,
      quantity: "0.12345678",
      current_value: "300.00",
    };
  p.holdings = [crypto, p.holdings[0]];
  const { user } = show(p);
  const table = await screen.findByRole("list", { name: "Holdings" });
  expect(
    within(table)
      .getAllByRole("listitem")
      .map((row) => within(row).getByRole("link").getAttribute("aria-label")),
  ).toEqual(["Trade AAPL", "Trade BTC"]);
  expect(table).toHaveTextContent("Crypto");
  expect(table).toHaveTextContent("0.12345678");
  expect(within(table).getByRole("link", { name: "Trade BTC" })).toHaveAttribute(
    "href",
    "/portfolios/1/trade/BTC",
  );
  await user.selectOptions(screen.getByRole("combobox", { name: "Sort holdings" }), "value");
  expect(within(table).getAllByRole("link")[0]).toHaveAccessibleName("Trade BTC");
  await user.selectOptions(screen.getByRole("combobox", { name: "Filter holdings" }), "stock");
  expect(within(table).getAllByRole("listitem")).toHaveLength(1);
  expect(within(table).getByRole("link")).toHaveAccessibleName("Trade AAPL");
});
it("preserves stored starting cash, realised cash and a truthful empty state", async () => {
  const p = cashPortfolio();
  Object.assign(p, {
    cash: "9999.00",
    total_value: "9999.00",
    known_value: "9999.00",
    total_pl: "-1.00",
    total_pl_percent: "-0.01",
    class_values: { cash: "9999.00", stocks: "0", crypto: "0" },
  });
  show(p);
  const summary = await screen.findByRole("region", { name: "Total portfolio value" });
  expect(summary).toHaveTextContent("$9,999.00");
  expect(summary).toHaveTextContent("−$1.00");
  expect(summary).toHaveTextContent("$10,000.00 start");
  expect(screen.getByText("No holdings yet")).toBeVisible();
  expect(screen.getByRole("link", { name: "Explore Markets" })).toHaveAttribute("href", "/");
});
it("hides unvalidated financial projections after refresh failure and preserves retry focus", async () => {
  const p = cashPortfolio();
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(p)))
      .mockResolvedValueOnce(new Response("{}", { status: 500 }))
      .mockImplementation(() => Promise.resolve(new Response(JSON.stringify(p)))),
  );
  const { user } = mount();
  await screen.findByRole("region", { name: "Cash" });
  const refresh = screen.getByRole("button", { name: "Update portfolio" });
  await user.click(refresh);
  expect(await screen.findByRole("alert")).toHaveTextContent("Can't load your portfolio right now");
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(refresh).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Try again" }));
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  expect(refresh).toHaveFocus();
});
it("loading and initial error recovery retain a reachable retry", async () => {
  let finish!: (r: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise<Response>((r) => {
            finish = r;
          }),
      )
      .mockImplementation(() => Promise.resolve(new Response(JSON.stringify(cashPortfolio())))),
  );
  const { user } = mount();
  expect(await screen.findByRole("status", { name: "Loading your portfolio" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await act(async () => finish(new Response("{}", { status: 500 })));
  expect(await screen.findByRole("alert")).toHaveTextContent("Can't load your portfolio right now");
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("region", { name: "Cash" })).toBeVisible();
});
it("in-flight refresh cannot be submitted twice and keeps cash visible", async () => {
  let finish!: (r: Response) => void;
  const p = cashPortfolio();
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(p)))
    .mockImplementation(
      () =>
        new Promise<Response>((r) => {
          finish = r;
        }),
    );
  vi.stubGlobal("fetch", fetch);
  const { user } = mount();
  await screen.findByRole("region", { name: "Cash" });
  await user.click(screen.getByRole("button", { name: "Update portfolio" }));
  const refresh = screen.getByRole("button", { name: "Updating portfolio…" });
  expect(refresh).toHaveAttribute("aria-disabled", "true");
  await user.click(refresh);
  await user.keyboard("{Enter} ");
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$10,000.00");
  await act(async () => finish(new Response(JSON.stringify(p))));
});
it.each(["-1", "100.01", "101", "1e2", "1%;color:red", "Infinity"])(
  "rejects unsafe CSS allocations %s",
  (percent) => {
    const p = cashPortfolio();
    p.class_allocation_percent = { cash: percent, stocks: null, crypto: null };
    render(<PortfolioAllocation portfolio={p} />);
    expect(document.querySelector("[data-allocation-fill]")).toBeNull();
  },
);
it("zero denominator is unavailable while positive raw values rounded to zero retain server allocations", async () => {
  const p = cashPortfolio();
  Object.assign(p, {
    cash: "0",
    total_value: "0",
    known_value: "0",
    total_pl: "-10000",
    total_pl_percent: "-100",
    cash_allocation_percent: null,
    class_values: { cash: "0", stocks: "0", crypto: "0" },
    class_allocation_percent: { cash: null, stocks: null, crypto: null },
  });
  show(p);
  expect(
    await screen.findByText("Allocation is unavailable while total portfolio value is zero."),
  ).toBeVisible();
  expect(document.querySelector("[data-allocation-fill]")).toBeNull();
});
it("long names and huge server values wrap and untrusted names stay escaped", async () => {
  const p = mixedPortfolio();
  p.holdings[0].name = '<img src=x onerror="alert(1)">' + "Long company name ".repeat(25);
  p.holdings[0].current_value = "12345678901234567890123456789012345678.99";
  show(p);
  const table = await screen.findByRole("list", { name: "Holdings" });
  expect(table.querySelector("img")).toBeNull();
  expect(table).toHaveTextContent("12,345,678,901,234,567,890,123,456,789,012,345,678.99");
});
it("retains undefined zero-basis return, inactive holdings and rounded-zero loss semantics", async () => {
  const p = mixedPortfolio();
  Object.assign(p.holdings[0], {
    cost_basis: "0",
    average_cost: "0",
    unrealized_pl: "202",
    unrealized_pl_percent: null,
    is_active: false,
  });
  show(p);
  const table = await screen.findByRole("list", { name: "Holdings" });
  expect(table).toHaveTextContent("Percentage return not applicable because cost basis is zero.");
  expect(table).toHaveTextContent("Inactive · trading unavailable");
  expect(within(table).queryByRole("link")).toBeNull();
});
it("positive raw crypto value rounded to zero keeps server allocation instead of a fabricated denominator", async () => {
  const p = cashPortfolio();
  Object.assign(p, {
    cash: "0",
    total_value: "0",
    known_value: "0",
    total_pl: "-10000",
    total_pl_percent: "-100",
    cash_allocation_percent: "0",
    class_values: { cash: "0", stocks: "0", crypto: "0" },
    class_allocation_percent: { cash: "0", stocks: "0", crypto: "100" },
  });
  p.holdings = [
    {
      ...stockHolding(),
      asset_class: "crypto",
      coin_id: "1",
      provider_asset_id: null,
      stock_mark: null,
      quantity: "0.00000001",
      mid: "1",
      current_value: "0",
      allocation_percent: "100",
    },
  ];
  show(p);
  const list = await screen.findByRole("list", { name: "Allocation" });
  expect(within(list).getByText("100%")).toBeVisible();
  expect(
    screen.queryByText("Allocation is unavailable while total portfolio value is zero."),
  ).toBeNull();
});

it("uses the full escaped portfolio name as the page heading", async () => {
  const name = ("<b>Portfolio</b> " + "Long name ".repeat(4) + "four").slice(0, 60);
  const p = { ...mixedPortfolio(), name };
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(p)))),
  );
  mount({ metadata: [{ id: "1", name }] });
  await screen.findByRole("list", { name: "Holdings" });
  const heading = screen.getByRole("heading", { level: 1, name });
  expect(heading).toBeVisible();
  expect(heading.querySelector("b")).toBeNull();
  expect(screen.getAllByText(name).filter((node) => node.tagName === "DD")).toHaveLength(0);
});

it("uses the actual unequal baseline and retains one root's figures", async () => {
  const p = mixedPortfolio();
  Object.assign(p, {
    cash: "500.00",
    starting_cash: "1234.00",
    total_value: "702.00",
    known_value: "702.00",
    total_pl: "-532.00",
    total_pl_percent: "-43.11",
    cash_allocation_percent: "71.23",
    class_values: { cash: "500.00", stocks: "202.00", crypto: "0.00" },
    class_allocation_percent: { cash: "71.23", stocks: "28.77", crypto: "0.00" },
  });
  p.holdings[0].allocation_percent = "28.77";
  show(p);
  const summary = await screen.findByRole("region", { name: "Total portfolio value" });
  expect(summary).toHaveTextContent("$702.00");
  expect(summary).toHaveTextContent("−$532.00");
  expect(summary).toHaveTextContent("−43.11%");
  expect(summary).toHaveTextContent("Compared with your $1,234.00 start");
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$500.00");
  expect(summary).not.toHaveTextContent("10,000");
});

it("does not issue financial requests or create a portfolio for a zero-root legacy entry", async () => {
  const finance = vi.fn();
  vi.stubGlobal("fetch", finance);
  mount({ route: "/portfolio", metadata: [] });
  expect(await screen.findByRole("heading", { name: "No portfolio available" })).toBeVisible();
  expect(finance).not.toHaveBeenCalled();
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(screen.queryByRole("list", { name: "Holdings" })).toBeNull();
  expect(screen.getByRole("link", { name: "Browse markets" })).toHaveAttribute("href", "/");
});

it("does not fall back from an explicit unavailable root to the sole valid sibling", async () => {
  const finance = vi.fn();
  vi.stubGlobal("fetch", finance);
  mount({ route: "/portfolios/2" });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(finance).not.toHaveBeenCalled();
  expect(screen.getByRole("combobox", { name: "Open portfolio" })).toHaveValue("");
  expect(screen.queryByRole("heading", { name: "My portfolio" })).toBeNull();
});

it("suppresses a delayed old-root statement after switching to a same-symbol sibling", async () => {
  let finish!: (response: Response) => void;
  const sibling = {
    ...mixedPortfolio(),
    portfolio_id: "2",
    name: "Sibling",
    cash: "300.00",
    starting_cash: "400.00",
    total_value: "502.00",
    known_value: "502.00",
    total_pl: "102.00",
    total_pl_percent: "25.50",
    cash_allocation_percent: "59.76",
    class_values: { cash: "300.00", stocks: "202.00", crypto: "0.00" },
    class_allocation_percent: { cash: "59.76", stocks: "40.24", crypto: "0.00" },
  };
  sibling.holdings[0].allocation_percent = "40.24";
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) =>
      String(input).endsWith("/1")
        ? new Promise<Response>((resolve) => {
            finish = resolve;
          })
        : Promise.resolve(new Response(JSON.stringify(sibling))),
    ),
  );
  const { user } = mount({
    metadata: [
      { id: "1", name: "My portfolio" },
      { id: "2", name: "Sibling" },
    ],
  });
  await screen.findByRole("status", { name: "Loading your portfolio" });
  await user.click(screen.getByRole("link", { name: "Open sibling" }));
  const cash = await screen.findByRole("region", { name: "Cash" });
  expect(cash).toHaveTextContent("$300.00");
  await act(async () => finish(new Response(JSON.stringify(mixedPortfolio()))));
  expect(cash).toHaveTextContent("$300.00");
  expect(screen.getByRole("combobox", { name: "Open portfolio" })).toHaveValue("2");
  expect(screen.queryByRole("heading", { name: "My portfolio" })).toBeNull();
  expect(screen.getByRole("region", { name: "Total portfolio value" })).toHaveTextContent(
    "$400.00 start",
  );
  for (const link of screen.getAllByRole("link", { name: "Trade AAPL" }))
    expect(link).toHaveAttribute("href", "/portfolios/2/trade/stocks/AAPL");
});

it("hides accepted holdings and a delayed refresh when the root becomes unavailable", async () => {
  let finish!: (response: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(mixedPortfolio())))
      .mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            finish = resolve;
          }),
      ),
  );
  const { user, client } = mount();
  await screen.findByRole("list", { name: "Holdings" });
  await user.click(screen.getByRole("button", { name: "Update portfolio" }));
  await act(async () => {
    client.setQueryData(["portfolios", "first@example.test"], []);
  });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  await act(async () => finish(new Response(JSON.stringify(mixedPortfolio()))));
  expect(screen.queryByRole("region", { name: "Cash" })).toBeNull();
  expect(screen.queryByRole("list", { name: "Holdings" })).toBeNull();
});
