import { expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithClient } from "@/test/render";
import type { EventDividend, EventDividendCorrection } from "@/api/eventHistory";
import { HistoryEventCash, HistoryEventDetails, HistoryEventTitle } from "./HistoryEventDetails";

const original: EventDividend = {
  kind: "dividend",
  id: "dividend:1",
  payment_reference: "dividend:1",
  recorded_at: "2026-11-12T15:00:00.000001Z",
  credited_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "1.00",
  credited_amount: "1.00",
  eligible_quantity: "100000000",
  rate: "0.00000001",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: null,
  record_date: "2026-11-11",
  payable_date: "2026-11-12",
};
const held: EventDividendCorrection = {
  kind: "dividend_correction",
  id: "dividend_correction:2",
  decision_reference: "dividend_correction:2",
  recorded_at: "2026-11-12T16:00:00Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "0.00",
  payment_reference: original.id,
  outcome: "held_uncertain",
  reason: "terms_unverified",
  desired_total: null,
  cumulative_applied_before: "1.00",
  proposed_delta: null,
  applied_delta: "0.00",
  terms: null,
  original,
};
it("shows an uncertain correction without inventing a cash credit or revised terms", () => {
  renderWithClient(<HistoryEventDetails item={held} />);
  expect(
    screen.getByText("The corrected dividend terms need verification. No cash changed."),
  ).toBeVisible();
  expect(screen.getByText("Applied change: $0.00")).toBeVisible();
  expect(screen.queryByText(/USD .* per share/)).not.toBeInTheDocument();
});

it("opens the immutable offpage original, focuses its heading and returns to its initiating control", async () => {
  const user = userEvent.setup();
  const { rerender } = render(<HistoryEventDetails item={held} />);
  const view = screen.getByRole("button", { name: "View original dividend" });
  await user.click(view);
  const heading = screen.getByRole("heading", { name: "Original dividend · AAPL · Apple" });
  expect(heading).toHaveFocus();
  expect(screen.getByText("USD 0.00000001 per share")).toBeVisible();
  expect(screen.getByText("Not provided")).toBeVisible();
  expect(screen.getByText("2026-11-12")).toBeVisible();
  const back = screen.getByRole("button", { name: "Back to correction" });
  back.focus();
  rerender(<HistoryEventDetails item={{ ...held }} />);
  expect(back).toHaveFocus();
  await user.click(back);
  expect(view).toHaveFocus();
  expect(screen.queryByRole("heading")).not.toBeInTheDocument();
});

it("focuses an already loaded original using its stable identity without opening a duplicate", async () => {
  const { user } = renderWithClient(
    <>
      <div id={`history-${original.id}`} tabIndex={-1}>
        Loaded original
      </div>
      <HistoryEventDetails item={held} />
    </>,
  );
  await user.click(screen.getByRole("button", { name: "View original dividend" }));
  expect(screen.getByText("Loaded original")).toHaveFocus();
  expect(screen.queryByRole("button", { name: "Back to correction" })).not.toBeInTheDocument();
});

it("separates a held debit proposal from applied zero and never offers a financial retry", () => {
  const item: EventDividendCorrection = {
    ...held,
    outcome: "held_unaffordable",
    reason: "insufficient_cash",
    desired_total: "0.50",
    proposed_delta: "-0.50",
    terms: original,
  };
  renderWithClient(
    <>
      <HistoryEventTitle item={item} />
      <HistoryEventCash item={item} />
      <HistoryEventDetails item={item} />
    </>,
  );
  expect(screen.getByText("Dividend correction held")).toBeVisible();
  expect(screen.getByText("Held when recorded")).toBeVisible();
  expect(
    screen.getByText("Not enough available cash for this correction. No cash changed."),
  ).toBeVisible();
  expect(screen.getByText("−$0.50")).toBeVisible();
  expect(screen.getByText("Applied change: $0.00")).toBeVisible();
  expect(screen.getByText("No cash changed")).toBeVisible();
  expect(screen.queryByRole("button", { name: /pay|retry/i })).not.toBeInTheDocument();
});

