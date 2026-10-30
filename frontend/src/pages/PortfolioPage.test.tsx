import { act, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import PortfolioPage from "./PortfolioPage";
import type { Portfolio, PortfolioHolding } from "@/api/portfolio";
import { PortfolioAllocation } from "@/components/PortfolioAllocation";

const payload: Portfolio = {
  cash: "9999.00",
  starting_cash: "10000.00",
  total_value: "9999.00",
  total_pl: "-1.00",
  total_pl_percent: "-0.01",
  cash_allocation_percent: "100.00",
  valuation_complete: true,
  valued_at: "2026-10-29T10:00:00Z",
  prices_as_of: null,
  fresh_seconds: 120,
  stale_seconds: 300,
  holdings: [],
};
const holding: PortfolioHolding = {
  symbol: "BTC",
  name: "Bitcoin",
  is_active: true,
  quantity: "0.00099501",
  cost_basis: "100.00",
  average_cost: "100501.50249746",
  mid: "100000.00000000",
  current_value: "99.50",
  unrealized_pl: "-0.50",
  unrealized_pl_percent: "-0.50",
  allocation_percent: "1.00",
  as_of: "2026-10-29T10:00:00Z",
  age_seconds: 10,
  status: "fresh",
};
const ok = (body = payload) => Promise.resolve(new Response(JSON.stringify(body)));
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

it("announces only meaningful freshness transitions while retained prices keep aging", async () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2035-01-01T00:00:00Z"));
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() =>
        ok({
          ...payload,
          prices_as_of: holding.as_of,
          holdings: [{ ...holding, age_seconds: 118 }],
        }),
      )
      .mockResolvedValue(new Response("{}", { status: 500 })),
  );
  renderWithClient(<PortfolioPage />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10);
  });
  const status = screen.getByRole("status");
  expect(status).toHaveAttribute("aria-atomic", "true");
  expect(status).toHaveTextContent("Live");
  const initial = status.textContent;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(status.textContent).toBe(initial);
  expect(screen.getAllByText("Live · 1m ago")).toHaveLength(2);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(status).toHaveTextContent("Some prices are delayed. Values use the last known prices.");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(180_000);
  });
  expect(screen.getAllByText("Delayed · 5m ago")).toHaveLength(2);
  expect(screen.getAllByRole("alert")).toHaveLength(1);
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$9,999.00");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(status).toHaveTextContent(
    "Some prices are out of date. Values use the last known prices.",
  );
  expect(screen.getAllByText("Stale · 5m ago")).toHaveLength(2);
  expect(screen.getAllByRole("status")).toHaveLength(1);
});

it("uses configured boundaries and keeps incomplete valuation ahead of stale warnings", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        valuation_complete: false,
        total_value: null,
        total_pl: null,
        total_pl_percent: null,
        cash_allocation_percent: null,
        prices_as_of: holding.as_of,
        fresh_seconds: 5,
        stale_seconds: 8,
        holdings: [
          { ...holding, age_seconds: 9, allocation_percent: null, is_active: false },
          {
            ...holding,
            symbol: "ETH",
            mid: null,
            as_of: null,
            age_seconds: null,
            current_value: null,
            unrealized_pl: null,
            unrealized_pl_percent: null,
            allocation_percent: null,
            status: "unpriced",
          },
        ],
      }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  await screen.findByText("Value unavailable");
  expect(screen.getByRole("status")).toHaveTextContent("Valuation incomplete");
  expect(
    screen.queryByText("Some prices are out of date. Values use the last known prices."),
  ).toBeNull();
  expect(screen.getByText(/Oldest available price/, { selector: "p" })).toHaveTextContent("9s ago");
  expect(screen.getAllByText("Stale · 9s ago")).toHaveLength(2);
  expect(screen.getAllByText("Price unavailable")).toHaveLength(2);
  const summary = screen.getByRole("region", { name: "Total portfolio value" });
  const time = summary.querySelector("time");
  expect(time).toHaveAttribute("datetime", holding.as_of);
  expect(time).toHaveAttribute("title", holding.as_of);
  expect(time?.textContent).toBeTruthy();
  expect(time).toHaveAccessibleName(time!.textContent!);
});

it("reports refresh recovery once and preserves manual refresh focus", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() => ok({ ...payload, holdings: [holding] }))
      .mockResolvedValueOnce(new Response("{}", { status: 500 }))
      .mockImplementation(() => ok()),
  );
  const { user } = renderWithClient(<PortfolioPage />);
  await screen.findByRole("region", { name: "Cash" });
  const refresh = screen.getByRole("button", { name: "Refresh portfolio" });
  await user.click(refresh);
  expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't refresh your portfolio");
  expect(refresh).toHaveFocus();
  await user.click(refresh);
  await vi.waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  expect(refresh).toHaveFocus();
  expect(screen.getByRole("status")).toHaveTextContent("Portfolio refreshed.");
  expect(screen.getByText("No market prices needed")).toBeVisible();
});

