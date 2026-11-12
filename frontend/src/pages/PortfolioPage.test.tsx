import { act, screen, within, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { render, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PortfolioPage from "./PortfolioPage";
import { PortfolioAllocation } from "@/components/PortfolioAllocation";
import { cashPortfolio, mixedPortfolio, stockHolding } from "@/test/portfolioFixtures";
import type { Portfolio } from "@/api/portfolio";
const clients: QueryClient[] = [];
function show(body = mixedPortfolio()) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(body)))));
  return mount();
}
function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } }); clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "9796" });
  const user = userEvent.setup();
  return { user, client, ...render(<QueryClientProvider client={client}><MemoryRouter><PortfolioPage /></MemoryRouter></QueryClientProvider>) };
}
function incomplete(): Portfolio {
  const p = mixedPortfolio();
  Object.assign(p, { valuation_complete: false, known_value: p.cash, unvalued_holding_count: 1, total_value: null, total_pl: null, total_pl_percent: null, cash_allocation_percent: null, class_values: { cash: p.cash, stocks: null, crypto: "0" }, class_allocation_percent: { cash: null, stocks: null, crypto: null } });
  Object.assign(p.holdings[0], { mid: null, current_value: null, unrealized_pl: null, unrealized_pl_percent: null, allocation_percent: null, as_of: null, age_seconds: null, status: "unpriced", average_cost: null, stock_mark: { mark_mode: "unavailable", valuation_reason: "action_unavailable", source: null, feed: null, event_at: null, collected_at: null, historical_admission_until: null, retained_until: null, valid_until: null, authority: null, units_safe: false } });
  return p;
}
afterEach(() => { cleanup(); clients.forEach(c => c.clear()); clients.length = 0; vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.useRealTimers(); });
it("shows direct stock figures, seven semantic columns and labelled mobile cards", async () => {
  show(); const table = await screen.findByRole("table", { name: "Holdings" });
  expect(within(table).getAllByRole("columnheader").map(h => h.textContent)).toEqual(["Asset", "Quantity", "Average cost", "Cost basis", "Current value", "Gain/loss", "Allocation"]);
  expect(table.parentElement).toHaveClass("hidden", "lg:block");
  const mobile = screen.getByRole("list", { name: "Holdings" }); expect(mobile).toHaveClass("lg:hidden");
  for (const view of [table, mobile]) {
    expect(view).toHaveTextContent("Stock"); expect(view).toHaveTextContent("Apple Inc.");
    for (const text of ["$102.00", "$204.00", "$202.00", "−$2.00", "−0.98%", "2.02%", "IEX midpoint"] ) expect(view).toHaveTextContent(text);
    expect(within(view).getByRole("link", { name: "Trade AAPL" })).toHaveAttribute("href", "/trade/stocks/AAPL");
    expect(view.querySelector("time")).toHaveAttribute("datetime", "2026-11-10T15:00:00Z");
  }
  for (const label of ["Quantity", "Average cost", "Cost basis", "Current value", "Gain/loss", "Allocation"]) expect(within(mobile).getByText(label, { selector: "dt" })).toBeInTheDocument();
  expect(screen.getByRole("note", { name: "Stock valuation price source" })).toHaveTextContent("IEX prices");
});
it("shows exact server incomplete subtotal with no allocation fills or overall returns", async () => {
  show(incomplete());
  expect(await screen.findByText("Known value: $9,796.00 — incomplete")).toBeVisible();
  expect(screen.getByText("1 holding cannot be valued. Overall gain/loss and allocation are unavailable.")).toBeVisible();
  const summary = screen.getByRole("region", { name: "Total portfolio value" }); expect(summary).not.toHaveTextContent("−$2.00");
  const table = screen.getByRole("table", { name: "Holdings" }); expect(table).toHaveTextContent("Suspended for corporate-action review");
  expect(table).not.toHaveTextContent("$102.00"); expect(table).toHaveTextContent("$204.00");
  expect(document.querySelector("[data-allocation-fill]")).toBeNull();
  expect(screen.getAllByRole("status")).toHaveLength(1);
});
it.each(["closed", "halted"] as const)("shows dated %s marks without calling them live", async mode => {
  const p = mixedPortfolio(); p.holdings[0].stock_mark!.mark_mode = mode; show(p);
  const table = await screen.findByRole("table", { name: "Holdings" });
  expect(table).toHaveTextContent(mode === "closed" ? "Market closed" : "Halted");
  expect(table).toHaveTextContent("Last verified midpoint"); expect(table).not.toHaveTextContent("Live");
  expect(table.querySelector("time")?.textContent).toMatch(/2026/);
});
it("uses exactly three server allocation bars and no balancing arithmetic", async () => {
  show(); const list = await screen.findByRole("list", { name: "Allocation" });
  const rows = within(list).getAllByRole("listitem"); expect(rows).toHaveLength(3);
  for (const [i,label,percent] of [[0,"Cash","97.98"],[1,"Stocks","2.02"],[2,"Crypto","0.00"]] as const) {
    expect(rows[i]).toHaveTextContent(label+percent+"%"); expect(rows[i].querySelector("[data-allocation-fill]")).toHaveStyle({ width: percent+"%" });
  }
});
it("keeps crypto fees, fractional units and route independent, with alphabetical identities", async () => {
  const p = mixedPortfolio(), crypto = { ...stockHolding(), symbol: "BTC", name: "Bitcoin", coin_id: "1", asset_class: "crypto" as const, provider_asset_id: null, stock_mark: null, quantity: "0.12345678" };
  p.holdings = [crypto, p.holdings[0]]; show(p);
  const table = await screen.findByRole("table", { name: "Holdings" });
  expect(within(table).getAllByRole("rowheader").map(h => h.textContent?.slice(0,4))).toEqual(["AAPL","BTCB"]);
  expect(table).toHaveTextContent("Crypto"); expect(table).toHaveTextContent("0.12345678");
  expect(within(table).getByRole("link", { name: "Trade BTC" })).toHaveAttribute("href", "/trade/BTC");
});
it("preserves stored starting cash, realised cash and a truthful empty state", async () => {
  const p = cashPortfolio(); Object.assign(p, { cash: "9999.00", total_value: "9999.00", known_value: "9999.00", total_pl: "-1.00", total_pl_percent: "-0.01", class_values: { cash: "9999.00", stocks: "0", crypto: "0" } }); show(p);
  const summary = await screen.findByRole("region", { name: "Total portfolio value" });
  expect(summary).toHaveTextContent("$9,999.00"); expect(summary).toHaveTextContent("−$1.00"); expect(summary).toHaveTextContent("$10,000.00 start");
  expect(screen.getByText("No holdings yet")).toBeVisible(); expect(screen.getByRole("link", { name: "Explore Markets" })).toHaveAttribute("href", "/");
});
it("retains valid values after refresh failure and preserves retry focus through recovery", async () => {
  const p = cashPortfolio(); vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(p))).mockResolvedValueOnce(new Response("{}", { status: 500 })).mockImplementation(() => Promise.resolve(new Response(JSON.stringify(p)))));
  const { user } = mount(); await screen.findByRole("region", { name: "Cash" });
  const refresh = screen.getByRole("button", { name: "Refresh portfolio" }); await user.click(refresh);
  expect(await screen.findByRole("alert")).toHaveTextContent("Only still-permitted values"); expect(refresh).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Retry refresh" }));
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull()); expect(refresh).toHaveFocus();
});
it("loading and initial error recovery retain a reachable retry", async () => {
  let finish!: (r: Response) => void;
  vi.stubGlobal("fetch", vi.fn().mockImplementationOnce(() => new Promise<Response>(r => { finish = r; })).mockImplementation(() => Promise.resolve(new Response(JSON.stringify(cashPortfolio())))));
  const { user } = mount(); expect(screen.getByRole("status", { name: "Loading your portfolio" })).toHaveAttribute("aria-busy", "true");
  await act(async () => finish(new Response("{}", { status: 500 })));
  expect(await screen.findByRole("alert")).toHaveTextContent("Can't load your portfolio right now");
  await user.click(screen.getByRole("button", { name: "Try again" })); expect(await screen.findByRole("region", { name: "Cash" })).toBeVisible();
});
it("in-flight refresh cannot be submitted twice and keeps cash visible", async () => {
  let finish!: (r: Response) => void; const p = cashPortfolio();
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(p))).mockImplementation(() => new Promise<Response>(r => { finish = r; })); vi.stubGlobal("fetch", fetch);
  const { user } = mount(); await screen.findByRole("region", { name: "Cash" });
  await user.click(screen.getByRole("button", { name: "Refresh portfolio" })); const refresh = screen.getByRole("button", { name: "Refreshing portfolio…" });
  expect(refresh).toHaveAttribute("aria-disabled", "true"); await user.click(refresh); await user.keyboard("{Enter} "); expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$10,000.00"); await act(async () => finish(new Response(JSON.stringify(p))));
});
it.each(["-1", "100.01", "101", "1e2", "1%;color:red", "Infinity"])("rejects unsafe CSS allocations %s", percent => {
  const p = cashPortfolio(); p.class_allocation_percent = { cash: percent, stocks: null, crypto: null };
  render(<PortfolioAllocation portfolio={p} />); expect(document.querySelector("[data-allocation-fill]")).toBeNull();
});
it("zero denominator is unavailable while positive raw values rounded to zero retain server allocations", async () => {
  const p = cashPortfolio(); Object.assign(p, { cash: "0", total_value: "0", known_value: "0", total_pl: "-10000", total_pl_percent: "-100", cash_allocation_percent: null, class_values: { cash: "0", stocks: "0", crypto: "0" }, class_allocation_percent: { cash: null, stocks: null, crypto: null } }); show(p);
  expect(await screen.findByText("Allocation is unavailable while total portfolio value is zero.")).toBeVisible(); expect(document.querySelector("[data-allocation-fill]")).toBeNull();
});
it("long names and huge server values wrap and untrusted names stay escaped", async () => {
  const p = mixedPortfolio(); p.holdings[0].name = '<img src=x onerror="alert(1)">' + "Long company name ".repeat(25); p.holdings[0].current_value = "12345678901234567890123456789012345678.99"; show(p);
  const table = await screen.findByRole("table", { name: "Holdings" }); expect(table).toHaveClass("table-fixed"); expect(table.querySelector("img")).toBeNull(); expect(table).toHaveTextContent("12,345,678,901,234,567,890,123,456,789,012,345,678.99");
});
