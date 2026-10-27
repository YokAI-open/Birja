import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "@/App";
import { renderWithClient } from "@/test/render";
import SignInPage from "./SignInPage";

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "yk_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

type Handler = () => Response;
type Routes = { request?: Handler; verify?: Handler };

const errorResponse = (status: number, code: string, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify({ detail: { code, message: "server text" } }), { status, headers });
const ok = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi(routes: Routes) {
  document.cookie = "yk_csrf=tok; path=/";
  const fetchMock = vi.fn((url: string) => {
    if (url === "/api/v1/auth/request-code") {
      return Promise.resolve((routes.request ?? (() => ok({ status: "code_sent" }, 202)))());
    }
    if (url === "/api/v1/auth/verify-code") {
      return Promise.resolve(
        (routes.verify ?? (() => ok({ email: "a@example.com", cash_usd: "10000.00000000" })))(),
      );
    }
    if (url === "/api/v1/me") {
      return Promise.resolve(errorResponse(401, "not_authenticated"));
    }
    return Promise.resolve(ok({ status: "ok", db: "ok", redis: "ok" }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function toCodeStep(routes: Routes = {}) {
  stubApi(routes);
  const view = renderWithClient(<SignInPage />);
  await view.user.type(screen.getByLabelText("Email"), "a@example.com");
  await view.user.click(screen.getByRole("button", { name: "Send code" }));
  await screen.findByLabelText("6-digit code");
  return view;
}

describe("SignInPage email step", () => {
  it("disables Send code with a helper while the field is empty", () => {
    stubApi({});
    renderWithClient(<SignInPage />);
    expect(screen.getByRole("button", { name: "Send code" })).toBeDisabled();
    expect(screen.getByText("Enter your email to get a code.")).toBeVisible();
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-describedby", "email-help");
  });

  it("moves to the code step with the expiry copy", async () => {
    await toCodeStep();
    expect(
      screen.getByText("We sent a code to a@example.com. It expires in 10 minutes."),
    ).toBeVisible();
    const input = screen.getByLabelText("6-digit code");
    expect(input).toHaveAttribute("autocomplete", "one-time-code");
    expect(input).toHaveAttribute("inputmode", "numeric");
    expect(input).toHaveAttribute("maxlength", "6");
  });

  it.each([
    [422, "validation_error", {}, "Enter a valid email address."],
    [429, "rate_limited", { "Retry-After": "120" }, "Too many attempts. Try again in 2 minutes."],
    [429, "rate_limited", { "Retry-After": "30" }, "Too many attempts. Try again in 30 seconds."],
    [429, "rate_limited", { "Retry-After": "1" }, "Too many attempts. Try again in 1 second."],
    [429, "rate_limited", {}, "Too many attempts. Try again in a moment."],
    [403, "csrf_failed", {}, "Your session token is out of date. Reload the page and try again."],
    [503, "service_unavailable", {}, "Sign-in is temporarily unavailable. Try again in a moment."],
    [500, "boom", {}, "Something went wrong. Try again."],
  ])("shows the right message for %i %s", async (status, code, headers, message) => {
    stubApi({ request: () => errorResponse(status, code, headers) });
    const { user } = renderWithClient(<SignInPage />);
    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(message);
    expect(alert).not.toHaveTextContent("server text");
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", alert.id);
  });

  it("shows a generic message for a non-API failure", async () => {
    stubApi({});
    vi.stubGlobal("fetch", () => Promise.reject(new TypeError("network")));
    const { user } = renderWithClient(<SignInPage />);
    await user.type(screen.getByLabelText("Email"), "a@example.com");
    await user.click(screen.getByRole("button", { name: "Send code" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong. Try again.");
  });
});

describe("SignInPage code step", () => {
  it("keeps Sign in disabled until six digits and strips non-digits", async () => {
    const { user } = await toCodeStep();
    const input = screen.getByLabelText("6-digit code");
    await user.type(input, "12a34");
    expect(input).toHaveValue("1234");
    expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
  });

  it("shows invalid_code under the field", async () => {
    const { user } = await toCodeStep({ verify: () => errorResponse(400, "invalid_code") });
    await user.type(screen.getByLabelText("6-digit code"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(
      "That code is wrong or has expired. Check it or send a new code.",
    );
    const input = screen.getByLabelText("6-digit code");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", alert.id);
  });

  it("does not treat a 422 on the code as an email error", async () => {
    const { user } = await toCodeStep({ verify: () => errorResponse(422, "validation_error") });
    await user.type(screen.getByLabelText("6-digit code"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong. Try again.");
  });

  it("re-requests a code for the same email", async () => {
    const { user } = await toCodeStep();
    await user.click(screen.getByRole("button", { name: "Send a new code" }));
    const fetchMock = vi.mocked(fetch);
    const calls = fetchMock.mock.calls.filter((c) => c[0] === "/api/v1/auth/request-code");
    expect(calls).toHaveLength(2);
    expect(calls[1]?.[1]?.body).toBe(JSON.stringify({ email: "a@example.com" }));
  });

  it("shows a resend error under the code field", async () => {
    let n = 0;
    const { user } = await toCodeStep({
      request: () =>
        ++n === 1 ? ok({ status: "code_sent" }, 202) : errorResponse(503, "service_unavailable"),
    });
    await user.click(screen.getByRole("button", { name: "Send a new code" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign-in is temporarily unavailable.",
    );
  });

  it("returns to the email step with a different email", async () => {
    const { user } = await toCodeStep();
    await user.click(screen.getByRole("button", { name: "Use a different email" }));
    expect(screen.getByLabelText("Email")).toBeVisible();
  });

  it("puts the user in the me cache so the account shows without another /me fetch", async () => {
    const fetchMock = stubApi({});
    const view = renderWithClient(<App />);
    await view.user.type(await screen.findByLabelText("Email"), "a@example.com");
    await view.user.click(screen.getByRole("button", { name: "Send code" }));
    await view.user.type(await screen.findByLabelText("6-digit code"), "123456");
    await view.user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("$10,000.00")).toBeVisible();
    const meCalls = fetchMock.mock.calls.filter((c) => c[0] === "/api/v1/me");
    // The signed-out /me is tried twice (401, silent refresh, retry); sign-in adds none.
    expect(meCalls).toHaveLength(2);
  });
});
