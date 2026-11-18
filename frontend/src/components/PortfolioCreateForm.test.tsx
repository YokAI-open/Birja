import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioCreateForm } from "./PortfolioCreateForm";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
vi.mock("@/hooks/usePortfolioManagement");
const submitCreation = vi.fn();
const retryCreation = vi.fn();
function show(overrides = {}, count: number | undefined = 0) {
  vi.mocked(usePortfolioManagement).mockReturnValue({ ready: true, creation: {phase: "editing", attempt: null, error: null}, submitCreation, retryCreation, ...overrides } as unknown as ReturnType<typeof usePortfolioManagement>);
  return render(<PortfolioCreateForm count={count} onClose={vi.fn()} onCreated={vi.fn()} />);
}
afterEach(() => {cleanup(); vi.clearAllMocks();});
it("focuses name, counts Unicode scalars and submits raw escaped text", () => {
  show();
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
  fireEvent.change(screen.getByLabelText("Portfolio name"), {target:{value:" <b>Moon</b> "}});
  fireEvent.change(screen.getByLabelText("Description (optional)"), {target:{value:"🚀\r\nline"}});
  expect(screen.getByText("6 / 1,000 characters")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", {name:"Create portfolio"}));
  expect(submitCreation).toHaveBeenCalledWith({name:" <b>Moon</b> ", description:"🚀\nline"});
  expect(document.querySelector("b")).toBeNull();
});
it("rejects controls and oversized astral input without truncating, linking field errors", () => {
  show();
  fireEvent.change(screen.getByLabelText("Portfolio name"), {target:{value:"bad\u0001"}});
  fireEvent.change(screen.getByLabelText("Description (optional)"), {target:{value:"🚀".repeat(1001)}});
  expect(screen.getByLabelText("Description (optional)")).toHaveValue("🚀".repeat(1001));
  expect(screen.getByLabelText("Description (optional)")).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByRole("button", {name:"Create portfolio"})).toBeDisabled();
  expect(submitCreation).not.toHaveBeenCalled();
});
it("keeps original unknown payload readonly and retryable at cap", () => {
  show({creation:{phase:"unknown", attempt:{key:"key", name:"Original", description:"Keep"}, error:null}},10);
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("Original");
  expect(screen.getByLabelText("Portfolio name")).toHaveAttribute("readonly");
  fireEvent.click(screen.getByRole("button",{name:"Retry creation"}));
  expect(retryCreation).toHaveBeenCalledOnce();
  expect(screen.getByRole("button",{name:"Close creation"})).toBeInTheDocument();
  expect(screen.queryByRole("button",{name:"Discard draft"})).toBeNull();
});
it.each([undefined,10])("blocks new creation while cap is unknown or full (%s)", count => {
  show({}, count);
  expect(screen.getByRole("button",{name:"Create portfolio"})).toBeDisabled();
});
