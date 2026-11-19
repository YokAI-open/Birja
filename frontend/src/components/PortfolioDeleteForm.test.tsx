import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioDeleteForm } from "./PortfolioDeleteForm";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";
import { DELETION_POLICY } from "@/api/portfolioDeletion";

vi.mock("@/hooks/usePortfolioDeletion");
const metadata = { id: "1", name: "<b>策略</b>" + "🚀".repeat(40), description: "" };
const intent = { portfolioId: "1", confirmationName: metadata.name, intentKey: "test", policyVersion: DELETION_POLICY };
const reviewDeletion = vi.fn(() => true), cancelReview = vi.fn(), confirmDeletion = vi.fn(), checkDeletionResult = vi.fn(), retryRecoveryStorage = vi.fn();
function state(extra = {}, deletion = {}) {
  vi.mocked(usePortfolioDeletion).mockReturnValue({ ready: true, canConfirm: true, canCheck: true, reviewDeletion, cancelReview, confirmDeletion, checkDeletionResult, retryRecoveryStorage, deletion: { phase: "idle", review: null, attempt: null, error: null, retryAt: null, reviewRequired: false, ...deletion }, ...extra } as ReturnType<typeof usePortfolioDeletion>);
}
function show(extra = {}, deletion = {}, props = {}) {
  state(extra, deletion);
  return render(<MemoryRouter><PortfolioDeleteForm portfolioId="1" metadata={metadata} metadataBusy={false} available refreshMetadata={vi.fn()} {...props} /></MemoryRouter>);
}
afterEach(() => { cleanup(); vi.clearAllMocks(); });
it("opens only a named review; Cancel is first and focused, Escape and Enter never send", () => {
  const view = show();
  const trigger = screen.getByRole("button", { name: "Delete portfolio…" });
  fireEvent.click(trigger);
  expect(reviewDeletion).toHaveBeenCalledWith(metadata);
  expect(confirmDeletion).not.toHaveBeenCalled();
  state({}, { phase: "review", review: intent });
  view.rerender(<MemoryRouter><PortfolioDeleteForm portfolioId="1" metadata={metadata} metadataBusy={false} available refreshMetadata={vi.fn()} /></MemoryRouter>);
  expect(screen.getByRole("heading", { name: `Delete “${metadata.name}”?` })).toBeVisible();
  expect(document.querySelector("b")).toBeNull();
  expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
  fireEvent.keyDown(screen.getByRole("region", { name: `Delete “${metadata.name}”?` }), { key: "Enter" });
  expect(confirmDeletion).not.toHaveBeenCalled();
  fireEvent.keyDown(screen.getByRole("button", { name: "Cancel" }), { key: "Escape" });
  expect(cancelReview).toHaveBeenCalledOnce();
  expect(confirmDeletion).not.toHaveBeenCalled();
});
it("explains freezing unpaid effects and permits only deliberate final activation", () => {
  show({}, { phase: "review", review: intent });
  expect(screen.getByText(/committed cash, investments and History/)).toBeVisible();
  expect(screen.getByText(/including unpaid dividends already earned/)).toBeVisible();
  expect(screen.getByText(/Nothing will be sold or moved/)).toHaveTextContent(/cannot undo/);
  fireEvent.click(screen.getByRole("button", { name: "Delete portfolio" }));
  expect(confirmDeletion).toHaveBeenCalledOnce();
});
it("keeps the reviewed name on rename and requires latest same-ID review", () => {
  const refreshMetadata = vi.fn();
  show({ canConfirm: false }, { phase: "review", review: intent, reviewRequired: true }, { metadata: { ...metadata, name: "Renamed" }, refreshMetadata });
  expect(screen.getByRole("heading", { name: `Delete “${metadata.name}”?` })).toBeVisible();
  expect(screen.getByRole("button", { name: "Delete portfolio" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Review latest portfolio" }));
  expect(refreshMetadata).toHaveBeenCalledOnce();
  expect(confirmDeletion).not.toHaveBeenCalled();
});
it.each(["persisting", "submitting", "checking", "unknown"])("shows immutable %s recovery without a misleading Cancel", (phase) => {
  show({}, { phase, attempt: intent }, { available: false });
  expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
  expect(screen.getByText(/Leaving does not cancel/)).toBeVisible();
  expect(screen.getByText(new RegExp(phase === "unknown" ? "We couldn't confirm" : "Checking the deletion"))).toHaveTextContent(metadata.name);
  if (phase === "unknown") { fireEvent.click(screen.getByRole("button", { name: "Check deletion result" })); expect(checkDeletionResult).toHaveBeenCalledOnce(); }
  else expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
});
it("waits for Retry-After and never silently retries", () => {
  show({ canCheck: false }, { phase: "unknown", attempt: intent, retryAt: Date.now() + 5000 });
  expect(screen.getByRole("button", { name: "Check deletion result" })).toBeDisabled();
  expect(screen.getByText(/Try again after/)).toBeVisible();
  expect(checkDeletionResult).not.toHaveBeenCalled();
});
it("blocks metadata drafts, another original and failed recovery with explicit safe retry", () => {
  show({}, {}, { metadataBusy: true });
  expect(screen.getByRole("button", { name: "Delete portfolio…" })).toBeDisabled();
  expect(screen.getByText(/Finish or discard/)).toBeVisible();
  cleanup();
  show({}, { phase: "unknown", attempt: { ...intent, portfolioId: "2" } });
  expect(screen.getByText(/before deleting another/)).toBeVisible();
  expect(screen.queryByText(new RegExp(metadata.name))).toBeNull();
  cleanup();
  show({ ready: false }, { error: new Error("Storage") });
  fireEvent.click(screen.getByRole("button", { name: "Retry deletion recovery" }));
  expect(retryRecoveryStorage).toHaveBeenCalledOnce();
  expect(confirmDeletion).not.toHaveBeenCalled();
});
it("does not display stale metadata on a private unavailable normal route", () => {
  show({}, {}, { available: false });
  expect(screen.queryByRole("heading")).toBeNull();
  expect(screen.queryByText(metadata.name)).toBeNull();
});
