import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioMetadataForm } from "./PortfolioMetadataForm";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { PortfolioManagementError } from "@/api/portfolioManagement";
vi.mock("@/hooks/usePortfolioManagement");
vi.mock("@/components/PortfolioDeleteForm", () => ({ PortfolioDeleteForm: () => null }));
const editMetadata = vi.fn(),
  saveMetadata = vi.fn(),
  discardMetadata = vi.fn(),
  reviewMetadata = vi.fn();
const metadata = { id: "1", name: "Original", description: "<b>Plain</b>\nSecond line" };
function state(extra = {}) {
  const result = {
    metadata,
    metadataError: null,
    metadataPending: false,
    draft: null,
    reviewRequired: false,
    editMetadata,
    saveMetadata,
    discardMetadata,
    reviewMetadata,
    refreshMetadata: vi.fn(),
    ...extra,
  };
  vi.mocked(usePortfolioManagement).mockReturnValue(
    result as unknown as ReturnType<typeof usePortfolioManagement>,
  );
  return result;
}
function show(extra = {}) {
  state(extra);
  return render(
    <MemoryRouter>
      <PortfolioMetadataForm portfolioId="1" />
    </MemoryRouter>,
  );
}
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("views escaped metadata and enters edit with focus; discard restores trigger", () => {
  show();
  expect(screen.getByText("<b>Plain</b> Second line")).toBeInTheDocument();
  expect(document.querySelector("b")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Edit portfolio" }));
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
  fireEvent.change(screen.getByLabelText("Description (optional)"), { target: { value: "" } });
  expect(editMetadata).toHaveBeenCalledWith({ description: "" });
  fireEvent.click(screen.getByRole("button", { name: "Discard changes" }));
  expect(discardMetadata).toHaveBeenCalledOnce();
  expect(screen.getByRole("button", { name: "Edit portfolio" })).toHaveFocus();
});
it("keeps stale draft and requires explicit authoritative review", () => {
  show({ draft: { name: "Draft", description: "🚀".repeat(1000) }, reviewRequired: true });
  expect(screen.getByText("1000 / 1,000 characters")).toBeInTheDocument();
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("Draft");
  expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  expect(screen.getByText(/Latest portfolio name/)).toHaveTextContent("Original");
  fireEvent.click(screen.getByRole("button", { name: "I have reviewed the latest details" }));
  expect(reviewMetadata).toHaveBeenCalledOnce();
});
it("suppresses metadata and editing when the explicit target is unavailable", () => {
  show({ metadata: undefined, metadataError: new Error("Unavailable") });
  expect(screen.queryByText("Original")).toBeNull();
  expect(screen.queryByRole("button", { name: "Edit portfolio" })).toBeNull();
  expect(screen.getByRole("alert")).toHaveTextContent(/metadata/i);
});
it("saves only explicit valid draft and rejects overlong/control input", () => {
  show({ draft: { name: "Updated", description: "" } });
  fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
  expect(saveMetadata).toHaveBeenCalledOnce();
  cleanup();
  show({ draft: { name: "bad\u0001", description: "🚀".repeat(1001) } });
  expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  expect(screen.getByLabelText("Description (optional)")).toHaveAttribute("aria-invalid", "true");
});
it("shows a genuine empty description and back link", () => {
  show({ metadata: { ...metadata, description: "" } });
  expect(screen.getByText("No description.")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Back to Portfolios" })).toHaveAttribute(
    "href",
    "/portfolios",
  );
});
it("links a refused duplicate-name summary to an invalid field while retaining description", () => {
  show({
    draft: { name: "Duplicate", description: "Keep this" },
    metadataError: new PortfolioManagementError("refused", "name_taken", 409),
  });
  expect(screen.getByRole("alert")).toHaveFocus();
  expect(screen.getByLabelText("Portfolio name")).toHaveAttribute("aria-invalid", "true");
  fireEvent.click(screen.getByRole("link", { name: "Review portfolio name" }));
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
  expect(screen.getByLabelText("Description (optional)")).toHaveValue("Keep this");
});
it("freezes submitted drafts and blocks premature stale review while authoritative refresh is pending", () => {
  show({
    draft: { name: "Draft", description: "Keep" },
    metadataPending: true,
    reviewRequired: true,
  });
  expect(screen.getByLabelText("Portfolio name")).toHaveAttribute("readonly");
  expect(screen.getByRole("button", { name: "I have reviewed the latest details" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Saving changes…" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Discard changes" })).toBeDisabled();
});
it("disables entering metadata editing while deletion owns the review lease", () => {
  show({ metadataBlocked: true });
  expect(screen.getByRole("button", { name: "Edit portfolio" })).toBeDisabled();
});
it.each(["bad\u0001", "bad\ud800"])(
  "rejects unsupported description scalars without changing the draft",
  (description) => {
    show({ draft: { name: "Valid", description } });
    expect(screen.getByLabelText("Description (optional)")).toHaveValue(description);
    expect(screen.getByLabelText("Description (optional)")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  },
);
