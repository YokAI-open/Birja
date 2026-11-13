import { afterEach, expect, it, vi } from "vitest";
import { act, screen, within } from "@testing-library/react";
import { renderWithClient } from "@/test/render";
import HistoryPage from "./HistoryPage";
import type {
  EventDividend,
  EventDividendCorrection,
  EventHistoryItem,
  EventTrade,
} from "@/api/eventHistory";
import { useQueryClient } from "@tanstack/react-query";

const item: EventTrade = {
  kind: "trade",
  asset_type: "crypto",
  id: "trade:9007199254740993",
  recorded_at: "2026-10-30T08:01:02.123456Z",
  symbol: "BTC",
  name: "Bitcoin",
  side: "buy",
  quantity: "0.00000001",
  exec_price: "123.45678901",
  fee: "0.25",
  cash_delta: "-100.00",
  filled_at: "2026-10-30T08:01:02.123456Z",
  source: null,
  feed: null,
  quote_at: null,
};
const cursor = (id = item.id) =>
  btoa(
    JSON.stringify({
      v: 2,
      recorded_at: item.recorded_at,
      kind_rank: 4,
      source_id: id.split(":")[1],
    }),
  )
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
function historyFetch(fetch: typeof globalThis.fetch) {
  vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) =>
    String(input) === "/api/v1/me"
      ? Promise.resolve(
          new Response(JSON.stringify({ email: "history@example.test", cash_usd: "10000.00" })),
        )
      : fetch(input, init),
  );
}
const ok = (items: EventHistoryItem[] = [item], next_cursor: string | null = null) =>
  Promise.resolve(
    new Response(
      JSON.stringify({
        items,
        next_cursor: next_cursor === null ? null : cursor(items.at(-1)!.id),
      }),
    ),
  );
