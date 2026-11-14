import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, render, screen, within, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import userEvent from "@testing-library/user-event";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";
import StockTradePage from "./StockTradePage";
import App from "@/App";
const clients: QueryClient[] = [];
function setup(
  options: {
    context?: () => Response;
    trade?: (body: Record<string, unknown>) => Response | Promise<Response>;
    route?: string;
    app?: boolean;
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
        {options.app ? (
          <App />
        ) : (
          <Routes>
            <Route path="/trade/stocks/:symbol" element={<StockTradePage />} />
          </Routes>
        )}
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
  const { user, calls } = setup({
    trade: () =>
      new Response(JSON.stringify({ detail: { code: "receipt_unavailable" } }), { status: 409 }),
  });
  const input = await screen.findByLabelText("Whole-share quantity");
  await user.type(input, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  const confirm = screen.getByRole("button", { name: "Confirm buy" });
  await waitFor(() => expect(confirm).toBeEnabled());
  await user.click(confirm);
  expect(await screen.findByRole("button", { name: "Check order result" })).toBeEnabled();
  expect(input).toBeDisabled();
  const original = calls.find((c) => c.path === "/api/v1/stock-trades")!.body;
  await user.click(screen.getByRole("button", { name: "Check order result" }));
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades").map((c) => c.body)).toEqual([
    original,
    original,
  ]);
});
it.each(["0", "1.5", "1e2", "-2", "1000000000000"])(
  "rejects invalid whole-share quantity %s without requesting a preview",
  async (quantity) => {
    const { user, calls } = setup();
    const input = await screen.findByLabelText("Whole-share quantity");
    await user.type(input, quantity);
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("button", { name: "Preview trade" })).toBeDisabled();
    expect(calls.some((c) => c.path.endsWith("/quote"))).toBe(false);
  },
);
it("Buy max edits the draft only and side selection highlights ask/bid with keyboard radios", async () => {
  const { user, calls } = setup();
  const input = await screen.findByLabelText("Whole-share quantity");
  await waitFor(() => expect(screen.getByRole("button", { name: "Buy max" })).toBeEnabled());
  await user.click(screen.getByRole("button", { name: "Buy max" }));
  expect(input).toHaveValue("98");
  expect(calls.some((c) => c.path.endsWith("/quote") || c.path === "/api/v1/stock-trades")).toBe(
    false,
  );
  expect(screen.getByText("Buy price")).toBeVisible();
  const sell = screen.getByRole("radio", { name: "Sell" });
  await user.click(sell);
  expect(sell).toBeChecked();
  expect(screen.getByText("Sell price")).toBeVisible();
  expect(screen.getByRole("button", { name: "Sell all" })).toBeDisabled();
});
it("price changes show old/new values and require a second explicit confirmation", async () => {
  const q = quoteFixture();
  Object.assign(q, {
    ask: "103",
    exact_mid: "101.5",
    exec_price: "103",
    notional: "206",
    cash_delta: "-206",
    cash_after: "9794",
  });
  const changed = {
    code: "price_changed",
    previous_exec_price: "102",
    previous_cash_delta: "-204",
    exec_price_change: "1",
    cash_delta_change: "-2",
    quote: q,
  };
  let count = 0;
  const { user, calls } = setup({
    trade: () => {
      count++;
      if (count === 1) return new Response(JSON.stringify({ detail: changed }), { status: 409 });
      const f = fillFixture();
      Object.assign(f, {
        ask: "103",
        exact_mid: "101.5",
        exec_price: "103",
        notional: "206",
        cash_delta: "-206",
        cash_after: "9794",
      });
      return new Response(JSON.stringify(f));
    },
  });
  await user.type(await screen.findByLabelText("Whole-share quantity"), "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  const confirm = screen.getByRole("button", { name: "Confirm buy" });
  await waitFor(() => expect(confirm).toBeEnabled());
  await user.click(confirm);
  const changes = await screen.findByRole("region", { name: "Price changes" });
  expect(changes).toHaveTextContent("Previous execution price$102.00");
  expect(changes).toHaveTextContent("New execution price$103.00");
  expect(changes).toHaveTextContent("Difference−$2.00");
  expect(count).toBe(1);
  expect(screen.queryByRole("heading", { name: "Order filled" })).toBeNull();
  await user.click(confirm);
  await screen.findByRole("heading", { name: "Order filled" });
  expect(count).toBe(2);
  const bodies = calls.filter((c) => c.path === "/api/v1/stock-trades").map((c) => c.body!);
  expect(bodies[0].idempotency_key).not.toBe(bodies[1].idempotency_key);
  expect(bodies[1].expected_exec_price).toBe("103");
});
it("unknown response keeps fields frozen and checks the same original body after closure", async () => {
  let count = 0;
  const { user, calls, client } = setup({
    trade: () => {
      if (++count === 1) throw new Error("lost");
      return new Response(JSON.stringify(fillFixture()));
    },
  });
  const input = await screen.findByLabelText("Whole-share quantity");
  await user.type(input, "2");
  await user.click(screen.getByRole("button", { name: "Preview trade" }));
  const confirm = screen.getByRole("button", { name: "Confirm buy" });
  await waitFor(() => expect(confirm).toBeEnabled());
  await user.click(confirm);
  const check = await screen.findByRole("button", { name: "Check order result" });
  expect(input).toBeDisabled();
  expect(screen.queryByRole("button", { name: "Trade again" })).toBeNull();
  const key = ["stockContext", "first@example.test", "AAPL"];
  const c = client.getQueryData<Record<string, unknown>>(key)!;
  act(() =>
    client.setQueryData(key, { ...c, execution_enabled: false, execution_reason: "market_closed" }),
  );
  await user.click(check);
  await screen.findByRole("heading", { name: "Order filled" });
  const bodies = calls.filter((c) => c.path === "/api/v1/stock-trades").map((c) => c.body);
  expect(bodies[1]).toEqual(bodies[0]);
});
it("invalid route symbols show a safe return to Markets without stock requests", () => {
  const { calls } = setup({ route: "/trade/stocks/invalid!" });
  expect(screen.getByRole("heading", { name: "Unknown stock" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Back to Markets" })).toHaveAttribute("href", "/");
  expect(calls).toHaveLength(0);
});

it("the authenticated App mounts the distinct stock route", async () => {
  setup({ app: true });
  expect(await screen.findByRole("heading", { name: "Trade AAPL", level: 1 })).toBeVisible();
  expect(await screen.findByLabelText("Whole-share quantity")).toBeVisible();
  expect(screen.getByRole("link", { name: "Markets" })).toHaveAttribute("href", "/");
  expect(screen.queryByLabelText("Amount (USD)")).toBeNull();
});
