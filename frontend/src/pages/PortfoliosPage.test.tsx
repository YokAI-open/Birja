import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import PortfoliosPage from "./PortfoliosPage";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { cashPortfolio } from "@/test/portfolioFixtures";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";
import { usePortfolioValueHistory } from "@/hooks/usePortfolioValueHistory";
vi.mock("@/hooks/usePortfolioOverview");
vi.mock("@/hooks/usePortfolioManagement");
vi.mock("@/hooks/usePortfolioDeletion");
vi.mock("@/hooks/usePortfolioValueHistory");
const refetch = vi.fn();
const retry = vi.fn();
function show(
  data: unknown,
  extra = {},
  trend: Partial<ReturnType<typeof usePortfolioValueHistory>> = {},
) {
  vi.mocked(usePortfolioValueHistory).mockReturnValue({
    data: undefined,
    failed: false,
    loading: false,
    retrying: false,
    paused: false,
    retry,
    ...trend,
  });
  vi.mocked(usePortfolioDeletion).mockReturnValue({
    ready: true,
    deletion: { phase: "idle", attempt: null },
  } as ReturnType<typeof usePortfolioDeletion>);
  vi.mocked(usePortfolioOverview).mockReturnValue({
    data,
    isPending: false,
    isError: false,
    isFetching: false,
    refetch,
    ...extra,
  } as unknown as ReturnType<typeof usePortfolioOverview>);
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: { phase: "editing", attempt: null, error: null },
  } as ReturnType<typeof usePortfolioManagement>);
  const client = new QueryClient();
  return render(<PortfoliosPage />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={client}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    ),
  });
}
it("keeps card membership, current values and exact dated observations paired through gaps", () => {
  const current = [
    { ...cashPortfolio(), id: "2", name: "Dividends", description: "Income" },
    { ...cashPortfolio(), id: "10", name: "Growth", description: "Long horizon" },
  ];
  show(
    current,
    {},
    {
      data: {
        start_day: "2026-10-01",
        end_day: "2026-10-30",
        portfolios: [
          {
            portfolio_id: "2",
            points: [
              {
                utc_day: "2026-10-10",
                captured_at: "2026-10-10T22:00:00Z",
                total_value: "1234.56",
                valuation_complete: true,
              },
            ],
          },
          { portfolio_id: "10", points: [] },
        ],
      },
    },
  );
  expect(usePortfolioValueHistory).toHaveBeenCalledWith(current);
  const dividends = screen.getByRole("link", { name: "Dividends" });
  expect(dividends).toHaveAccessibleDescription(
    /One recorded value \(UTC\) on Oct 10, 2026, \$1,234.56/,
  );
  expect(dividends).toHaveTextContent("$10,000.00 cash");
  expect(screen.getByRole("link", { name: "Growth" })).toHaveAccessibleDescription(
    "Collecting daily values",
  );
  expect(
    within(screen.getAllByRole("listitem").at(-1)!).getByRole("button", { name: "New portfolio" }),
  ).toBeEnabled();
});
it("exposes one history retry outside fully usable cards and keeps current figures visible", () => {
  show([{ ...cashPortfolio(), id: "2", name: "Dividends", description: "" }], {}, { failed: true });
  const link = screen.getByRole("link", { name: "Dividends" });
  expect(link).toHaveAccessibleDescription("Value history unavailable");
  expect(link).toHaveTextContent("$10,000.00 cash");
  const button = screen.getByRole("button", { name: "Retry value history" });
  expect(link).not.toContainElement(button);
  fireEvent.click(button);
  expect(retry).toHaveBeenCalledOnce();
  expect(refetch).not.toHaveBeenCalled();
});

