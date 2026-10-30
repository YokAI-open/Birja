import { act, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import PortfolioPage from "./PortfolioPage";
import type { Portfolio, PortfolioHolding } from "@/api/portfolio";

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