it("renders the mixed Account activity heading", async () => {
  historyFetch(() => ok([]));
  renderWithClient(<HistoryPage />);
  expect(await screen.findByRole("heading", { name: "Account activity" })).toBeVisible();
});
afterEach(() => vi.unstubAllGlobals());
it("reserves the initial loading region", () => {
  historyFetch(() => new Promise(() => {}));
  renderWithClient(<HistoryPage />);
  expect(screen.getByRole("status", { name: "Loading history" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
});

it("cancels the first page when the view unmounts", async () => {
  let signal: AbortSignal | undefined;
  historyFetch((_url, init) => {
    signal = init?.signal as AbortSignal;
    return new Promise(() => {});
  });
  const { unmount } = renderWithClient(<HistoryPage />);
  await vi.waitFor(() => expect(signal?.aborted).toBe(false));
  unmount();
  expect(signal?.aborted).toBe(true);
});

it("keeps Refresh focusable and blocks repeated activation during an in-flight refresh", async () => {
  let resolve: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => ok())
    .mockImplementation(
      () =>
        new Promise<Response>((done) => {
          resolve = done;
        }),
    );
  historyFetch(fetch);
  const { user } = renderWithClient(<HistoryPage />);
  await screen.findByRole("table");
  await user.click(screen.getByRole("button", { name: "Refresh history" }));
  const refresh = screen.getByRole("button", { name: "Refreshing history…" });
  expect(refresh).toBeEnabled();
  expect(refresh).toHaveAttribute("aria-disabled", "true");
  expect(refresh).toHaveFocus();
  await user.click(refresh);
  await user.keyboard("{Enter} ");
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  resolve(new Response(JSON.stringify({ items: [item], next_cursor: null })));
  await vi.waitFor(() =>
    expect(screen.getByRole("button", { name: "Refresh history" })).toBeEnabled(),
  );
  await vi.waitFor(() => expect(refresh).toHaveAttribute("aria-disabled", "false"));
  expect(refresh).toHaveFocus();
});
it.each([
  ["Try again", false],
  ["Retry refresh", false],
  ["Retry refresh", true],
] as const)(
  "preserves %s focus through retry and recovery (move focus: %s)",
  async (label, moveFocus) => {
    let finish!: (response: Response) => void;
    const fetch = vi.fn();
    if (label === "Retry refresh") fetch.mockImplementationOnce(() => ok());
    fetch.mockResolvedValueOnce(new Response("{}", { status: 500 })).mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    historyFetch(fetch);
    const { user } = renderWithClient(<HistoryPage />);
    if (label === "Retry refresh") {
      await screen.findByRole("table");
      await user.click(screen.getByRole("button", { name: "Refresh history" }));
    }
    const retry = await screen.findByRole("button", { name: label });
    await user.click(retry);
    const refresh = screen.getByRole("button", { name: "Refreshing history…" });
    expect(refresh).toHaveAttribute("aria-disabled", "true");
    const count = fetch.mock.calls.length;
    if (label === "Retry refresh") {
      expect(retry).toHaveFocus();
      expect(retry).toHaveAttribute("aria-disabled", "true");
      await user.click(retry);
      await user.keyboard("{Enter} ");
    } else {
      expect(refresh).toHaveFocus();
    }
    expect(fetch).toHaveBeenCalledTimes(count);
    if (moveFocus) await user.tab();
    const focused = document.activeElement;
    await act(async () => finish(await ok()));
    await vi.waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    if (moveFocus) expect(document.activeElement).toBe(focused);
    else expect(refresh).toHaveFocus();
  },
);

it("renders stored values in desktop and labelled mobile views without a false end message", async () => {
  const fetch = vi.fn(() =>
    ok(
      [
        item,
        { ...item, id: "trade:2", side: "sell", cash_delta: "99.50" },
        { ...item, id: "trade:1", side: "sell", cash_delta: "0.00" },
      ],
      cursor(),
    ),
  );
  historyFetch(fetch);
  renderWithClient(<HistoryPage />);
  const table = await screen.findByRole("table", { name: "Account activity" });
  const mobile = screen.getByRole("list", { name: "Account activity" });
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
    expect(within(view).getAllByRole("time")[0]).toHaveAttribute("title", item.recorded_at);
  }
  for (const label of ["Recorded", "Event", "Asset", "Details", "Cash change"]) {
    expect(within(mobile).getAllByText(label, { selector: "dt" })).toHaveLength(3);
  }
  expect(screen.queryByText("All events loaded.")).toBeNull();
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("shows only successful empty responses as empty", async () => {
  historyFetch(() => ok([]));
  renderWithClient(<HistoryPage />);
  expect(await screen.findByText("No activity yet")).toBeVisible();
  expect(screen.getByRole("link", { name: "Browse markets" })).toHaveAttribute("href", "/");
});
it("retries an initial error", async () => {
  historyFetch(
    vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 500 }))
      .mockImplementation(() => ok()),
  );
  const { user } = renderWithClient(<HistoryPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Can't load your history right now. Try again.",
  );
  expect(screen.queryByText("No activity yet")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("table", { name: "Account activity" })).toHaveTextContent(
    "−$100.00",
  );
});
it("retains fills after failed refresh and can retry", async () => {
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => ok())
    .mockResolvedValueOnce(new Response("{}", { status: 500 }))
    .mockImplementation(() => ok());
  historyFetch(fetch);
  const { user } = renderWithClient(<HistoryPage />);
  await screen.findByRole("table");
  await user.click(screen.getByRole("button", { name: "Refresh history" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Couldn't refresh your history. Showing the last successful update.",
  );
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  await user.click(screen.getByRole("button", { name: "Retry refresh" }));
  await vi.waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
});

it("appends three ordered pages once, retries the same cursor and transfers final button focus", async () => {
  let finish: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => ok([item], cursor()))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((done) => {
          finish = done;
        }),
    )
    .mockResolvedValueOnce(new Response("{}", { status: 500 }))
    .mockImplementationOnce(() =>
      ok(
        [{ ...item, id: "trade:9007199254740992", name: "Second" }],
        cursor("trade:9007199254740992"),
      ),
    )
    .mockImplementationOnce(() => ok([{ ...item, id: "trade:9007199254740991", name: "Third" }]));
  historyFetch(fetch);
  const { user } = renderWithClient(<HistoryPage />);
  const button = await screen.findByRole("button", { name: "Load more" });
  await user.dblClick(button);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("button", { name: "Loading more events…" })).toBeDisabled();
  finish(new Response("{}", { status: 500 }));
  await user.click(await screen.findByRole("button", { name: "Try loading more" }));
  expect(await screen.findByRole("button", { name: "Try loading more" })).toBeEnabled();
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Couldn't load more events. Your loaded events are still here.",
  );
  expect(
    screen.queryByText("Couldn't refresh your history. Showing the last successful update."),
  ).toBeNull();
  expect(screen.getByRole("table")).toHaveTextContent("−$100.00");
  await user.click(screen.getByRole("button", { name: "Try loading more" }));
  await vi.waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent("1 more events loaded. 2 events shown."),
  );
  expect(button).toHaveFocus();
  expect(screen.queryByText("All events loaded.")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Load more" }));
  const end = await screen.findByText("All events loaded.");
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
    "/api/v1/history",
    `/api/v1/history?cursor=${cursor()}`,
    `/api/v1/history?cursor=${cursor()}`,
    `/api/v1/history?cursor=${cursor()}`,
    `/api/v1/history?cursor=${cursor("trade:9007199254740992")}`,
  ]);
});

it("disables append during background refresh and preserves focus elsewhere on exhaustion", async () => {
  let finish: (value: Response) => void = () => {};
  historyFetch(
    vi
      .fn()
      .mockImplementationOnce(() => ok([item], cursor()))
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
  await screen.findByText("All events loaded.");
  expect(refresh).toHaveFocus();
});

it("preserves append focus intent when a native disabled control blurs before final publication", async () => {
  let finish: (value: Response) => void = () => {};
  historyFetch(
    vi
      .fn()
      .mockImplementationOnce(() => ok([item], cursor()))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((done) => {
            finish = done;
          }),
      ),
  );
  const { user } = renderWithClient(<HistoryPage />);
  const append = await screen.findByRole("button", { name: "Load more" });
  await user.click(append);
  expect(append).toBeDisabled();
  // JSDOM retains native disabled focus, unlike Chromium. Explicitly model
  // that browser blur while preserving the original keyboard activation.
  document.body.tabIndex = -1;
  document.body.focus();
  document.body.removeAttribute("tabindex");
  expect(document.body).toHaveFocus();
  finish(new Response(JSON.stringify({ items: [{ ...item, id: "trade:2" }], next_cursor: null })));
  expect(await screen.findByText("All events loaded.")).toHaveFocus();
});

