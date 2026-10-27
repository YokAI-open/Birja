import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

const health = () =>
  new Response(JSON.stringify({ status: "ok", db: "ok", redis: "ok" }), { status: 200 });

function stubApi(me: () => Response | Promise<Response>) {
  const fetchMock = vi.fn((url: string) => Promise.resolve(url === "/api/v1/me" ? me() : health()));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

const unauthorized = () =>
  new Response(JSON.stringify({ detail: { code: "not_authenticated", message: "x" } }), {
    status: 401,
  });

describe("App", () => {
  it("shows a loading skeleton while /me is pending", async () => {
    stubApi(() => new Promise<Response>(() => {}));
    renderWithClient(<App />);
    expect(screen.getByText("YokaiExchange")).toBeVisible();
    const skeleton = screen.getByRole("status", { name: "Loading your account" });
    expect(skeleton).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("heading", { name: "System status" })).toBeVisible();
    expect(await screen.findByText("All systems operational")).toBeVisible();
  });

  it("shows the sign-in card when not authenticated", async () => {
    stubApi(unauthorized);
    renderWithClient(<App />);
    expect(await screen.findByRole("button", { name: "Send code" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "System status" })).toBeVisible();
  });

  it("shows the account view with the formatted balance", async () => {
    stubApi(
      () =>
        new Response(JSON.stringify({ email: "a@example.com", cash_usd: "10000.00000000" }), {
          status: 200,
        }),
    );
    renderWithClient(<App />);
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
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Can't reach YokaiExchange right now.",
    );
    expect(screen.getByRole("heading", { name: "System status" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("$1.00")).toBeVisible();
  });
});
