import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { PortfolioCreateForm } from "./PortfolioCreateForm";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PortfolioManagementError } from "@/api/portfolioManagement";
vi.mock("@/hooks/usePortfolioManagement");
const submitCreation = vi.fn();
const retryCreation = vi.fn();
it("does not consume an earlier resolved receipt when opening a fresh creation", () => {
  const onCreated = vi.fn();
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: {
      phase: "resolved",
      attempt: null,
      error: null,
      receipt: { metadata: { id: "8", name: "Earlier", description: "" }, isCurrent: () => true },
    },
  } as unknown as ReturnType<typeof usePortfolioManagement>);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <PortfolioCreateForm count={1} onClose={vi.fn()} onCreated={onCreated} />
    </QueryClientProvider>,
  );
  expect(onCreated).not.toHaveBeenCalled();
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("");
});
it("focuses a new linked server error summary", () => {
  const view = show();
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: "Duplicate" } });
  fireEvent.click(screen.getByRole("button", { name: "Create portfolio" }));
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: {
      phase: "editing",
      attempt: null,
      error: new PortfolioManagementError("refused", "name_taken", 409),
    },
  } as ReturnType<typeof usePortfolioManagement>);
  view.rerender(<QueryClientProvider client={new QueryClient()}><PortfolioCreateForm count={1} onClose={vi.fn()} onCreated={vi.fn()} /></QueryClientProvider>);
  expect(screen.getByRole("alert")).toHaveFocus();
  fireEvent.click(screen.getByRole("link", { name: "Review portfolio name" }));
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
});
it("discards an old definitive duplicate error when reopening a fresh draft", () => {
  const refusal = new PortfolioManagementError("refused", "name_taken", 409);
  const first = show();
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: "Duplicate" } });
  fireEvent.click(screen.getByRole("button", { name: "Create portfolio" }));
  first.unmount();
  const reopened = show({ creation: { phase: "editing", attempt: null, error: refusal } });
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("");
  expect(screen.getByLabelText("Portfolio name")).not.toHaveAccessibleDescription(/already have an active/);
  reopened.unmount();
});
it.each([true, false])("publishes only a current captured receipt (%s)", (current) => {
  const onCreated = vi.fn();
  const client = new QueryClient();
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: { phase: "editing", attempt: null, error: null },
  } as ReturnType<typeof usePortfolioManagement>);
  const view = render(
    <QueryClientProvider client={client}>
      <PortfolioCreateForm count={10} onClose={vi.fn()} onCreated={onCreated} />
    </QueryClientProvider>,
  );
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: {
      phase: "resolved",
      attempt: null,
      error: null,
      receipt: {
        metadata: { id: "8", name: "Renamed", description: "Latest" },
        isCurrent: () => current,
      },
    },
  } as unknown as ReturnType<typeof usePortfolioManagement>);
  view.rerender(
    <QueryClientProvider client={client}>
      <PortfolioCreateForm count={10} onClose={vi.fn()} onCreated={onCreated} />
    </QueryClientProvider>,
  );
  if (current)
    expect(onCreated).toHaveBeenCalledWith(
      { id: "8", name: "Renamed", description: "Latest" },
      false,
    );
  else expect(onCreated).not.toHaveBeenCalled();
});
it("clears a local creation draft on owner/session loss", () => {
  const client = new QueryClient();
  client.setQueryData(["me"], { email: "first@example.test" });
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: { phase: "editing", attempt: null, error: null },
  } as ReturnType<typeof usePortfolioManagement>);
  render(
    <QueryClientProvider client={client}>
      <PortfolioCreateForm count={0} onClose={vi.fn()} onCreated={vi.fn()} />
    </QueryClientProvider>,
  );
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: "Private draft" } });
  act(() => client.setQueryData(["me"], null));
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("");
});
function show(overrides = {}, count: number | null = 0) {
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: { phase: "editing", attempt: null, error: null },
    submitCreation,
    retryCreation,
    ...overrides,
  } as unknown as ReturnType<typeof usePortfolioManagement>);
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <PortfolioCreateForm
        count={count === null ? undefined : count}
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />
    </QueryClientProvider>,
  );
}
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("focuses name, counts Unicode scalars and submits raw escaped text", () => {
  show();
  expect(screen.getByLabelText("Portfolio name")).toHaveFocus();
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: " <b>Moon</b> " } });
  fireEvent.change(screen.getByLabelText("Description (optional)"), {
    target: { value: "🚀\r\nline" },
  });
  expect(screen.getByText("6 / 1,000 characters")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Create portfolio" }));
  expect(submitCreation).toHaveBeenCalledWith({ name: " <b>Moon</b> ", description: "🚀\nline" });
  expect(document.querySelector("b")).toBeNull();
});
it("rejects controls and oversized astral input without truncating, linking field errors", () => {
  show();
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: "bad\u0001" } });
  fireEvent.change(screen.getByLabelText("Description (optional)"), {
    target: { value: "🚀".repeat(1001) },
  });
  expect(screen.getByLabelText("Description (optional)")).toHaveValue("🚀".repeat(1001));
  expect(screen.getByLabelText("Description (optional)")).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByRole("button", { name: "Create portfolio" })).toBeDisabled();
  expect(submitCreation).not.toHaveBeenCalled();
});
it("keeps original unknown payload readonly and retryable at cap", () => {
  show(
    {
      creation: {
        phase: "unknown",
        attempt: { key: "key", name: "Original", description: "Keep" },
        error: null,
      },
    },
    10,
  );
  expect(screen.getByLabelText("Portfolio name")).toHaveValue("Original");
  expect(screen.getByLabelText("Portfolio name")).toHaveAttribute("readonly");
  fireEvent.click(screen.getByRole("button", { name: "Retry creation" }));
  expect(retryCreation).toHaveBeenCalledOnce();
  expect(screen.getByRole("button", { name: "Close creation" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Discard draft" })).toBeNull();
});
it.each([null, 10])("blocks new creation while cap is unknown or full (%s)", (count) => {
  show({}, count);
  fireEvent.change(screen.getByLabelText("Portfolio name"), { target: { value: "Valid name" } });
  expect(screen.getByRole("button", { name: "Create portfolio" })).toBeDisabled();
});