it("keeps focus on another control when append finishes and refresh announces the current count", async () => {
  let finish: (value: Response) => void = () => {};
  historyFetch(
    vi
      .fn()
      .mockImplementationOnce(() => ok([item], cursor()))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((done) => {
            finish = done;
          }),
      )
      .mockImplementationOnce(() => ok([item])),
  );
  const { user } = renderWithClient(<HistoryPage />);
  await user.click(await screen.findByRole("button", { name: "Load more" }));
  const region = screen.getByRole("region", { name: "Account activity table" });
  region.focus();
  finish(new Response(JSON.stringify({ items: [{ ...item, id: "trade:2" }], next_cursor: null })));
  await screen.findByText("All events loaded.");
  expect(region).toHaveFocus();
  expect(screen.getByRole("status")).toHaveTextContent("1 more events loaded. 2 events shown.");
  await user.click(screen.getByRole("button", { name: "Refresh history" }));
  await vi.waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(/^1 events shown\.$/),
  );
});

const dividend: EventDividend = {
  kind: "dividend",
  id: "dividend:1",
  payment_reference: "dividend:1",
  recorded_at: "2026-11-12T15:00:00.000001Z",
  credited_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "A very long saved company name ".repeat(7),
  cash_delta: "1.00",
  credited_amount: "1.00",
  eligible_quantity: "100000000",
  rate: "0.00000001",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: "2026-11-10",
  record_date: null,
  payable_date: "2026-11-12",
};
const held: EventDividendCorrection = {
  kind: "dividend_correction",
  id: "dividend_correction:2",
  decision_reference: "dividend_correction:2",
  recorded_at: dividend.recorded_at,
  asset_type: "stock",
  symbol: "AAPL",
  name: dividend.name,
  cash_delta: "0.00",
  payment_reference: dividend.id,
  outcome: "held_uncertain",
  reason: "terms_unverified",
  desired_total: null,
  cumulative_applied_before: "1.00",
  proposed_delta: null,
  applied_delta: "0.00",
  terms: null,
  original: dividend,
};

it("renders all mixed kinds in server order with the five approved columns and loaded original navigation", async () => {
  const crypto = { ...item, recorded_at: dividend.recorded_at, filled_at: dividend.recorded_at };
  const split = {
    kind: "split",
    id: "split:1",
    recorded_at: dividend.recorded_at,
    asset_type: "stock",
    symbol: "AAPL",
    name: "AAPL",
    cash_delta: "0.00",
    ratio_new: "3",
    ratio_old: "2",
    quantity_before: "2",
    quantity_after: "3",
    cost_basis_before: "100.00",
    cost_basis_after: "100.00",
    effective_at: dividend.cutoff,
  } as const;
  historyFetch(() => ok([crypto, dividend, split, held]));
  const { user } = renderWithClient(<HistoryPage />);
  const table = await screen.findByRole("table");
  expect(
    within(table)
      .getAllByRole("columnheader")
      .map((node) => node.textContent),
  ).toEqual(["Recorded", "Event", "Asset", "Details", "Cash change"]);
  const rows = within(table).getAllByRole("row").slice(1);
  expect(rows.map((row) => row.id)).toEqual([
    `history-desktop-${crypto.id}`,
    `history-desktop-${dividend.id}`,
    `history-desktop-${split.id}`,
    `history-desktop-${held.id}`,
  ]);
  expect(table).toHaveTextContent("USD 0.00000001 per share");
  expect(table).toHaveTextContent("Held when recorded");
  expect(table).toHaveTextContent(
    "The corrected dividend terms need verification. No cash changed.",
  );
  expect(table).toHaveTextContent("Crypto");
  expect(table).toHaveTextContent("Stock");
  expect(rows[1]).toHaveTextContent(dividend.name.trim());
  await user.click(within(table).getByRole("button", { name: "View original dividend" }));
  expect(rows[1]).toHaveFocus();
  expect(screen.queryByRole("button", { name: "Back to correction" })).not.toBeInTheDocument();
});

function SignOut() {
  const client = useQueryClient();
  return <button onClick={() => client.setQueryData(["me"], null)}>Test sign out</button>;
}

it("removes offpage original details immediately on logout", async () => {
  historyFetch(() => ok([held]));
  const { user } = renderWithClient(
    <>
      <HistoryPage />
      <SignOut />
    </>,
  );
  const table = await screen.findByRole("table");
  await user.click(within(table).getByRole("button", { name: "View original dividend" }));
  const heading = screen.getByRole("heading", { name: /^Original dividend/ });
  expect(heading).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Test sign out" }));
  expect(screen.queryByRole("table")).not.toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: /^Original dividend/ })).not.toBeInTheDocument();
  expect(screen.queryByText(dividend.payment_reference)).not.toBeInTheDocument();
});