it("labels an in-flight manual refresh and keeps the existing data visible", async () => {
  let finish!: (response: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() => ok())
      .mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            finish = resolve;
          }),
      ),
  );
  const { user } = renderWithClient(<PortfolioPage />);
  await screen.findByRole("region", { name: "Cash" });
  await user.click(screen.getByRole("button", { name: "Refresh portfolio" }));
  const refresh = screen.getByRole("button", { name: "Refreshing portfolio…" });
  expect(refresh).toBeEnabled();
  expect(refresh).toHaveAttribute("aria-disabled", "true");
  expect(refresh).toHaveFocus();
  await user.click(refresh);
  await user.keyboard("{Enter} ");
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(screen.getByRole("status")).toHaveTextContent("Refreshing portfolio…");
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$9,999.00");
  await act(async () => finish(await ok()));
  expect(await screen.findByRole("button", { name: "Refresh portfolio" })).toBeEnabled();
  expect(refresh).toHaveAttribute("aria-disabled", "false");
  expect(refresh).toHaveFocus();
});

it.each(["Try again", "Retry refresh"])(
  "preserves %s focus through retry and recovery",
  async (label) => {
    let finish!: (response: Response) => void;
    const fetch = vi.fn();
    if (label === "Retry refresh") fetch.mockImplementationOnce(() => ok());
    fetch.mockResolvedValueOnce(new Response("{}", { status: 500 })).mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetch);
    const { user } = renderWithClient(<PortfolioPage />);
    if (label === "Retry refresh") {
      await screen.findByRole("region", { name: "Cash" });
      await user.click(screen.getByRole("button", { name: "Refresh portfolio" }));
    }
    const retry = await screen.findByRole("button", { name: label });
    await user.click(retry);
    const refresh = screen.getByRole("button", { name: "Refreshing portfolio…" });
    expect(refresh).toHaveAttribute("aria-disabled", "true");
    const count = fetch.mock.calls.length;
    if (label === "Retry refresh") {
      expect(retry).toHaveFocus();
      expect(retry).toHaveAttribute("aria-disabled", "true");
      await user.click(retry);
      await user.keyboard("{Enter} ");
      expect(fetch).toHaveBeenCalledTimes(count);
    } else {
      expect(refresh).toHaveFocus();
      await user.click(refresh);
    }
    expect(fetch).toHaveBeenCalledTimes(count);
    await act(async () => finish(await ok()));
    await vi.waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(refresh).toHaveFocus();
  },
);

it("shows actual liquidated cash and return against stored starting cash", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => ok()),
  );
  renderWithClient(<PortfolioPage />);
  const summary = await screen.findByRole("region", { name: "Total portfolio value" });
  expect(within(summary).getByText("$9,999.00")).toBeVisible();
  expect(within(summary).getByText(/−\$1.00/)).toBeVisible();
  expect(screen.getByText("Compared with your $10,000.00 start")).toBeVisible();
  expect(screen.getByText("No market prices needed")).toBeVisible();
  expect(within(screen.getByRole("region", { name: "Cash" })).getByText("$9,999.00")).toBeVisible();
});

it("reserves loading shapes then offers an initial error retry", async () => {
  let resolve!: (response: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(
        () =>
          new Promise<Response>((r) => {
            resolve = r;
          }),
      )
      .mockImplementation(() => ok()),
  );
  const { user } = renderWithClient(<PortfolioPage />);
  expect(screen.getByRole("status", { name: "Loading your portfolio" })).toBeVisible();
  await act(async () => resolve(new Response("{}", { status: 500 })));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Can't load your portfolio right now. Try again.",
  );
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("region", { name: "Cash" })).toBeVisible();
});

