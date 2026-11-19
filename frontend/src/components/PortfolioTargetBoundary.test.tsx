import { act, cleanup, render, renderHook, screen, waitFor } from "@testing-library/react";
import { useRef, type ReactNode } from "react";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation, useOutletContext } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { PortfolioContext } from "./PortfolioContext";
import { PortfolioTargetBoundary } from "./PortfolioTargetBoundary";

const owner = "alice@example.test";
const first = { id: "1", name: "My portfolio" };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const clients: QueryClient[] = [];
function FinancialChild() {
  const target = useOutletContext<PortfolioTarget>();
  return (
    <>
      <h1>Financial page</h1>
      <PortfolioContext name={target.name} />
      <p>Private cash 8123.45</p>
      <button>Confirm order</button>
    </>
  );
}
function Location() {
  return <p data-testid="location">{useLocation().pathname}</p>;
}
function setup(route = "/portfolios/1", legacy = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: owner });
  const ui = render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <Location />
        <Routes>
          <Route path="/portfolios/:portfolioId" element={<PortfolioTargetBoundary />}>
            <Route index element={<FinancialChild />} />
          </Route>
          <Route
            path="/portfolio"
            element={
              <PortfolioTargetBoundary
                legacyDestination={legacy ? (id) => `/portfolios/${id}` : undefined}
              />
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { client, ...ui };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((c) => c.clear());
  vi.unstubAllGlobals();
  sessionStorage.clear();
});
function ExternallyHeadedBoundary() {
  const heading = useRef<HTMLHeadingElement>(null);
  return <><h1 ref={heading} tabIndex={-1}>Portfolio unavailable</h1><PortfolioTargetBoundary primaryHeading={heading} /></>;
}
it("uses a supplied primary heading for private refusal without duplicating it", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([])));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: owner });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/portfolios/1"]}><Routes><Route path="/portfolios/:portfolioId" element={<ExternallyHeadedBoundary />} /></Routes></MemoryRouter></QueryClientProvider>);
  await screen.findByText("This portfolio is unavailable. Choose another portfolio from Portfolios.");
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.getByRole("heading", { name: "Portfolio unavailable" })).toHaveFocus();
});
it("removes focused financial controls at confirmed submit and keeps only an unresolved-order boolean", async () => {
  document.cookie = "bj_csrf=test; path=/";
  vi.stubGlobal("fetch", (_url: string, init?: RequestInit) =>
    init?.method === "DELETE"
      ? Promise.reject(new TypeError("lost response"))
      : Promise.resolve(json([first])),
  );
  const { client } = setup();
  const confirm = await screen.findByRole("button", { name: "Confirm order" });
  confirm.focus();
  client.setQueryDefaults(["cryptoTradeState"], { gcTime: Infinity });
  client.setQueryData(["cryptoTradeState", owner, "1", 0, "BTC"], {
    phase: "unknown",
    attempt: { idempotency_key: "private-original-key", order: { amount_usd: "8123.45" } },
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const deletion = renderHook(() => usePortfolioDeletion("1"), { wrapper });
  await waitFor(() => expect(deletion.result.current.ready).toBe(true));
  act(() => {
    const metadata = { ...first, description: "Private description" };
    client.setQueryData(["portfolioMetadata", owner, "1", 0], metadata);
    expect(deletion.result.current.reviewDeletion(metadata)).toBe(true);
  });
  await act(async () => deletion.result.current.confirmDeletion());
  const heading = await screen.findByRole("heading", { name: "Portfolio unavailable" });
  expect(heading).toHaveFocus();
  expect(
    screen.queryByText(/Private cash|My portfolio|Private description|private-original-key/),
  ).toBeNull();
  expect(screen.queryByRole("button", { name: /Confirm order|retry/i })).toBeNull();
  expect(screen.getByText(/earlier order's result is unconfirmed/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
});

it("renders full escaped names with natural narrow-screen wrapping and no chooser", async () => {
  const name = "<script>" + "A".repeat(43) + "</script>";
  vi.stubGlobal("fetch", () => Promise.resolve(json([{ id: "1", name }])));
  const { container } = setup();
  const value = await screen.findByText(name);
  expect(value.tagName).toBe("DD");
  expect(value.className).toContain("min-w-0");
  expect(value.className).toContain("overflow-wrap:anywhere");
  expect(value.className).not.toMatch(/truncate|whitespace-nowrap/);
  expect(container.querySelector("script")).toBeNull();
  expect(screen.queryByRole("combobox")).toBeNull();
  expect(screen.getByText("Portfolio").closest("dl")).not.toHaveAttribute("aria-live");
});
it("never mounts financial children while metadata is loading", () => {
  vi.stubGlobal("fetch", () => new Promise<Response>(() => {}));
  setup();
  expect(screen.getByRole("status", { name: "Loading portfolio" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
  expect(screen.queryByText(/Private cash/)).toBeNull();
  expect(screen.queryByRole("button", { name: "Confirm order" })).toBeNull();
});
it.each([{ items: [] }, { items: [{ id: "2", name: "Other" }] }])(
  "hides unavailable finance and focuses its non-enumerating refusal",
  async ({ items }) => {
    vi.stubGlobal("fetch", () => Promise.resolve(json(items)));
    setup();
    const heading = await screen.findByRole("heading", { name: "Portfolio unavailable" });
    expect(heading).toHaveFocus();
    expect(
      screen.getByText("This portfolio is unavailable. Choose another portfolio from Portfolios."),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
    expect(screen.getByRole("link", { name: "Return to Markets" })).toHaveAttribute("href", "/");
    expect(screen.queryByText(/Private cash/)).toBeNull();
  },
);
it.each(["0", "01", "nope", "9223372036854775808"])(
  "does not query malformed explicit target %s",
  async (id) => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    setup(`/portfolios/${id}`);
    expect(await screen.findByRole("heading", { name: "Portfolio required" })).toBeVisible();
    expect(fetch).not.toHaveBeenCalled();
  },
);
it.each([
  {
    values: [],
    heading: "No portfolio available",
    body: "You're signed in, but no portfolio is available. You can still browse Markets or sign out.",
    action: "Browse markets",
  },
  {
    values: [first, { id: "2", name: "Second" }],
    heading: "Portfolio required",
    body: "Open a portfolio-specific link to continue. No portfolio was selected.",
    action: "Return to Markets",
  },
])(
  "legacy $heading never picks or creates a replacement",
  async ({ values, heading, body, action }) => {
    const fetch = vi.fn(() => Promise.resolve(json(values)));
    vi.stubGlobal("fetch", fetch);
    setup("/portfolio", true);
    expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
    expect(screen.getByText(body)).toBeVisible();
    expect(screen.getByRole("link", { name: action })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Portfolios" })).toHaveAttribute("href", "/portfolios");
    expect(screen.getByTestId("location")).toHaveTextContent("/portfolio");
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0]).toEqual(expect.arrayContaining(["/api/v2/portfolios"]));
  },
);
it("replaces a sole legacy entry before mounting financial children", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([first])));
  setup("/portfolio", true);
  expect(await screen.findByText(/Private cash/)).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1");
});
it("refuses missing target unless discovery was explicitly enabled", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  setup("/portfolio");
  expect(await screen.findByRole("heading", { name: "Portfolio required" })).toBeVisible();
  expect(fetch).not.toHaveBeenCalled();
});
it("retries metadata failures at the same target without exposing old finance", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json({}, 500))
    .mockResolvedValue(json([first]));
  vi.stubGlobal("fetch", fetch);
  setup();
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Can't load this portfolio right now. Try again.",
  );
  expect(screen.queryByText(/Private cash/)).toBeNull();
  await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByText(/Private cash/)).toBeVisible();
  expect(fetch.mock.calls.every(([url]) => url === "/api/v2/portfolios")).toBe(true);
});
it("removes finance on root loss without stealing focus from a persistent external control", async () => {
  let values = [first];
  vi.stubGlobal("fetch", () => Promise.resolve(json(values)));
  const { client } = setup();
  await screen.findByRole("button", { name: "Confirm order" });
  const action = document.createElement("button");
  document.body.append(action);
  action.focus();
  values = [];
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios", owner] });
  });
  const heading = await screen.findByRole("heading", { name: "Portfolio unavailable" });
  expect(heading).not.toHaveFocus();
  expect(action).toHaveFocus();
  action.remove();
  expect(heading.closest("section")).toHaveAttribute("aria-live", "polite");
  expect(screen.queryByText(/Private cash/)).toBeNull();
  expect(screen.queryByRole("button", { name: "Confirm order" })).toBeNull();
});
it("masks prior finances immediately when the signed-in owner changes", async () => {
  let release!: (r: Response) => void;
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json([first]))
    .mockImplementation(
      () =>
        new Promise<Response>((r) => {
          release = r;
        }),
    );
  vi.stubGlobal("fetch", fetch);
  const { client } = setup();
  await screen.findByText(/Private cash/);
  act(() => client.setQueryData(["me"], { email: "bob@example.test" }));
  await waitFor(() => expect(screen.queryByText(/Private cash/)).toBeNull());
  await act(async () => {
    release(json([]));
  });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
});

