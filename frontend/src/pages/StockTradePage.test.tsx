import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, render, screen, within, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import userEvent from "@testing-library/user-event";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";
import StockTradePage from "./StockTradePage";
const clients: QueryClient[] = [];
function setup(
  options: {
    context?: () => Response;
    trade?: (body: Record<string, unknown>) => Response | Promise<Response>;
    route?: string;
  } = {},
) {
  document.cookie = "bj_csrf=test; path=/";
  const calls: { path: string; body: Record<string, unknown> | null }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input),
        body = init?.body ? JSON.parse(String(init.body)) : null;
      calls.push({ path, body });
      if (path.endsWith("/context"))
        return options.context?.() ?? new Response(JSON.stringify(contextFixture()));
      if (path.endsWith("/quote")) return new Response(JSON.stringify(quoteFixture()));
      if (path === "/api/v1/stock-trades")
        return options.trade?.(body!) ?? new Response(JSON.stringify(fillFixture()));
      if (path.endsWith("/me"))
        return new Response(JSON.stringify({ email: "first@example.test", cash_usd: "9796" }));
      return new Response("{}", { status: 404 });
    }),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  const user = userEvent.setup();
  const rendered = render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[options.route ?? "/trade/stocks/AAPL"]}>
        <Routes>
          <Route path="/trade/stocks/:symbol" element={<StockTradePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { ...rendered, user, client, calls };
}
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});
it("requires preview and explicit confirmation, then focuses the immutable historical receipt", async () => {
  const { user, calls } = setup();
  const input = await screen.findByLabelText("Whole-share quantity");
  await user.type(input, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  const confirm = await screen.findByRole("button", { name: "Confirm buy" });
  await waitFor(() => expect(confirm).toBeEnabled());
  expect(calls.filter((x) => x.path === "/api/v1/stock-trades")).toHaveLength(0);
  expect(screen.getByText("Commission")).toBeVisible();
  expect(screen.getByText("Added spread")).toBeVisible();
  await user.click(confirm);
  const heading = await screen.findByRole("heading", { name: "Order filled" });
  expect(heading).toHaveFocus();
  const receipt = screen.getByRole("region", { name: "Order filled" });
  expect(receipt).toHaveTextContent("Cash after this trade$9,796.00");
  expect(receipt).toHaveTextContent("Shares after this trade2");
  expect(within(receipt).getByRole("link", { name: "Portfolio" })).toHaveAttribute(
    "href",
    "/portfolio",
  );
  await user.click(screen.getByRole("button", { name: "Trade again" }));
  expect(screen.getByLabelText("Whole-share quantity")).toHaveValue("");
});
it("closed stocks allow only a draft, with no queue or unsafe executable prices", async () => {
  const c = contextFixture();
  Object.assign(c, {
    execution_enabled: false,
    execution_reason: "market_closed",
    buy_max_quantity: "0",
    valid_until: null,
  });
  c.session.state = "closed";
  const { user, calls } = setup({ context: () => new Response(JSON.stringify(c)) });
  const input = await screen.findByLabelText("Whole-share quantity");
  await user.type(input, "3");
  expect(input).toHaveValue("3");
  expect(screen.getByRole("button", { name: "Preview trade" })).toBeDisabled();
  expect(
    screen.getByText("Market closed. You can edit a draft; no order is queued."),
  ).toBeVisible();
  expect(screen.getByRole("button", { name: "Confirm buy" })).toBeDisabled();
  expect(calls.some((x) => x.path === "/api/v1/stock-trades")).toBe(false);
});
it("keeps an unresolvable saved receipt as an uncertain attempt instead of allowing a new order", async () => {
  const { user, calls } = setup({ trade: () => new Response(JSON.stringify({ detail: { code: "receipt_unavailable" } }), { status: 409 }) });
  const input = await screen.findByLabelText("Whole-share quantity"); await user.type(input, "2"); await user.click(screen.getByRole("button", { name: "Preview trade" }));
  const confirm = screen.getByRole("button", { name: "Confirm buy" }); await waitFor(() => expect(confirm).toBeEnabled()); await user.click(confirm);
  expect(await screen.findByRole("button", { name: "Check order result" })).toBeEnabled(); expect(input).toBeDisabled();
  const original = calls.find(c => c.path === "/api/v1/stock-trades")!.body;
  await user.click(screen.getByRole("button", { name: "Check order result" }));
  expect(calls.filter(c => c.path === "/api/v1/stock-trades").map(c => c.body)).toEqual([original, original]);
});