it.each(["-0.50", "0.50", "0.00"])(
  "renders exact applied correction %s separately from the total owed",
  (delta) => {
    const item: EventDividendCorrection = {
      ...held,
      outcome: delta === "0.00" ? "verified_no_change" : "applied",
      reason: delta === "0.00" ? "target_unchanged" : "target_applied",
      cash_delta: delta,
      applied_delta: delta,
      proposed_delta: delta,
      desired_total: "1.00",
      terms: original,
    };
    renderWithClient(
      <>
        <HistoryEventTitle item={item} />
        <HistoryEventCash item={item} />
        <HistoryEventDetails item={item} />
      </>,
    );
    expect(
      screen.getByText(
        `Applied change: ${delta.startsWith("-") ? "−$0.50" : delta === "0.00" ? "$0.00" : "+$0.50"}`,
      ),
    ).toBeVisible();
    expect(screen.getByText("Verified total now owed")).toBeVisible();
    if (delta === "0.00")
      expect(screen.getByText("Dividend correction — no cash adjustment")).toBeVisible();
  },
);

it("preserves exact tiny rates, calendar dates, UTC instants and escaped names", () => {
  const item = { ...original, name: '<img src=x onerror="alert(1)">' };
  const { container } = renderWithClient(
    <>
      <span>{item.name}</span>
      <HistoryEventDetails item={item} />
    </>,
  );
  expect(screen.getByText(item.name)).toBeVisible();
  expect(container.querySelector("img")).toBeNull();
  expect(screen.getByText("USD 0.00000001 per share")).toBeVisible();
  expect(container.querySelector(`time[datetime="${item.cutoff}"]`)).toHaveAttribute(
    "title",
    item.cutoff,
  );
});

it("renders saved split shares and conserved basis as a noncash event", () => {
  const item = {
    kind: "split",
    id: "split:1",
    recorded_at: original.recorded_at,
    asset_type: "stock",
    symbol: "AAPL",
    name: "Apple",
    cash_delta: "0.00",
    ratio_new: "3",
    ratio_old: "2",
    quantity_before: "2",
    quantity_after: "3",
    cost_basis_before: "999999999999.99",
    cost_basis_after: "999999999999.99",
    effective_at: original.cutoff,
  } as const;
  renderWithClient(
    <>
      <HistoryEventTitle item={item} />
      <HistoryEventDetails item={item} />
    </>,
  );
  expect(screen.getByText("Forward split")).toBeVisible();
  expect(screen.getByText("3:2")).toBeVisible();
  expect(screen.getByText("2 → 3")).toBeVisible();
  expect(screen.getByText("$999,999,999,999.99 → $999,999,999,999.99 (unchanged)")).toBeVisible();
});

it.each(["stock", "crypto"] as const)(
  "renders saved %s fill economics with appropriate source attribution",
  (asset_type) => {
    const item = {
      kind: "trade",
      id: "trade:1",
      recorded_at: original.recorded_at,
      asset_type,
      symbol: "AAPL",
      name: "Apple",
      cash_delta: "-100.00",
      side: "sell",
      quantity: "2",
      exec_price: "50.00",
      fee: "0.00",
      filled_at: original.recorded_at,
      source: asset_type === "stock" ? "alpaca" : null,
      feed: asset_type === "stock" ? "iex" : null,
      quote_at: asset_type === "stock" ? original.cutoff : null,
    } as const;
    renderWithClient(
      <>
        <HistoryEventTitle item={item} />
        <HistoryEventCash item={item} />
        <HistoryEventDetails item={item} />
      </>,
    );
    expect(screen.getByText("Sell")).toBeVisible();
    expect(screen.getByText("−$100.00")).toBeVisible();
    expect(screen.getByText(asset_type === "stock" ? "Commission" : "Fee")).toBeVisible();
    expect(screen.queryByText(/IEX prices/)).toBe(
      asset_type === "stock" ? screen.getByText(/IEX prices/) : null,
    );
  },
);