it.each(["cryptoTradeState", "stockTradeState"])(
  "shows only an unresolved boolean for unavailable original %s",
  async (prefix) => {
    vi.stubGlobal("fetch", () => Promise.resolve(json([])));
    const { client } = setup();
    client.setQueryDefaults([prefix], { gcTime: Infinity });
    act(() =>
      client.setQueryData([prefix, owner, "1", 0, "BTC"], {
        phase: "unknown",
        attempt: { private_amount: "8123.45" },
      }),
    );
    const notice = await screen.findByText(
      "An earlier order's result is unconfirmed for this unavailable portfolio. It won't be retried in another portfolio.",
    );
    expect(notice).toBeVisible();
    expect(screen.queryByText(/8123.45/)).toBeNull();
    expect(screen.queryByRole("button", { name: /Confirm|Check order/ })).toBeNull();
    act(() => client.setQueryData(["me"], null));
    await waitFor(() => expect(screen.queryByText(/An earlier order's result/)).toBeNull());
  },
);
it("does not disclose a sibling, foreign-owner or prior-session unresolved attempt", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([])));
  const { client } = setup();
  act(() => {
    client.setQueryData(["cryptoTradeState", owner, "2", 0, "BTC"], {
      phase: "unknown",
      attempt: {},
    });
    client.setQueryData(["stockTradeState", "other@example.test", "1", 0], {
      phase: "unknown",
      attempt: {},
    });
    client.setQueryData(["cryptoTradeState", owner, "1", -1, "BTC"], {
      phase: "unknown",
      attempt: {},
    });
  });
  await screen.findByRole("heading", { name: "Portfolio unavailable" });
  expect(screen.queryByText(/An earlier order's result/)).toBeNull();
});

it("immediately removes an original unknown notice when the authenticated owner changes", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([])));
  const { client } = setup();
  client.setQueryDefaults(["cryptoTradeState"], { gcTime: Infinity });
  act(() =>
    client.setQueryData(["cryptoTradeState", owner, "1", 0, "BTC"], {
      phase: "unknown",
      attempt: {},
    }),
  );
  await screen.findByText(/An earlier order's result is unconfirmed/);
  act(() => client.setQueryData(["me"], { email: "new-owner@example.test" }));
  await waitFor(() => expect(screen.queryByText(/An earlier order's result/)).toBeNull());
  expect(screen.queryByRole("button", { name: /Confirm|Check order/ })).toBeNull();
});
