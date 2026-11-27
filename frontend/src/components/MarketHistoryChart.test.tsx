import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  type HistoryInstrument,
  type HistoryRange,
  type HistoryResponse,
} from "@/api/marketHistory";
import { useMarketHistory } from "@/hooks/useMarketHistory";
import { MarketHistoryChart } from "./MarketHistoryChart";

const apple = { kind: "featured", symbol: "AAPL" } as const;
const msft = { kind: "featured", symbol: "MSFT" } as const;
const series: NonNullable<HistoryResponse["series"]> = {
  source: "alpaca_iex",
  currency: "USD",
  time_basis: "regular_session",
  adjustment: "split",
  interval_minutes: 30,
  start_at: "2026-11-23T14:30:00Z",
  end_at: "2026-11-24T16:30:00Z",
  expected_through_at: "2026-11-24T16:30:00Z",
  as_of: "2026-11-24T16:00:00Z",
  coverage: "partial",
  timeliness: "delayed",
  points: [
    {
      starts_at: "2026-11-23T14:30:00Z",
      ends_at: "2026-11-23T15:00:00Z",
      close: "12.003450000644",
      gap_before: null,
    },
    {
      starts_at: "2026-11-24T14:30:00Z",
      ends_at: "2026-11-24T15:00:00Z",
      close: "13.50",
      gap_before: "closed",
    },
    {
      starts_at: "2026-11-24T15:30:00Z",
      ends_at: "2026-11-24T16:00:00Z",
      close: "14.00",
      gap_before: "missing",
    },
  ],
  day_change_pct: null,
  period_change_pct: null,
};
const json = (body: unknown) =>
  new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
  });
const empty = (instrument: HistoryInstrument, range: HistoryRange) =>
  json({ instrument, range, state: "unavailable", series: null });

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0";
});

function connect(instrument: typeof apple | typeof msft = apple) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  client.setQueryDefaults(["me"], { gcTime: Infinity });
  client.setQueryData(["me"], { email: "chart@example.test" });
  document.cookie = "bj_csrf=test";
  function History({ target }: { target: typeof instrument }) {
    const [range, setRange] = useState<HistoryRange>("1W");
    const history = useMarketHistory(target, range);
    return (
      <MarketHistoryChart symbol={target.symbol} range={range} onRange={setRange} {...history} />
    );
  }
  const tree = (target: typeof instrument) => (
    <QueryClientProvider client={client}>
      <History target={target} />
    </QueryClientProvider>
  );
  const view = render(tree(instrument));
  return { ...view, client, select: (target: typeof instrument) => view.rerender(tree(target)) };
}

describe("market history chart", () => {
  it("exposes identical precise dates and closes and both kinds of gap in Price data", async () => {
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
    const response: HistoryResponse = { instrument: apple, range: "1W", state: "partial", series };
    render(
      <MarketHistoryChart
        symbol="AAPL"
        range="1W"
        onRange={vi.fn()}
        response={response}
        loading={false}
      />,
    );
    expect(screen.getByText("Some price intervals are missing")).toBeVisible();
    expect(screen.getByText("History behind · As of").querySelector("time")).toHaveAttribute(
      "datetime",
      series.as_of,
    );
    expect(screen.getByText("IEX · Regular sessions · Split-adjusted")).toBeVisible();
    await userEvent.click(screen.getByText("Price data"));
    const table = screen.getByRole("table", { name: "AAPL closing prices · Past week" });
    expect(within(table).getAllByRole("row")).toHaveLength(4);
    const prices = ["$12.003450000644", "$13.50", "$14.00"];
    series.points.forEach((point, index) => {
      expect(table.querySelector(`time[datetime="${point.ends_at}"]`)).toBeInTheDocument();
      expect(within(table).getByText(prices[index])).toBeVisible();
    });
    expect(within(table).getByText("After market close")).toBeVisible();
    expect(within(table).getByText("After missing intervals")).toBeVisible();
  });

  it("defaults to 1W and supports all ranges through the keyboard", async () => {
    const sent: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((_url, init: RequestInit) => {
        const { range } = JSON.parse(String(init.body)) as { range: HistoryRange };
        sent.push(range);
        return Promise.resolve(empty(apple, range));
      }),
    );
    connect();
    await screen.findByText("Couldn’t load price history");
    const ranges = within(screen.getByRole("group", { name: "Price history range" }));
    expect(ranges.getByRole("button", { name: "1W" })).toHaveAttribute("aria-pressed", "true");
    const user = userEvent.setup();
    ranges.getByRole("button", { name: "1D" }).focus();
    await user.keyboard("{Enter}");
    expect(ranges.getByRole("button", { name: "1D" })).toHaveAttribute("aria-pressed", "true");
    await user.tab();
    await user.tab();
    await user.keyboard(" ");
    expect(ranges.getByRole("button", { name: "1M" })).toHaveAttribute("aria-pressed", "true");
    expect(sent).toEqual(["1W", "1D", "1M"]);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("cancels an abandoned instrument and fences replies during session departure", async () => {
    const replies: { signal: AbortSignal; resolve: (response: Response) => void }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url, { signal }: RequestInit) =>
          new Promise<Response>((resolve) => {
            replies.push({ signal: signal!, resolve });
          }),
      ),
    );
    const view = connect();
    await waitFor(() => expect(replies).toHaveLength(1));
    view.select(msft);
    await waitFor(() => expect(replies).toHaveLength(2));
    expect(replies[0].signal.aborted).toBe(true);
    await act(async () => {
      replies[0].resolve(json({ instrument: apple, range: "1W", state: "partial", series }));
      view.client.setQueryData(["me"], null);
    });
    await waitFor(() => expect(replies[1].signal.aborted).toBe(true));
    await act(async () =>
      replies[1].resolve(json({ instrument: msft, range: "1W", state: "partial", series })),
    );
    expect(screen.queryByText("Price data")).not.toBeInTheDocument();
  });

  it("dates a one-day equity chart by its actual regular session", () => {
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
      },
    );
    const response: HistoryResponse = {
      instrument: apple,
      range: "1D",
      state: "partial",
      series: {
        ...series,
        timeliness: "on_time",
        end_at: series.as_of!,
        expected_through_at: series.as_of,
      },
    };
    render(
      <MarketHistoryChart
        symbol="AAPL"
        range="1D"
        onRange={vi.fn()}
        response={response}
        loading={false}
      />,
    );
    expect(screen.getByText("Regular session", { exact: true })).toBeVisible();
    expect(screen.getByText(/IEX · Regular sessions/).querySelector("time")).toHaveAttribute(
      "datetime",
      series.as_of,
    );
  });

  it("polls a pending response at most three times and offers a new user retry", async () => {
    vi.useFakeTimers();
    const fetch = vi.fn(() =>
      Promise.resolve(json({ instrument: apple, range: "1W", state: "pending", series: null })),
    );
    vi.stubGlobal("fetch", fetch);
    connect();
    await act(async () => vi.advanceTimersByTimeAsync(10_000));
    expect(fetch).toHaveBeenCalledTimes(4);
    expect(screen.getByText("History is still loading")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try history again" }));
    await act(async () => vi.advanceTimersByTimeAsync(0));
    expect(screen.getByRole("button", { name: "1W" })).toHaveFocus();
    expect(fetch).toHaveBeenCalledTimes(5);
  });
});
