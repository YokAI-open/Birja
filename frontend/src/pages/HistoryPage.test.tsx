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

it("cancels the first page when the view unmounts", () => {
  let signal: AbortSignal | undefined;
  vi.stubGlobal("fetch", (_url: string, init: RequestInit) => {
    signal = init.signal as AbortSignal;
    return new Promise(() => {});
  });
  const { unmount } = renderWithClient(<HistoryPage />);
  expect(signal?.aborted).toBe(false);
  unmount();
  expect(signal?.aborted).toBe(true);
});

it("disables Refresh while retaining the stored fills during an in-flight refresh", async () => {
  let resolve: (value: Response) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() => ok())
      .mockImplementation(
        () =>
          new Promise<Response>((done) => {
            resolve = done;
          }),
      ),
  );
  const { user } = renderWithClient(<HistoryPage />);
  await screen.findByRole("table");
  await user.click(screen.getByRole("button", { name: "Refresh history" }));
  expect(screen.getByRole("button", { name: "Refreshing history…" })).toBeDisabled();
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  resolve(new Response(JSON.stringify({ items: [item], next_cursor: null })));
  await vi.waitFor(() =>
    expect(screen.getByRole("button", { name: "Refresh history" })).toBeEnabled(),
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
    "Total cash change",
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

it("appends three ordered pages once, retries the same cursor and transfers final button focus", async () => {
  let finish: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => ok([item], "opaque_A-1"))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((done) => {
          finish = done;
        }),
    )
    .mockResolvedValueOnce(new Response("{}", { status: 500 }))
    .mockImplementationOnce(() =>
      ok([{ ...item, id: "9007199254740992", name: "Second" }], "opaque_B-2"),
    )
    .mockImplementationOnce(() => ok([{ ...item, id: "9007199254740991", name: "Third" }]));
  vi.stubGlobal("fetch", fetch);
  const { user } = renderWithClient(<HistoryPage />);
  const button = await screen.findByRole("button", { name: "Load more" });
  await user.dblClick(button);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("button", { name: "Loading more trades…" })).toBeDisabled();
  finish(new Response("{}", { status: 500 }));
  await user.click(await screen.findByRole("button", { name: "Try loading more" }));
  expect(await screen.findByRole("button", { name: "Try loading more" })).toBeEnabled();
  expect(
    screen.queryByText("Couldn't refresh your trade history. Showing the last successful update."),
  ).toBeNull();
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  await user.click(screen.getByRole("button", { name: "Try loading more" }));
  await vi.waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent("1 more trades loaded. 2 trades shown."),
  );
  expect(button).toHaveFocus();
  expect(screen.queryByText("All trades loaded.")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Load more" }));
  const end = await screen.findByText("All trades loaded.");
  expect(end).toHaveFocus();
  expect(end).toHaveAttribute("tabindex", "-1");
  expect(
    within(screen.getByRole("table"))
      .getAllByRole("row")
      .slice(1)
      .map((row) => row.textContent),
  ).toEqual([
    expect.stringContaining("Bitcoin"),
    expect.stringContaining("Second"),
    expect.stringContaining("Third"),
  ]);
  expect(fetch.mock.calls.map((args) => String(args[0]))).toEqual([
    "/api/v1/trades",
    "/api/v1/trades?cursor=opaque_A-1",
    "/api/v1/trades?cursor=opaque_A-1",
    "/api/v1/trades?cursor=opaque_A-1",
    "/api/v1/trades?cursor=opaque_B-2",
  ]);
});

it("disables append during background refresh and preserves focus elsewhere on exhaustion", async () => {
  let finish: (value: Response) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() => ok([item], "old_boundary"))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((done) => {
            finish = done;
          }),
      ),
  );
  const { user } = renderWithClient(<HistoryPage />);
  await screen.findByRole("button", { name: "Load more" });
  const refresh = screen.getByRole("button", { name: "Refresh history" });
  await user.click(refresh);
  expect(screen.getByRole("button", { name: "Load more" })).toBeDisabled();
  finish(new Response(JSON.stringify({ items: [item], next_cursor: null })));
  await screen.findByText("All trades loaded.");
  expect(refresh).toHaveFocus();
});
