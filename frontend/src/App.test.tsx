import { useEffect } from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation, useNavigate, useOutletContext, useParams } from "react-router";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { PortfolioContext } from "@/components/PortfolioContext";
import App from "./App";

// Real page migration belongs to24/25; these probes verify shell and boundary
// wiring and captured target identity without claiming future page behavior.
const probes = vi.hoisted(() => ({ mounted: vi.fn() }));
function FinancialProbe({ page }: { page: string }) {
  const target = useOutletContext<PortfolioTarget>();
  const { pathname } = useLocation();
  const { symbol } = useParams();
  useEffect(() => {
    probes.mounted(pathname, target);
  }, [pathname, target]);
  return (
    <>
      <h1>
        {page}
        {symbol ? ` ${symbol}` : ""}
      </h1>
      <PortfolioContext name={target.name} />
      <p>
        Private {target.owner} root {target.portfolioId}
      </p>
      <button>Financial action</button>
    </>
  );
}
vi.mock("@/pages/PortfolioPage", () => ({
  default: () => <FinancialProbe page="Portfolio page" />,
}));
vi.mock("@/pages/HistoryPage", () => ({ default: () => <FinancialProbe page="History page" /> }));
vi.mock("@/pages/TradePage", () => ({ default: () => <FinancialProbe page="Crypto" /> }));
vi.mock("@/pages/StockTradePage", () => ({ default: () => <FinancialProbe page="Stock" /> }));

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const unauthorized = () =>
  json({ detail: { code: "not_authenticated", message: "Unavailable" } }, 401);
const first = { id: "1", name: "My portfolio" },
  second = { id: "2", name: "Second strategy" };
const clients: QueryClient[] = [];
function prices() {
  return json({
    server_time: "2026-11-16T10:00:00Z",
    fresh_seconds: 90,
    stale_seconds: 300,
    items: [
      {
        symbol: "BTC",
        name: "Bitcoin",
        price: "81042.35000000",
        as_of: "2026-11-16T09:59:50Z",
        age_seconds: 10,
        status: "fresh",
      },
    ],
  });
}
function api({
  identity = () => json({ email: "alice@example.test" }),
  metadata = () => json([first]),
}: {
  identity?: () => Response | Promise<Response>;
  metadata?: () => Response | Promise<Response>;
} = {}) {
  const fetch = vi.fn((path: string) =>
    Promise.resolve(
      path === "/api/v2/me"
        ? identity()
        : path === "/api/v2/portfolios"
          ? metadata()
          : path === "/api/v2/portfolios/overview"
            ? json([])
            : path === "/api/v1/prices"
              ? prices()
              : path === "/api/v1/health"
                ? json({ status: "ok", db: "ok", redis: "ok" })
                : path === "/api/v1/auth/refresh"
                  ? unauthorized()
                  : json({}, 500),
    ),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}
function Controls() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => void navigate(-1)}>Back</button>
      <p data-testid="location">{useLocation().pathname}</p>
    </>
  );
}
function setup(route = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  return {
    client,
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[route]}>
          <Controls />
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  };
}
afterEach(() => {
  clients.splice(0).forEach((c) => c.clear());
  vi.unstubAllGlobals();
  probes.mounted.mockReset();
  document.cookie = "bj_csrf=; max-age=0; path=/";
  sessionStorage.clear();
});

