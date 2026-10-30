import { afterEach, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithClient } from "@/test/render";
import HistoryPage from "./HistoryPage";

const item = {
  id: "9007199254740993",
  created_at: "2026-10-30T08:01:02.123456Z",
  symbol: "BTC",
  name: "Bitcoin",
  side: "buy",
  quantity: "0.00000001",
  exec_price: "123.45678901",
  fee: "0.25",
  total: "-100.00",
};
const ok = (items = [item], next_cursor: string | null = null) =>
  Promise.resolve(new Response(JSON.stringify({ items, next_cursor })));
afterEach(() => vi.unstubAllGlobals());
it("reserves the initial loading region", () => {
  vi.stubGlobal("fetch", () => new Promise(() => {}));
  renderWithClient(<HistoryPage />);
  expect(screen.getByRole("status", { name: "Loading trade history" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
});
it("renders stored values in desktop and labelled mobile views without a false end message", async () => {
  const fetch = vi.fn(() =>
    ok(
      [
        item,
        { ...item, id: "2", side: "sell", total: "99.50" },
        { ...item, id: "1", side: "sell", total: "0.00" },
      ],
      "more",
    ),
  );
  vi.stubGlobal("fetch", fetch);
  renderWithClient(<HistoryPage />);
  const table = await screen.findByRole("table", { name: "Trade history" });
  const mobile = screen.getByRole("list", { name: "Trade history" });
  for (const view of [table, mobile]) {
    expect(view).toHaveTextContent("Bitcoin");
    expect(view).toHaveTextContent("Buy");
    expect(view).toHaveTextContent("Sell");
    expect(view).toHaveTextContent("−$100.00");
    expect(view).toHaveTextContent("+$99.50");
    expect(view).toHaveTextContent("$0.00");
    expect(view).toHaveTextContent("0.00000001");
    expect(view).toHaveTextContent("$123.46");
    expect(view).toHaveTextContent("$0.25");
    expect(within(view).getAllByRole("time")[0]).toHaveAttribute("title", item.created_at);
  }
  for (const label of [
    "Date/time",
    "Coin",
    "Side",
    "Quantity",
    "Execution price",
    "Fee",
    "Total",
  ]) {
    expect(within(mobile).getAllByText(label, { selector: "dt" })).toHaveLength(3);
  }
  expect(screen.queryByText("All trades loaded.")).toBeNull();
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("shows only successful empty responses as empty", async () => {
  vi.stubGlobal("fetch", () => ok([]));
  renderWithClient(<HistoryPage />);
  expect(await screen.findByText("No trades yet")).toBeVisible();
  expect(screen.getByRole("link", { name: "Browse markets" })).toHaveAttribute("href", "/");
});
it("retries an initial error", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 500 }))
      .mockImplementation(() => ok()),
  );
  const { user } = renderWithClient(<HistoryPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Can't load your trade history right now. Try again.",
  );
  expect(screen.queryByText("No trades yet")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("table", { name: "Trade history" })).toHaveTextContent("−$100.00");
});
it("retains fills after failed refresh and can retry", async () => {
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => ok())
    .mockResolvedValueOnce(new Response("{}", { status: 500 }))
    .mockImplementation(() => ok());
  vi.stubGlobal("fetch", fetch);
  const { user } = renderWithClient(<HistoryPage />);
  await screen.findByRole("table");
  await user.click(screen.getByRole("button", { name: "Refresh history" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Couldn't refresh your trade history. Showing the last successful update.",
  );
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  await user.click(screen.getByRole("button", { name: "Retry refresh" }));
  await vi.waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
});
