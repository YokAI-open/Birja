import { screen, within } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import type { StocksResponse } from "@/api/stocks";
import { StockSection } from "./StockSection";

const state = vi.hoisted(() => ({
  data: undefined as StocksResponse | undefined,
  isPending: false,
  isError: false,
  isFetching: false,
  refetch: vi.fn(),
}));
vi.mock("@/hooks/useStocks", () => ({ useStocks: () => state }));
function payload(): StocksResponse {
  return {
    server_now: "2026-11-10T15:00:00Z",
    admission: { state: "approved", generation: 1, valid_until: "2026-11-11T15:00:00Z" },
    attribution: {
      label: "IEX prices",
      explanation: "One venue",
      required_text: "Required provider credit",
    },
    items: Array.from({ length: 20 }, (_, i) => ({
      id: i + 16,
      symbol: `A${String.fromCharCode(65 + i)}`,
      company_name: `Company ${i}`,
      listing_exchange: "NASDAQ",
      currency: "USD",
      quote: {
        bid: "100.00000000",
        ask: "102.00000000",
        mid: "101.00000000",
        event_at: "2026-11-10T14:59:50Z",
        collected_at: "2026-11-10T14:59:51Z",
        source: "alpaca",
        feed: "iex",
        age_seconds: 10,
      },
      session: {
        state: "open",
        opens_at: "2026-11-10T14:30:00Z",
        closes_at: "2026-11-10T21:00:00Z",
        next_open_at: null,
        valid_until: "2026-11-11T00:00:00Z",
        timezone: "America/New_York",
      },
      status: { state: "unknown", observed_at: null, valid_until: null },
      execution_enabled: false,
      execution_reason: "phase_disabled",
      quote_reason: "recent",
      session_reason: "open",
      status_reason: "unknown",
    })),
  };
}
beforeEach(() => {
  state.data = payload();
  state.isPending = false;
  state.isError = false;
  state.isFetching = false;
  state.refetch.mockReset();
});

it("preserves twenty identities, separate listing/source, exact money and semantic source time without stock controls", () => {
  renderWithClient(<StockSection />);
  expect(screen.getByRole("heading", { name: "US stocks · 20" })).toBeVisible();
  expect(screen.getByRole("note", { name: "Stock price source" })).toHaveTextContent(
    "Required provider credit",
  );
  const table = screen.getByRole("table", { name: "US stocks" });
  expect(within(table).getAllByRole("row")).toHaveLength(21);
  const first = within(table).getAllByRole("row")[1]!;
  expect(first).toHaveTextContent("AA");
  expect(first).toHaveTextContent("Company 0");
  expect(first).toHaveTextContent("NASDAQ");
  expect(first).toHaveTextContent("$100.00");
  expect(first).toHaveTextContent("$102.00");
  expect(first.querySelector("time")).toHaveAttribute("dateTime", "2026-11-10T14:59:50Z");
  expect(first).toHaveTextContent("Recent · 10s ago");
  expect(first).toHaveTextContent("Market open");
  expect(first).toHaveTextContent("Stock status unverified");
  expect(screen.queryAllByRole("link")).toHaveLength(0);
  expect(screen.queryAllByRole("button")).toHaveLength(0);
  expect(screen.getByText(/Stock trading coming later/)).toBeVisible();
  expect(screen.getAllByRole("status")).toHaveLength(1);
});
it("keeps the catalogue but removes all quote values and times on denial", () => {
  state.data!.admission = { state: "unavailable", generation: null, valid_until: null };
  state.data!.items.forEach((item) => {
    item.quote = null;
    item.quote_reason = "permission_unavailable";
  });
  renderWithClient(<StockSection />);
  expect(screen.getByText(/Stock prices are unavailable while data permissions/)).toBeVisible();
  expect(screen.queryByText("$100.00")).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
  expect(within(screen.getByRole("table", { name: "US stocks" })).getAllByRole("row")).toHaveLength(
    21,
  );
});
it("shows missing, stale, previous-session, closed and unknown facts separately", () => {
  const items = state.data!.items;
  items[0].quote = null;
  items[0].quote_reason = "missing";
  items[1].quote_reason = "stale";
  items[1].quote!.age_seconds = 120;
  items[2].quote_reason = "session_unavailable";
  items[3].session.state = "closed";
  items[3].quote_reason = "session_unavailable";
  items[3].session.next_open_at = "2026-11-11T14:30:00Z";
  items[4].session.state = "unknown";
  items[4].quote = null;
  renderWithClient(<StockSection />);
  const rows = within(screen.getByRole("table", { name: "US stocks" }))
    .getAllByRole("row")
    .slice(1);
  expect(rows[0]).toHaveTextContent("Waiting for an IEX quote.");
  expect(rows[0]).not.toHaveTextContent("$0");
  expect(rows[1]).toHaveTextContent("Out of date · 2m ago");
  expect(rows[2]).toHaveTextContent("Previous session");
  expect(rows[2]).not.toHaveTextContent("Recent");
  expect(rows[3]).toHaveTextContent("Last quote");
  expect(rows[3]).toHaveTextContent("Next regular session");
  expect(rows[3]).toHaveTextContent("America/New_York");
  expect(rows[4]).toHaveTextContent("Session unavailable");
});
it("uses one non-ticking contextual announcement and retains original dated values on background failure", () => {
  state.isError = true;
  const { rerender } = renderWithClient(<StockSection />);
  const status = screen.getByRole("status");
  const announcement = status.textContent;
  expect(status).toHaveTextContent("Couldn’t refresh stock prices");
  state.data!.items[0].quote!.age_seconds = 11;
  rerender(<StockSection />);
  expect(status.textContent).toBe(announcement);
  expect(
    within(screen.getByRole("table", { name: "US stocks" })).getAllByRole("row")[1],
  ).toHaveTextContent("Recent · 11s ago");
});
it("renders independent loading and actionable retry without raw error details", async () => {
  state.data = undefined;
  state.isPending = true;
  const { rerender, user } = renderWithClient(<StockSection />);
  expect(screen.getByRole("status", { name: "Loading stocks" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
  state.isPending = false;
  state.isError = true;
  rerender(<StockSection />);
  expect(screen.getByRole("status")).toHaveTextContent("Can’t load stock prices right now");
  await user.click(screen.getByRole("button", { name: "Retry stock prices" }));
  expect(state.refetch).toHaveBeenCalledOnce();
});

it("reserves the full twenty-record loading catalogue", () => {
  state.data = undefined;
  state.isPending = true;
  const { container } = renderWithClient(<StockSection />);
  const skeletons = container.querySelectorAll('[aria-hidden="true"] > div');
  expect(skeletons).toHaveLength(20);
});

it("restores keyboard position to the stock heading after successful retry", async () => {
  state.data = undefined;
  state.isPending = false;
  state.isError = true;
  state.refetch.mockResolvedValue({ isError: false });
  const { user } = renderWithClient(<StockSection />);
  const retry = screen.getByRole("button", { name: "Retry stock prices" });
  retry.focus();
  await user.keyboard("{Enter}");
  expect(screen.getByRole("heading", { name: "US stocks · 20" })).toHaveFocus();
});