it("keeps public Markets, Account and three safe responsive primary destinations", async () => {
  api();
  setup();
  const nav = await screen.findByRole("navigation", { name: "Main" });
  expect(nav.querySelectorAll("a")).toHaveLength(3);
  expect(nav).not.toContainElement(screen.getByRole("link", { name: "Account" }));
  expect(nav.className).toContain("safe-area-inset-bottom");
  expect(screen.getByRole("main").className).toContain("80px");
  for (const a of nav.querySelectorAll("a")) {
    expect(a.className).toContain("min-h-11");
    expect(a.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  }
  expect(await screen.findByText("$81,042.35")).toBeVisible();
  expect(screen.getByRole("link", { name: "Trade BTC" })).toHaveAttribute("href", "/trade/BTC");
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
});
it.each([
  ["/portfolios/1", "Portfolio page"],
  ["/portfolios/1/history", "History page"],
  ["/portfolios/1/trade/BTC", "Crypto BTC"],
  ["/portfolios/1/trade/stocks/AAPL", "Stock AAPL"],
])("hands explicit %s to financial children only after metadata", async (path, heading) => {
  let release!: (value: Response) => void;
  api({
    metadata: () =>
      new Promise((r) => {
        release = r;
      }),
  });
  setup(path);
  expect(await screen.findByRole("status", { name: "Loading portfolio" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  await waitFor(() => expect(release).toBeTypeOf("function"));
  expect(probes.mounted).not.toHaveBeenCalled();
  await act(async () => {
    release(json([first, second]));
  });
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(probes.mounted).toHaveBeenCalledWith(
    path,
    expect.objectContaining({ owner: "alice@example.test", portfolioId: "1", name: first.name }),
  );
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
  expect(screen.getByRole("link", { name: "History" })).toHaveAttribute(
    "href",
    "/portfolios/1/history",
  );
});
it.each([
  ["/portfolio", "/portfolios/1", "Portfolio page"],
  ["/history", "/portfolios/1/history", "History page"],
  ["/trade/BTC", "/portfolios/1/trade/BTC", "Crypto BTC"],
  ["/trade/stocks/AAPL", "/portfolios/1/trade/stocks/AAPL", "Stock AAPL"],
])("replaces legacy %s before financial child mount", async (path, next, heading) => {
  api();
  setup(path);
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(screen.getByTestId("location")).toHaveTextContent(next);
  expect(probes.mounted.mock.calls.every(([url]) => url === next)).toBe(true);
});
it.each([
  { values: [], heading: "No portfolio available" },
  { values: [first, second], heading: "Portfolio required" },
])("never selects or grants on legacy $heading", async ({ values, heading }) => {
  const fetch = api({ metadata: () => json(values) });
  setup("/trade/BTC");
  expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(screen.getByTestId("location")).toHaveTextContent("/trade/BTC");
  expect(
    fetch.mock.calls.every(([url]) => ["/api/v2/me", "/api/v2/portfolios"].includes(url)),
  ).toBe(true);
  expect(screen.queryByRole("combobox")).toBeNull();
});
it.each(["/portfolios/01", "/portfolios/0", "/portfolios/nope/history"])(
  "refuses missing/malformed %s without metadata or finance",
  async (path) => {
    const fetch = api();
    setup(path);
    expect(await screen.findByRole("heading", { name: "Portfolio required" })).toBeVisible();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(["/api/v2/me"]);
  },
);
it("never substitutes a sole other strategy for an explicit unavailable root", async () => {
  api({ metadata: () => json([second]) });
  setup("/portfolios/1/history");
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1/history");
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
});
it("retains verified root through nav, global Markets and trade links", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup("/portfolios/2/history");
  await screen.findByRole("heading", { name: "History page" });
  await user.click(screen.getByRole("link", { name: "Markets" }));
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
  expect(await screen.findByRole("link", { name: "Trade BTC" })).toHaveAttribute(
    "href",
    "/portfolios/2/trade/BTC",
  );
  expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
    "href",
    "/portfolios",
  );
  await user.click(screen.getByRole("link", { name: "Trade BTC" }));
  expect(await screen.findByRole("heading", { name: "Crypto BTC" })).toBeVisible();
  expect(screen.getByText("Private alice@example.test root 2")).toBeVisible();
});
it("focuses route and Back headings without refetch focus theft", async () => {
  api();
  const { client, user } = setup();
  expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
  await user.click(screen.getByRole("link", { name: "Account" }));
  expect(await screen.findByRole("heading", { name: "Account", level: 1 })).toHaveFocus();
  const logout = screen.getByRole("button", { name: "Sign out" });
  logout.focus();
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["me"] });
  });
  expect(logout).toHaveFocus();
  await user.click(screen.getByRole("button", { name: "Back" }));
  expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
});
it("keeps Account identity-only with zero roots and no financial discovery", async () => {
  const fetch = api({ metadata: () => json([]) });
  setup("/account");
  expect(await screen.findByText("alice@example.test")).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled();
  expect(screen.queryByText("Cash")).toBeNull();
  expect(screen.queryByText(/\$10,000/)).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url === "/api/v2/portfolios")).toBe(false);
});
it("masks prior finance and nav memory on account switch", async () => {
  let email = "alice@example.test";
  let values = [first];
  api({ identity: () => json({ email }), metadata: () => json(values) });
  const { client, user } = setup("/portfolios/1");
  await screen.findByText("Private alice@example.test root 1");
  await user.click(screen.getByRole("link", { name: "Markets" }));
  await screen.findByRole("heading", { name: "Markets" });
  email = "bob@example.test";
  values = [];
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["me"] });
  });
  await waitFor(() =>
    expect(screen.getAllByRole("link", { name: "Portfolios" })[0]).toHaveAttribute(
      "href",
      "/portfolios",
    ),
  );
  expect(screen.queryByText(/Private alice/)).toBeNull();
  await user.click(screen.getAllByRole("link", { name: "Portfolios" })[0]!);
  expect(await screen.findByRole("heading", { name: "No portfolios yet" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Financial action" })).toBeNull();
});
it("removes finance on metadata revocation without redirecting", async () => {
  let values = [first];
  api({ metadata: () => json(values) });
  const { client } = setup("/portfolios/1");
  await screen.findByText("Private alice@example.test root 1");
  values = [second];
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios", "alice@example.test"] });
  });
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(screen.queryByText(/Private alice/)).toBeNull();
  expect(screen.getByTestId("location")).toHaveTextContent("/portfolios/1");
});
it("shows account skeleton while identity is pending", () => {
  api({ identity: () => new Promise<Response>(() => {}) });
  setup();
  expect(screen.getByRole("status", { name: "Loading your account" })).toHaveAttribute(
    "aria-busy",
    "true",
  );
  expect(screen.queryByRole("navigation")).toBeNull();
});
it.each(["/account", "/portfolio", "/portfolios/1/history", "/trade/BTC"])(
  "keeps signed-out %s behind OTP",
  async (path) => {
    api({ identity: unauthorized });
    setup(path);
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.queryByRole("navigation", { name: "Main" })).toBeNull();
    expect(probes.mounted).not.toHaveBeenCalled();
  },
);
it("uses existing sign-in flow after metadata401", async () => {
  api({ metadata: unauthorized });
  setup("/portfolios/1");
  expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
  expect(probes.mounted).not.toHaveBeenCalled();
});
it("retries identity failure without synthetic financial fields", async () => {
  let count = 0;
  api({ identity: () => (++count === 1 ? json({}, 500) : json({ email: "alice@example.test" })) });
  const { user } = setup();
  expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach Birja right now.");
  await user.click(screen.getByRole("button", { name: "Try again" }));
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
});
it("redirects unknown paths to Markets", async () => {
  api();
  setup("/unknown");
  expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
});
it("preserves logout CSRF and refuses late identity/root resurrection", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  let defer = false;
  let release!: (r: Response) => void;
  let signal!: AbortSignal;
  const base = api();
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/v2/me" && defer) {
      signal = init!.signal as AbortSignal;
      return new Promise<Response>((r) => {
        release = r;
      });
    }
    if (url === "/api/v1/auth/logout") return Promise.resolve(new Response(null, { status: 204 }));
    return base(url);
  });
  vi.stubGlobal("fetch", fetch);
  const { client, user } = setup("/account");
  await screen.findByRole("button", { name: "Sign out" });
  const query = client.getQueryCache().find({ queryKey: ["me"] });
  defer = true;
  let pending!: Promise<void>;
  act(() => {
    pending = client.invalidateQueries({ queryKey: ["me"] });
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  await user.click(screen.getByRole("button", { name: "Sign out" }));
  expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
  expect(signal.aborted).toBe(true);
  expect(client.getQueryCache().find({ queryKey: ["me"] })).toBe(query);
  const call = fetch.mock.calls.find(([url]) => url === "/api/v1/auth/logout")!;
  expect(new Headers(call[1]!.headers).get("X-CSRF-Token")).toBe("synthetic");
  await act(async () => {
    release(json({ email: "alice@example.test" }));
    await pending;
  });
  expect(client.getQueryData(["me"])).toBeNull();
  expect(screen.queryByRole("navigation")).toBeNull();
});
it("keeps identity visible on logout failure", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  api();
  const { user } = setup("/account");
  await user.click(await screen.findByRole("button", { name: "Sign out" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't sign out. Try again.");
  expect(screen.getByText("alice@example.test")).toBeVisible();
});

it.each([{ values: [] }, { values: [first] }, { values: [first, second] }])(
  "routes the real overview independently of target count $values.length",
  async ({ values }) => {
    const fetch = api({ metadata: () => json(values) });
    setup("/portfolios");
    expect(await screen.findByRole("heading", { name: "Portfolios", level: 1 })).toHaveFocus();
    expect(await screen.findByRole("heading", { name: "No portfolios yet" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Create portfolio" })).toBeEnabled();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.some(([url]) => url === "/api/v2/portfolios/overview")).toBe(true);
  },
);

it("opens a draft choice at detail, preserving the original trade route for Back", async () => {
  api({ metadata: () => json([first, second]) });
  const { user } = setup("/portfolios/1/trade/BTC");
  await screen.findByRole("heading", { name: "Crypto BTC" });
  const select = screen.getByRole("combobox", { name: "Open portfolio" });
  await user.selectOptions(select, "2");
  expect(screen.getByText("Private alice@example.test root 1")).toBeVisible();
  expect(probes.mounted.mock.calls.every(([, target]) => target.portfolioId === "1")).toBe(true);
  await user.click(screen.getByRole("button", { name: "Open selected portfolio" }));
  expect(await screen.findByRole("heading", { name: "Portfolio page" })).toHaveFocus();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/2$/);
  expect(screen.getByText("Private alice@example.test root 2")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Back" }));
  expect(await screen.findByRole("heading", { name: "Crypto BTC" })).toHaveFocus();
  expect(screen.getByText("Private alice@example.test root 1")).toBeVisible();
});

it("navigates a current real creation receipt to its original ID and focuses detail once", async () => {
  document.cookie = "bj_csrf=synthetic; path=/";
  let values: { id: string; name: string }[] = [];
  const base = api({ metadata: () => json(values) });
  const fetch = vi.fn((url: string, init?: RequestInit) => {
    if (url === "/api/v2/portfolios" && init?.method === "POST") {
      values = [{ id: "19", name: "Created strategy" }];
      return Promise.resolve(json({ id: "19", name: "Created strategy", description: "" }, 201));
    }
    return base(url);
  });
  vi.stubGlobal("fetch", fetch);
  const { user, client } = setup("/portfolios");
  await screen.findByRole("heading", { name: "No portfolios yet" });
  await user.click(screen.getByRole("button", { name: "Create portfolio" }));
  const name = screen.getByRole("textbox", { name: "Portfolio name" });
  expect(name).toHaveFocus();
  await user.type(name, "Created strategy");
  await user.click(screen.getAllByRole("button", { name: "Create portfolio" })[1]!);
  const heading = await screen.findByRole("heading", { name: "Portfolio page" });
  expect(heading).toHaveFocus();
  expect(screen.getByTestId("location")).toHaveTextContent(/^\/portfolios\/19$/);
  const action = screen.getByRole("button", { name: "Financial action" });
  action.focus();
  await act(async () => {
    await client.invalidateQueries({ queryKey: ["portfolios"] });
  });
  // Revalidation may replace financial children; route focus must not rerun.
  expect(await screen.findByRole("heading", { name: "Portfolio page" })).not.toHaveFocus();
  expect(fetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
});

it.each(["route", "owner"])(
  "ignores a late real creation receipt after %s departure",
  async (departure) => {
    document.cookie = "bj_csrf=synthetic; path=/";
    let release!: (response: Response) => void;
    const base = api({ metadata: () => json([first, second]) });
    const fetch = vi.fn((url: string, init?: RequestInit) =>
      url === "/api/v2/portfolios" && init?.method === "POST"
        ? new Promise<Response>((resolve) => {
            release = resolve;
          })
        : base(url),
    );
    vi.stubGlobal("fetch", fetch);
    const { user, client } = setup("/portfolios");
    await screen.findByRole("heading", { name: "No portfolios yet" });
    await user.click(screen.getByRole("button", { name: "Create portfolio" }));
    await user.type(
      screen.getByRole("textbox", { name: "Portfolio name" }),
      "Private old creation",
    );
    await user.click(screen.getAllByRole("button", { name: "Create portfolio" })[1]!);
    await waitFor(() => expect(release).toBeTypeOf("function"));
    if (departure === "route") await user.click(screen.getByRole("link", { name: "Markets" }));
    else act(() => client.setQueryData(["me"], { email: "bob@example.test" }));
    await act(async () => {
      release(json({ id: "99", name: "Private old creation", description: "" }, 201));
    });
    await waitFor(() =>
      expect(screen.getByTestId("location")).not.toHaveTextContent("/portfolios/99"),
    );
    expect(screen.queryByText("Private old creation")).toBeNull();
    expect(probes.mounted).not.toHaveBeenCalled();
    expect(fetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  },
);
