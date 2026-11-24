import { act, cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioTargetBoundary } from "@/components/PortfolioTargetBoundary";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";
import { cashPortfolio } from "@/test/portfolioFixtures";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";
import TradePage from "./TradePage";
import StockTradePage from "./StockTradePage";

const json = (body: unknown) => new Response(JSON.stringify(body));
function deferred() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>((done) => (resolve = done));
  return { promise, resolve };
}
const clients: QueryClient[] = [];
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

const cryptoQuote = {
  portfolio_id: "1",
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100",
  mid: "100000.00000000",
  as_of: "2026-11-10T15:00:00Z",
  age_seconds: 10,
  exec_price: "100250.00000000",
  quantity: "0.00099501",
  notional: "99.75000000",
  fee: "0.25000000",
  cash_delta: "-100.00000000",
  cash_before: "10000.00000000",
  cash_after: "9900.00000000",
  held_before: "0",
  held_after: "0.00099501",
  whole_position: false,
};
const cryptoFill = {
  ...cryptoQuote,
  trade_id: 1,
  created_at: "2026-11-10T15:00:10Z",
};

it.each(
  (["crypto", "stock"] as const).flatMap((asset) =>
    (["lost", "pending", "filled"] as const).map((mode) => ({ asset, mode })),
  ),
)(
  "preserves the original $asset request across a $mode order and routed rename",
  async ({ asset, mode }) => {
    const stock = asset === "stock";
    let name = "Original",
      renewing = false;
    const metadata = deferred(),
      pendingFill = deferred();
    const requests: { path: string; body: string }[] = [];
    const tradePath = `/api/v2/portfolios/1/${stock ? "stock-trades" : "trades"}`;
    const fill = stock ? fillFixture() : cryptoFill;
    document.cookie = "bj_csrf=test; path=/";
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path === "/api/v2/me") return Promise.resolve(json({ email: "owner@example.test" }));
        if (path === "/api/v2/portfolios")
          return renewing ? metadata.promise : Promise.resolve(json([{ id: "1", name }]));
        if (path === "/api/v2/portfolios/1")
          return Promise.resolve(json({ ...cashPortfolio(), name }));
        if (path.endsWith("/holdings/BTC"))
          return Promise.resolve(json({ portfolio_id: "1", symbol: "BTC", quantity: "0" }));
        if (path === "/api/v1/prices")
          return Promise.resolve(
            json({
              server_time: "2026-11-10T15:00:10Z",
              fresh_seconds: 90,
              stale_seconds: 300,
              items: [
                {
                  symbol: "BTC",
                  name: "Bitcoin",
                  price: cryptoQuote.mid,
                  as_of: cryptoQuote.as_of,
                  age_seconds: 10,
                  status: "fresh",
                },
              ],
            }),
          );
        if (path.endsWith("/context")) return Promise.resolve(json(contextFixture()));
        if (path.endsWith("/quote"))
          return Promise.resolve(json(stock ? quoteFixture() : cryptoQuote));
        if (path === tradePath) {
          requests.push({ path, body: String(init?.body) });
          if (requests.length === 1 && mode === "lost")
            return Promise.reject(new Error("response lost"));
          if (requests.length === 1 && mode === "pending") return pendingFill.promise;
          return Promise.resolve(json(fill));
        }
        return Promise.resolve(new Response("{}", { status: 404 }));
      }),
    );
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    clients.push(client);
    client.setQueryData(["me"], { email: "owner@example.test" });
    const user = userEvent.setup();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/portfolios/1/trade/${stock ? "stocks/AAPL" : "BTC"}`]}>
          <Routes>
            <Route path="/portfolios/:portfolioId" element={<PortfolioTargetBoundary />}>
              <Route path="trade/:symbol" element={<TradePage />} />
              <Route path="trade/stocks/:symbol" element={<StockTradePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await user.type(
      await screen.findByLabelText(stock ? "Whole-share quantity" : "Amount"),
      stock ? "2" : "100",
    );
    if (stock) await user.click(screen.getByRole("button", { name: "Preview trade" }));
    const confirm = screen.getByRole("button", { name: "Confirm buy" });
    await waitFor(() => expect(confirm).toBeEnabled());
    await user.click(confirm);
    await waitFor(() => expect(requests).toHaveLength(1));
    if (mode === "lost") await screen.findByRole("button", { name: "Check order result" });
    if (mode === "filled") await screen.findByRole("heading", { name: "Order filled" });

    // Exercise the real metadata event and discovery boundary, not hook rerender
    // props: its loading state must actually remove the financial Outlet.
    renewing = true;
    act(() => broadcastMetadataChange("1"));
    await screen.findByRole("status", { name: "Loading portfolio" });
    expect(screen.queryByRole("heading", { name: stock ? "Trade AAPL" : "Trade BTC" })).toBeNull();
    name = "Renamed";
    renewing = false;
    await act(async () => metadata.resolve(json([{ id: "1", name }])));
    await screen.findByRole("heading", { name: stock ? "Trade AAPL" : "Trade BTC" });
    expect(screen.queryByText("Renamed")).toBeNull();
    if (mode === "pending") await act(async () => pendingFill.resolve(json(fill)));
    if (mode !== "filled") {
      const retry = await screen.findByRole("button", { name: "Check order result" });
      expect(screen.queryByText("Original")).toBeNull();
      expect(requests).toHaveLength(1);
      await user.click(retry);
      await waitFor(() => expect(requests).toHaveLength(2));
      expect(requests[1]).toEqual(requests[0]);
      const original = JSON.parse(requests[0]!.body);
      expect(original.idempotency_key).toEqual(expect.any(String));
      expect(original.symbol).toBe(stock ? "AAPL" : "BTC");
    }
    const receipt = within(await screen.findByRole("region", { name: "Order filled" }));
    expect(receipt.queryByText("Original")).toBeNull();
    expect(receipt.queryByText("Renamed")).toBeNull();
    expect(receipt.getByRole("link", { name: "Portfolio" })).toHaveAttribute(
      "href",
      "/portfolios/1",
    );
    expect(requests).toHaveLength(mode === "filled" ? 1 : 2);
    await user.click(receipt.getByRole("button", { name: "Trade again" }));
    expect(screen.queryByText("Original")).toBeNull();
    expect(screen.queryByText("Renamed")).toBeNull();
    expect(screen.getByLabelText(stock ? "Whole-share quantity" : "Amount")).toHaveValue("");
  },
);
