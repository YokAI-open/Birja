import { act, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import PortfolioPage from "./PortfolioPage";

const payload = {
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