it("retains successful values and retries a failed refresh", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() => ok())
      .mockResolvedValueOnce(new Response("{}", { status: 500 }))
      .mockImplementation(() => ok()),
  );
  const { user } = renderWithClient(<PortfolioPage />);
  await screen.findByRole("region", { name: "Cash" });
  await user.click(screen.getByRole("button", { name: "Refresh portfolio" }));
  expect(
    await screen.findByText("Couldn't refresh your portfolio. Showing the last successful update."),
  ).toBeVisible();
  expect(screen.getByRole("region", { name: "Cash" })).toHaveTextContent("$9,999.00");
  await user.click(screen.getByRole("button", { name: "Retry refresh" }));
  await vi.waitFor(() => expect(screen.queryByText(/Couldn't refresh/)).toBeNull());
});

it("renders missing valuation immediately without invented numeric defaults", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        valuation_complete: false,
        total_value: null,
        total_pl: null,
        total_pl_percent: null,
        cash_allocation_percent: null,
      } as unknown as typeof payload),
    ),
  );
  renderWithClient(<PortfolioPage />);
  expect(await screen.findByText("Value unavailable")).toBeVisible();
  expect(
    screen.getByText(
      "Some holdings have no price. Total value, profit/loss and allocation are unavailable until prices return.",
    ),
  ).toBeVisible();
});

it("shows every holding field in semantic desktop and mobile representations", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => ok({ ...payload, holdings: [holding] })),
  );
  renderWithClient(<PortfolioPage />);
  const table = await screen.findByRole("table", { name: "Holdings" });
  expect(table.parentElement).toHaveAttribute("tabindex", "0");
  expect(table.parentElement).toHaveClass("hidden", "md:block", "overflow-x-auto");
  expect(
    within(table)
      .getAllByRole("columnheader")
      .map((h) => h.textContent),
  ).toEqual([
    "Coin",
    "Quantity",
    "Average cost",
    "Mid price",
    "Current value",
    "Unrealized P/L",
    "Allocation",
    "Price updated",
    "Trade",
  ]);
  expect(within(table).getByRole("rowheader")).toHaveTextContent("BTCBitcoin");
  const mobile = screen.getByRole("list", { name: "Holdings" });
  expect(mobile).toHaveClass("md:hidden");
  for (const view of [table, mobile]) {
    expect(view).toHaveTextContent("0.00099501");
    expect(view).toHaveTextContent("$100,501.50");
    expect(view).toHaveTextContent("$100,000.00");
    expect(view).toHaveTextContent("$99.50");
    expect(view).toHaveTextContent("−$0.50");
    expect(view).toHaveTextContent("−0.50%");
    expect(view).toHaveTextContent("1.00%");
    expect(view.querySelector("time")).toHaveAttribute("datetime", holding.as_of);
    expect(view.querySelector("time")).toHaveAttribute("title", holding.as_of);
    expect(view.querySelector("time")).toHaveAccessibleName();
    expect(within(view).getByRole("link", { name: "Trade BTC" })).toHaveAttribute(
      "href",
      "/trade/BTC",
    );
  }
  for (const label of [
    "Quantity",
    "Average cost",
    "Mid price",
    "Unrealized P/L",
    "Allocation",
    "Price updated",
  ]) {
    expect(within(mobile).getByText(label, { selector: "dt" })).toBeInTheDocument();
  }
  expect(
    screen.getByText("Average cost includes buy fees. Values use market mid prices."),
  ).toBeVisible();
});

it("distinguishes zero basis, unknown prices, inactive positions and rounded-zero outcomes", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        holdings: [
          {
            ...holding,
            cost_basis: "0.00",
            average_cost: "0.00000000",
            unrealized_pl: "99.50",
            unrealized_pl_percent: null,
            is_active: false,
          },
          {
            ...holding,
            symbol: "ETH",
            name: "Ethereum",
            mid: null,
            current_value: null,
            unrealized_pl: null,
            unrealized_pl_percent: null,
            as_of: null,
            age_seconds: null,
            status: "unpriced",
          },
          { ...holding, symbol: "SOL", unrealized_pl_percent: "0.00" },
        ],
      }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  const table = await screen.findByRole("table", { name: "Holdings" });
  const rows = within(table).getAllByRole("row").slice(1);
  expect(rows[0]).toHaveTextContent("$0.00");
  expect(rows[0]).toHaveTextContent("+$99.50");
  expect(rows[0]).toHaveTextContent("Not applicable");
  expect(rows[0]).toHaveTextContent("Percentage return is unavailable because cost basis is zero.");
  expect(rows[0]).toHaveTextContent("Inactive · trading unavailable");
  expect(within(rows[0]!).queryByRole("link")).toBeNull();
  expect(rows[1]).toHaveTextContent("Price unavailable");
  expect(rows[1]).not.toHaveTextContent("Not applicable");
  expect(within(rows[1]!).getAllByText("Unavailable").length).toBeGreaterThanOrEqual(4);
  expect(rows[2]).toHaveTextContent("Loss:");
  expect(rows[2]).toHaveTextContent("No change: 0.00%");
  expect(rows[2]).not.toHaveTextContent("Gain:");
});

