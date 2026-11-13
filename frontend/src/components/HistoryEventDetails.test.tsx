import { expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithClient } from "@/test/render";
import type { EventDividend, EventDividendCorrection } from "@/api/eventHistory";
import { HistoryEventDetails } from "./HistoryEventDetails";

const original: EventDividend = {
  kind: "dividend", id: "dividend:1", payment_reference: "dividend:1",
  recorded_at: "2026-11-12T15:00:00.000001Z", credited_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock", symbol: "AAPL", name: "Apple", cash_delta: "1.00", credited_amount: "1.00",
  eligible_quantity: "100000000", rate: "0.00000001", cutoff: "2026-11-10T14:30:00Z",
  ex_date: null, record_date: "2026-11-11", payable_date: "2026-11-12",
};
const held: EventDividendCorrection = {
  kind: "dividend_correction", id: "dividend_correction:2", decision_reference: "dividend_correction:2",
  recorded_at: "2026-11-12T16:00:00Z", asset_type: "stock", symbol: "AAPL", name: "Apple",
  cash_delta: "0.00", payment_reference: original.id, outcome: "held_uncertain", reason: "terms_unverified",
  desired_total: null, cumulative_applied_before: "1.00", proposed_delta: null, applied_delta: "0.00",
  terms: null, original,
};
it("shows an uncertain correction without inventing a cash credit or revised terms", () => {
  renderWithClient(<HistoryEventDetails item={held} />);
  expect(screen.getByText("The corrected dividend terms need verification. No cash changed.")).toBeVisible();
  expect(screen.getByText("Applied change: $0.00")).toBeVisible();
  expect(screen.queryByText(/USD .* per share/)).not.toBeInTheDocument();
});
