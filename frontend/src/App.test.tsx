import { screen } from "@testing-library/react";
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