it("keeps the retry focus during an offline pause and restores it on success", () => {
  const view = show(
    [{ ...cashPortfolio(), id: "2", name: "Dividends", description: "" }],
    {},
    { failed: true },
  );
  const button = screen.getByRole("button", { name: "Retry value history" });
  button.focus();
  fireEvent.click(button);
  const started = { loading: true, paused: true, retrying: true, failed: false, retry };
  vi.mocked(usePortfolioValueHistory).mockReturnValue({ ...started, data: undefined });
  view.rerender(<PortfoliosPage />);
  expect(screen.getByText("Waiting for a connection to load value history.")).toBeVisible();
  expect(button).toHaveFocus();
  expect(button).toHaveAttribute("aria-disabled", "true");
  expect(screen.getByRole("link", { name: "Dividends" })).toHaveTextContent("$10,000.00 cash");

  vi.mocked(usePortfolioValueHistory).mockReturnValue({
    ...started,
    loading: false,
    paused: false,
    retrying: false,
    data: {
      start_day: "2026-10-01",
      end_day: "2026-10-30",
      portfolios: [{ portfolio_id: "2", points: [] }],
    },
  });
  view.rerender(<PortfoliosPage />);
  expect(screen.getByText("Value history updated.")).toHaveAttribute("aria-live", "polite");
  expect(screen.getByRole("heading", { name: "Portfolios", level: 1 })).toHaveFocus();
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it("does not present uncertain masked membership as empty or grant capacity", () => {
  show([], { membershipUncertain: true });
  expect(screen.queryByText("No portfolios yet")).toBeNull();
  expect(screen.getByRole("button", { name: "New portfolio" })).toBeDisabled();
});
it("shows genuine zero-book empty state and restores create trigger focus", () => {
  show([]);
  expect(screen.getByText("No portfolios yet")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "New portfolio" }));
  fireEvent.click(screen.getByRole("button", { name: "Discard draft" }));
  expect(screen.getByRole("button", { name: "New portfolio" })).toHaveFocus();
});
it("shows server values and incomplete returns without a valuation disclosure", () => {
  show([
    { ...cashPortfolio(), id: "2", name: "<script>safe</script>", description: "Line\nTwo" },
    {
      ...cashPortfolio(),
      id: "10",
      name: "Unpriced",
      description: "",
      valuation_complete: false,
      total_value: null,
      total_pl: null,
      total_pl_percent: null,
      known_value: "9000.12000000",
      unvalued_holding_count: 1,
    },
  ]);
  expect(screen.getByText("<script>safe</script>")).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
  expect(screen.getByText(/Known value: \$9,000.12/)).toBeInTheDocument();
  expect(screen.getByText("Return unavailable")).toBeInTheDocument();
  expect(screen.queryByText("Valuation details")).toBeNull();
  expect(screen.queryByText(/of 10 active portfolios/)).toBeNull();
  const links = screen.getAllByRole("link");
  expect(links).toHaveLength(2);
  expect(links[0]).toHaveAccessibleName("<script>safe</script>");
  expect(links[1]).toHaveAccessibleName("Unpriced");
  expect(links.map((link) => link.getAttribute("href"))).toEqual([
    "/portfolios/2",
    "/portfolios/10",
  ]);
  expect(screen.queryByText("No description.")).toBeNull();
});
it("distinguishes loading, initial error and failed refresh without hiding permitted rows", () => {
  const view = show(undefined, { isPending: true });
  expect(screen.getByRole("status")).toHaveTextContent("Loading portfolios");
  view.unmount();
  show(undefined, { isError: true });
  expect(screen.getByRole("alert")).toHaveTextContent("Can't load your portfolios");
});
it("keeps permitted data after refresh failure and offers retry", () => {
  show([{ ...cashPortfolio(), id: "1", description: "" }], { isError: true });
  expect(screen.getByRole("alert")).toHaveTextContent("Couldn't refresh");
  fireEvent.click(screen.getByRole("button", { name: "Retry refresh" }));
  expect(refetch).toHaveBeenCalled();
});
it.each([1, 2])("uses correct missing-holding copy for %i without inventing a return", (count) => {
  show([
    {
      ...cashPortfolio(),
      id: "1",
      description: "",
      valuation_complete: false,
      known_value: "9000.00",
      total_value: null,
      total_pl: null,
      total_pl_percent: null,
      unvalued_holding_count: count,
    },
  ]);
  expect(
    screen.getByText(`${count} ${count === 1 ? "holding" : "holdings"} cannot be valued.`, {
      exact: true,
    }),
  ).toBeInTheDocument();
  expect(screen.getByText("Return unavailable", { exact: true })).toBeInTheDocument();
  expect(screen.getByText(/Known value: \$9,000.00/)).toBeInTheDocument();
});
it("shows ten books and the visible cap reason", () => {
  show(
    Array.from({ length: 10 }, (_, i) => ({
      ...cashPortfolio(),
      id: String(i + 1),
      name: `Book ${i + 1}`,
      description: "",
    })),
  );
  expect(screen.getAllByRole("link")).toHaveLength(10);
  expect(screen.getByRole("button", { name: "New portfolio" })).toBeDisabled();
  expect(screen.getByText(/You have 10 active portfolios/)).toBeInTheDocument();
});
it("links each card once and preserves numeric ID order", () => {
  show([
    { ...cashPortfolio(), id: "2", name: "Two", description: "" },
    { ...cashPortfolio(), id: "10", name: "Ten", description: "" },
  ]);
  expect(screen.queryByRole("table")).toBeNull();
  const cards = screen.getAllByRole("listitem");
  expect(cards).toHaveLength(3);
  const create = screen.getByRole("button", { name: "New portfolio" });
  expect(cards[2]).toContainElement(create);
  expect(create).toHaveTextContent(/^New portfolio$/);
  expect(screen.queryByRole("button", { name: "Refresh portfolios" })).toBeNull();
  const links = screen.getAllByRole("link");
  expect(links).toHaveLength(2);
  expect(links[0]).toHaveAccessibleName("Two");
  expect(links[1]).toHaveAccessibleName("Ten");
  expect(links.map((link) => link.getAttribute("href"))).toEqual([
    "/portfolios/2",
    "/portfolios/10",
  ]);
  expect(screen.queryByText("No description.")).toBeNull();
});
it("keeps unknown creation notice after close and allows original retry at cap", () => {
  show(
    Array.from({ length: 10 }, (_, i) => ({
      ...cashPortfolio(),
      id: String(i + 1),
      name: `Book ${i + 1}`,
      description: "",
    })),
  );
  const retry = vi.fn();
  vi.mocked(usePortfolioManagement).mockReturnValue({
    ready: true,
    creation: {
      phase: "unknown",
      attempt: { key: "original", name: "Uncertain", description: "Keep" },
      error: null,
    },
    retryCreation: retry,
  } as unknown as ReturnType<typeof usePortfolioManagement>);
  // Updating the query state represents the next hook publication, not optimistic data.
  cleanup();
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <PortfoliosPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Review original creation" }));
  fireEvent.click(screen.getByRole("button", { name: "Close creation" }));
  expect(screen.getByText(/An original creation request is unresolved/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "New portfolio" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Review original creation" })).toHaveFocus();
  fireEvent.click(screen.getByRole("button", { name: "Review original creation" }));
  fireEvent.click(screen.getByRole("button", { name: "Retry creation" }));
  expect(retry).toHaveBeenCalledOnce();
});
