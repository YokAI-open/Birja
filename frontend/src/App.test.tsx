import { act, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useNavigate } from "react-router";
import userEvent from "@testing-library/user-event";
import { fetchHistory } from "@/api/history";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

const health = () =>
  new Response(JSON.stringify({ status: "ok", db: "ok", redis: "ok" }), { status: 200 });

const prices = () =>
  new Response(
    JSON.stringify({
      server_time: "2026-10-28T10:00:00Z",
      fresh_seconds: 90,
      stale_seconds: 300,
      items: [
        ["BTC", "Bitcoin", "81042.35000000"],
        ["ETH", "Ethereum", "3200.10000000"],
      ].map(([symbol, name, price]) => ({
        symbol,
        name,
        price,
        as_of: "2026-10-28T09:59:50Z",
        age_seconds: 10,
        status: "fresh",
      })),
    }),
    { status: 200 },
  );

const route = (url: string, me: () => Response | Promise<Response>) => {
  if (url === "/api/v1/me") return me();
  if (url === "/api/v1/prices") return prices();
  if (url === "/api/v1/holdings/BTC")
    return new Response(JSON.stringify({ symbol: "BTC", quantity: "0" }), { status: 200 });
  return health();
};

function stubApi(me: () => Response | Promise<Response>) {
  const fetchMock = vi.fn((url: string) => Promise.resolve(route(url, me)));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const meOk = () =>
  new Response(JSON.stringify({ email: "a@example.com", cash_usd: "10000.00000000" }), {
    status: 200,
  });

const unauthorized = () =>
  new Response(JSON.stringify({ detail: { code: "not_authenticated", message: "x" } }), {
    status: 401,
  });

describe("App", () => {
  it("keeps Account separate from the three responsive primary destinations", async () => {
    stubApi(meOk);
    renderWithClient(<App />);
    const nav = await screen.findByRole("navigation", { name: "Main" });
    expect(nav.querySelectorAll("a")).toHaveLength(3);
    expect(nav).not.toContainElement(screen.getByRole("link", { name: "Account" }));
    expect(nav.className).toContain("md:static");
    expect(nav.className).toContain("safe-area-inset-bottom");
    expect(screen.getByRole("main").className).toContain("80px");
    for (const link of nav.querySelectorAll("a")) {
      expect(link.className).toContain("min-h-11");
      expect(link.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    }
  });

  it("focuses route headings on direct entry, navigation and Back without refetch theft", async () => {
    stubApi(meOk);
    function Back() {
      const navigate = useNavigate();
      return <button onClick={() => void navigate(-1)}>Back</button>;
    }
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <Back />
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    const user = userEvent.setup();
    expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
    await user.click(screen.getByRole("link", { name: "Account" }));
    expect(await screen.findByRole("heading", { name: "Account", level: 1 })).toHaveFocus();
    const signOut = screen.getByRole("button", { name: "Sign out" });
    signOut.focus();
    await act(async () => {
      await client.invalidateQueries({ queryKey: ["me"] });
    });
    expect(signOut).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Back" }));
    expect(await screen.findByRole("heading", { name: "Markets", level: 1 })).toHaveFocus();
    client.clear();
  });

  it("never shows cached or late A portfolio/history after passive expiry and B sign-in", async () => {
    document.cookie = "bj_csrf=synthetic; path=/";
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const portfolio = (cash: string) => ({
      cash,
      starting_cash: "10000.00",
      total_value: cash,
      total_pl: "0.00",
      total_pl_percent: "0.00",
      cash_allocation_percent: "100.00",
      valuation_complete: true,
      valued_at: "2026-10-30T07:00:00Z",
      prices_as_of: null,
      fresh_seconds: 120,
      stale_seconds: 300,
      holdings: [],
    });
    const aHistory = {
      items: [
        {
          id: "1",
          created_at: "2026-10-30T07:00:00Z",
          symbol: "BTC",
          name: "Private A coin",
          side: "buy",
          quantity: "1",
          exec_price: "100",
          fee: "0.25",
          total: "-100.25",
        },
      ],
      next_cursor: null,
    };
    const response = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), { status });
    let identity: "a" | "expired" | "b" = "a";
    let releaseA!: (r: Response) => void;
    let releasePortfolioB!: (r: Response) => void;
    let releaseHistoryB!: (r: Response) => void;
    let aSignal!: AbortSignal;
    vi.stubGlobal(
      "fetch",
      vi.fn((path: string, init?: RequestInit) => {
        if (path === "/api/v1/me")
          return Promise.resolve(
            identity === "expired"
              ? unauthorized()
              : response({
                  email: `${identity}@example.test`,
                  cash_usd: identity === "a" ? "8123.45" : "10000.00",
                }),
          );
        if (path === "/api/v1/auth/refresh") return Promise.resolve(unauthorized());
        if (path === "/api/v1/auth/request-code")
          return Promise.resolve(response({ status: "code_sent" }, 202));
        if (path === "/api/v1/auth/verify-code") {
          identity = "b";
          return Promise.resolve(response({ email: "b@example.test", cash_usd: "10000.00" }));
        }
        if (path === "/api/v1/portfolio")
          return identity === "a"
            ? Promise.resolve(response(portfolio("8123.45")))
            : new Promise<Response>((resolve) => {
                releasePortfolioB = resolve;
              });
        if (path.startsWith("/api/v1/trades")) {
          if (identity === "a") {
            aSignal = init!.signal as AbortSignal;
            return new Promise<Response>((resolve) => {
              releaseA = resolve;
            });
          }
          return new Promise<Response>((resolve) => {
            releaseHistoryB = resolve;
          });
        }
        return Promise.resolve(health());
      }),
    );
    client.setQueryData(["history"], { pages: [aHistory], pageParams: [undefined] });
    const { container, unmount } = render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/portfolio"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    const user = userEvent.setup();
    expect((await screen.findAllByText("$8,123.45")).length).toBeGreaterThan(0);
    const oldMe = client.getQueryCache().find({ queryKey: ["me"] });
    // Keep an unobserved A read alive even when the signed-in routes unmount.
    const pendingA = client
      .fetchQuery({
        queryKey: ["history", "pending"],
        queryFn: ({ signal }) => fetchHistory({}, signal),
      })
      .catch((error: unknown) => error);
    identity = "expired";
    await act(async () => {
      await client.invalidateQueries({ queryKey: ["me"] });
    });
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(client.getQueryData(["portfolio"])).toEqual(portfolio("8123.45"));
    expect(aSignal.aborted).toBe(false);
    const frames: string[] = [];
    const observer = new MutationObserver(() => {
      frames.push(container.textContent ?? "");
    });
    observer.observe(container, { subtree: true, childList: true, characterData: true });
    await user.type(screen.getByLabelText("Email"), "b@example.test");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    await user.type(await screen.findByLabelText("6-digit code"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(releasePortfolioB).toBeTypeOf("function"));
    expect(client.getQueryCache().find({ queryKey: ["me"] })).toBe(oldMe);
    expect(oldMe!.getObserversCount()).toBe(1);
    expect(aSignal.aborted).toBe(true);
    expect(screen.queryByText("$8,123.45")).toBeNull();
    await user.click(screen.getByRole("link", { name: "History" }));
    await waitFor(() => expect(releaseHistoryB).toBeTypeOf("function"));
    expect(screen.queryByText("Private A coin")).toBeNull();
    await act(async () => {
      releaseA(response(aHistory));
      releasePortfolioB(response(portfolio("10000.00")));
      releaseHistoryB(response({ items: [], next_cursor: null }));
      await pendingA;
    });
    expect(await screen.findByText("No trades yet")).toBeVisible();
    expect(client.getQueryData(["history", "pending"])).toBeUndefined();
    expect(
      frames.every((frame) => !frame.includes("$8,123.45") && !frame.includes("Private A coin")),
    ).toBe(true);
    observer.disconnect();
    unmount();
    client.clear();
    document.cookie = "bj_csrf=; max-age=0; path=/";
  });

  it("shows a loading skeleton while /me is pending", async () => {
    stubApi(() => new Promise<Response>(() => {}));
    renderWithClient(<App />);
    expect(screen.getByText("Birja")).toBeVisible();
    const skeleton = screen.getByRole("status", { name: "Loading your account" });
    expect(skeleton).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByRole("heading", { name: "System status" })).toBeNull();
  });

  it("shows the sign-in card when not authenticated", async () => {
    stubApi(unauthorized);
    renderWithClient(<App />);
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "System status" })).toBeNull();
    expect(screen.queryByRole("navigation", { name: "Main" })).toBeNull();
  });

  it("shows the sign-in card on /account when signed out", async () => {
    stubApi(unauthorized);
    renderWithClient(<App />, { route: "/account" });
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "System status" })).toBeNull();
    expect(screen.queryByRole("navigation", { name: "Main" })).toBeNull();
  });

  it("shows Markets with the nav at / when signed in", async () => {
    stubApi(meOk);
    renderWithClient(<App />);
    expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
    expect(await screen.findByText("$81,042.35")).toBeVisible();
    expect(screen.getByRole("link", { name: "Markets" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Account" })).not.toHaveAttribute("aria-current");
    expect(screen.queryByRole("heading", { name: "System status" })).toBeNull();
  });

  it("falls back to sign-in when prices return 401 mid-session", async () => {
    let meCalls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url === "/api/v1/me") {
          meCalls += 1;
          return Promise.resolve(meCalls === 1 ? meOk() : unauthorized());
        }
        return Promise.resolve(unauthorized());
      }),
    );
    renderWithClient(<App />);
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
  });

  it("shows the trade page at /trade/BTC when signed in", async () => {
    stubApi(meOk);
    renderWithClient(<App />, { route: "/trade/BTC" });
    expect(await screen.findByRole("heading", { level: 1, name: "Trade BTC" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Main" })).toBeVisible();
  });

  it("shows the sign-in card at /trade/BTC when signed out", async () => {
    stubApi(unauthorized);
    renderWithClient(<App />, { route: "/trade/BTC" });
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Trade BTC" })).toBeNull();
  });

  it("redirects unknown paths to Markets", async () => {
    stubApi(meOk);
    renderWithClient(<App />, { route: "/unknown" });
    expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
  });

  it("navigates from Markets to Account", async () => {
    stubApi(meOk);
    const { user } = renderWithClient(<App />);
    await user.click(await screen.findByRole("link", { name: "Account" }));
    expect(await screen.findByText("$10,000.00")).toBeVisible();
    expect(screen.getByRole("link", { name: "Account" })).toHaveAttribute("aria-current", "page");
  });

  it("shows the account view with the formatted balance", async () => {
    stubApi(meOk);
    renderWithClient(<App />, { route: "/account" });
    expect(await screen.findByText("$10,000.00")).toBeVisible();
    expect(screen.getByText("a@example.com")).toBeVisible();
    expect(screen.getByRole("heading", { name: "System status" })).toBeVisible();
  });

  it("shows an error with a retry when /me fails", async () => {
    let calls = 0;
    stubApi(() => {
      calls += 1;
      return calls === 1
        ? new Response("{}", { status: 500 })
        : new Response(JSON.stringify({ email: "a@example.com", cash_usd: "1.00" }), {
            status: 200,
          });
    });
    const { user } = renderWithClient(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Can't reach Birja right now.");
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
  });

  describe("sign out", () => {
    it("signs out and shows the sign-in card", async () => {
      document.cookie = "bj_csrf=tok; path=/";
      let resolveLogout: (r: Response) => void = () => {};
      const fetchMock = vi.fn((url: string) => {
        if (url === "/api/v1/auth/logout") {
          return new Promise<Response>((resolve) => {
            resolveLogout = resolve;
          });
        }
        return Promise.resolve(route(url, meOk));
      });
      vi.stubGlobal("fetch", fetchMock);
      const { user } = renderWithClient(<App />, { route: "/account" });
      await user.click(await screen.findByRole("button", { name: "Sign out" }));
      expect(await screen.findByRole("button", { name: "Signing out…" })).toBeDisabled();
      const call = fetchMock.mock.calls.find(([u]) => u === "/api/v1/auth/logout") as unknown as [
        string,
        RequestInit,
      ];
      expect(new Headers(call[1].headers).get("X-CSRF-Token")).toBe("tok");
      resolveLogout(new Response(null, { status: 204 }));
      expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
      expect(screen.queryByText("$10,000.00")).toBeNull();
      document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    });

    it("keeps the account view and shows an error when sign-out fails", async () => {
      document.cookie = "bj_csrf=tok; path=/";
      vi.stubGlobal(
        "fetch",
        vi.fn((url: string) => {
          if (url === "/api/v1/auth/logout") {
            return Promise.resolve(new Response("{}", { status: 500 }));
          }
          return Promise.resolve(route(url, meOk));
        }),
      );
      const { user } = renderWithClient(<App />, { route: "/account" });
      await user.click(await screen.findByRole("button", { name: "Sign out" }));
      expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't sign out. Try again.");
      expect(screen.getByText("$10,000.00")).toBeVisible();
      document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    });
  });
});