it("offers Browse markets only for a successful empty holdings response", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => ok()),
  );
  renderWithClient(<PortfolioPage />);
  expect(await screen.findByText("No holdings yet")).toBeVisible();
  expect(
    screen.getByText("Your cash is available to trade. Browse markets to choose a coin."),
  ).toBeVisible();
  expect(screen.getByRole("link", { name: "Browse markets" })).toHaveAttribute("href", "/");
});

it("shows cash and each position allocation directly from the server", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        cash: "9000.00",
        total_value: "10000.00",
        cash_allocation_percent: "90.00",
        holdings: [{ ...holding, current_value: "1000.00", allocation_percent: "10.00" }],
      }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  const list = await screen.findByRole("list", { name: "Allocation" });
  const rows = within(list).getAllByRole("listitem");
  expect(rows).toHaveLength(2);
  expect(rows[0]).toHaveTextContent("Cash90.00%");
  expect(rows[1]).toHaveTextContent("BTC · Bitcoin10.00%");
  expect(rows[0]!.querySelector("[data-allocation-fill]")).toHaveStyle({ width: "90.00%" });
  expect(rows[1]!.querySelector("[data-allocation-fill]")).toHaveStyle({ width: "10.00%" });
  for (const row of rows) {
    expect(row.querySelector("[aria-hidden=true]")).toHaveClass("h-2", "bg-muted");
  }
  expect(screen.getByText("Share of total portfolio value, including cash.")).toBeVisible();
});

it.each(["33.33", "33.34"])("preserves %s allocations without a balancing row", async (percent) => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        cash_allocation_percent: percent,
        holdings: [
          { ...holding, allocation_percent: percent },
          { ...holding, symbol: "ETH", allocation_percent: percent },
        ],
      }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  const list = await screen.findByRole("list", { name: "Allocation" });
  expect(within(list).getAllByText(`${percent}%`)).toHaveLength(3);
  expect(within(list).getAllByRole("listitem")).toHaveLength(3);
});

it("distinguishes known zero allocation from incomplete valuation", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockImplementationOnce(() =>
        ok({ ...payload, cash_allocation_percent: "0.00", holdings: [holding] }),
      )
      .mockImplementation(() =>
        ok({
          ...payload,
          valuation_complete: false,
          total_value: null,
          total_pl: null,
          total_pl_percent: null,
          cash_allocation_percent: null,
          holdings: [{ ...holding, allocation_percent: null }],
        }),
      ),
  );
  const { user } = renderWithClient(<PortfolioPage />);
  const list = await screen.findByRole("list", { name: "Allocation" });
  expect(within(list).getByText("0.00%")).toBeVisible();
  expect(
    within(list).getAllByRole("listitem")[0]!.querySelector("[data-allocation-fill]"),
  ).toHaveStyle({ width: "0.00%" });
  await user.click(screen.getByRole("button", { name: "Refresh portfolio" }));
  await vi.waitFor(() => expect(within(list).getAllByText("Unavailable")).toHaveLength(2));
  expect(list.querySelector("[data-allocation-fill]")).toBeNull();
});

it("explains zero total allocation without displaying a fabricated zero percent", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({ ...payload, cash: "0.00", total_value: "0.00", cash_allocation_percent: null }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  expect(
    await screen.findByText("Allocation is unavailable while total portfolio value is zero."),
  ).toBeVisible();
  const list = screen.getByRole("list", { name: "Allocation" });
  expect(within(list).getByText("Unavailable")).toBeVisible();
  expect(within(list).queryByText("0.00%")).toBeNull();
});

it.each(["-1.00", "100.01", "101", "1e2", "1%;color:red", "Infinity"])(
  "refuses unbounded or malformed CSS allocation %s",
  (percent) => {
    renderWithClient(
      <PortfolioAllocation portfolio={{ ...payload, cash_allocation_percent: percent }} />,
    );
    const list = screen.getByRole("list", { name: "Allocation" });
    expect(within(list).getByText("Unavailable")).toBeVisible();
    expect(list.querySelector("[data-allocation-fill]")).toBeNull();
  },
);

it("keeps allocations known when positive raw value rounds to zero dollars", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      ok({
        ...payload,
        cash: "0.00",
        total_value: "0.00",
        cash_allocation_percent: "0.00",
        holdings: [
          {
            ...holding,
            quantity: "0.00000001",
            current_value: "0.00",
            allocation_percent: "100.00",
          },
        ],
      }),
    ),
  );
  renderWithClient(<PortfolioPage />);
  const list = await screen.findByRole("list", { name: "Allocation" });
  expect(within(list).getByText("100.00%")).toBeVisible();
  expect(
    screen.queryByText("Allocation is unavailable while total portfolio value is zero."),
  ).toBeNull();
});
