import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "@/App";
import { renderWithClient } from "@/test/render";
import SignInPage from "./SignInPage";

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

type Handler = () => Response | Promise<Response>;
type Routes = { request?: Handler; verify?: Handler };

const errorResponse = (status: number, code: string, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify({ detail: { code, message: "server text" } }), { status, headers });
const ok = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function stubApi(routes: Routes) {
  document.cookie = "bj_csrf=tok; path=/";
  const fetchMock = vi.fn((url: string) => {
    if (url === "/api/v1/auth/request-code") {
      return Promise.resolve((routes.request ?? (() => ok({ status: "code_sent" }, 202)))());
    }
    if (url === "/api/v2/auth/verify-code") {
      return Promise.resolve((routes.verify ?? (() => ok({ email: "a@example.com" })))());
    }
    if (url === "/api/v2/me") {
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
  it("labels the email field for autofill and disables Send code while empty", () => {
    stubApi({});
    renderWithClient(<SignInPage />);
    expect(screen.getByRole("button", { name: "Send code" })).toBeDisabled();
    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Email")).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText("Email")).toHaveAttribute("inputmode", "email");
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
    expect(input).toHaveFocus();
  });

  it("sends one request when submissions repeat before the pending state renders", async () => {
    let release!: (response: Response) => void;
    const fetchMock = stubApi({
      request: () => new Promise((resolve) => (release = resolve)),
    });
    const { user } = renderWithClient(<SignInPage />);
    const email = screen.getByLabelText("Email");
    await user.type(email, "a@example.com");
    await user.tab();
    const submit = screen.getByRole("button", { name: "Send code" });
    expect(submit).toHaveFocus();
    const form = email.closest("form")!;
    act(() => {
      fireEvent.submit(form);
      fireEvent.submit(form);
    });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByRole("button", { name: "Sending…" })).toBe(submit);
    expect(submit).toHaveAttribute("aria-disabled", "true");
    expect(submit).toHaveFocus();
    await act(async () => release(ok({ status: "code_sent" }, 202)));
    expect(await screen.findByLabelText("6-digit code")).toHaveFocus();
  });

  it.each([
    [422, "validation_error", {}, "Enter a valid email address."],
    [429, "rate_limited", { "Retry-After": "120" }, "Too many attempts. Try again in 2 minutes."],
    [429, "rate_limited", { "Retry-After": "30" }, "Too many attempts. Try again in 30 seconds."],
    [429, "rate_limited", { "Retry-After": "1" }, "Too many attempts. Try again in 1 second."],
    [429, "rate_limited", {}, "Too many attempts. Try again in a moment."],
    [403, "csrf_failed", {}, "Your session token is out of date. Reload the page and try again."],
    [403, "registration_closed", {}, "Birja isn’t accepting registrations at the moment."],
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

  it.each([
    [400, "invalid_code", "That code is wrong or has expired. Check it or send a new code."],
    [403, "registration_closed", "Birja isn’t accepting registrations at the moment."],
  ])("shows the %s %s message under the code field", async (status, code, message) => {
    const { user } = await toCodeStep({ verify: () => errorResponse(status, code) });
    await user.type(screen.getByLabelText("6-digit code"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(message);
    const input = screen.getByLabelText("6-digit code");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", alert.id);
  });

  it.each([false, true])(
    "retains focus after a failed verification when focus moves: %s",
    async (moveFocus) => {
      let release!: (response: Response) => void;
      const { user } = await toCodeStep({
        verify: () => new Promise((resolve) => (release = resolve)),
      });
      const input = screen.getByLabelText("6-digit code");
      await user.paste("123456");
      expect(input).toHaveValue("123456");
      await user.tab();
      const submit = screen.getByRole("button", { name: "Sign in" });
      expect(submit).toHaveFocus();
      const form = input.closest("form")!;
      act(() => {
        fireEvent.submit(form);
        fireEvent.submit(form);
      });
      const verificationCalls = () =>
        vi.mocked(fetch).mock.calls.filter(([url]) => url === "/api/v2/auth/verify-code");
      await waitFor(() => expect(verificationCalls()).toHaveLength(1));
      expect(await screen.findByRole("button", { name: "Signing in…" })).toBe(submit);
      expect(submit).toHaveAttribute("aria-disabled", "true");
      expect(submit).toHaveFocus();
      const resend = screen.getByRole("button", { name: "Send a new code" });
      expect(resend).toHaveAttribute("aria-disabled", "true");
      expect(screen.getByRole("button", { name: "Use a different email" })).toHaveAttribute(
        "aria-disabled",
        "true",
      );
      if (moveFocus) await user.tab();
      await user.keyboard("{Enter}");
      expect(verificationCalls()).toHaveLength(1);
      expect(
        vi.mocked(fetch).mock.calls.filter(([url]) => url === "/api/v1/auth/request-code"),
      ).toHaveLength(1);
      await act(async () => release(errorResponse(503, "service_unavailable")));
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "Sign-in is temporarily unavailable.",
      );
      expect(submit).not.toHaveAttribute("aria-disabled");
      expect(moveFocus ? resend : submit).toHaveFocus();
    },
  );

  it("does not treat a 422 on the code as an email error", async () => {
    const { user } = await toCodeStep({ verify: () => errorResponse(422, "validation_error") });
    await user.type(screen.getByLabelText("6-digit code"), "123456");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong. Try again.");
  });

  it.each([false, true])(
    "clears the code after keyboard resend when focus moves: %s",
    async (moveFocus) => {
      let release!: (response: Response) => void;
      const request = vi.fn<Handler>().mockReturnValueOnce(ok({ status: "code_sent" }, 202));
      request.mockImplementation(() => new Promise((resolve) => (release = resolve)));
      const { user } = await toCodeStep({ request });
      const input = screen.getByLabelText("6-digit code");
      await user.type(input, "123456");
      await user.tab();
      await user.tab();
      const resend = screen.getByRole("button", { name: "Send a new code" });
      expect(resend).toHaveFocus();
      await user.keyboard("{Enter}");
      expect(await screen.findByRole("button", { name: "Sending…" })).toBe(resend);
      expect(resend).toHaveAttribute("aria-disabled", "true");
      expect(resend).toHaveFocus();
      await user.keyboard("{Enter}");
      if (moveFocus) await user.tab();
      const fetchMock = vi.mocked(fetch);
      const calls = fetchMock.mock.calls.filter((c) => c[0] === "/api/v1/auth/request-code");
      expect(calls).toHaveLength(2);
      expect(calls[1]?.[1]?.body).toBe(JSON.stringify({ email: "a@example.com" }));
      await act(async () => release(ok({ status: "code_sent" }, 202)));
      await waitFor(() => expect(input).toHaveValue(""));
      expect(
        moveFocus ? screen.getByRole("button", { name: "Use a different email" }) : input,
      ).toHaveFocus();
    },
  );

  it("shows a resend error under the code field", async () => {
    let n = 0;
    const { user } = await toCodeStep({
      request: () =>
        ++n === 1 ? ok({ status: "code_sent" }, 202) : errorResponse(503, "service_unavailable"),
    });
    const resend = screen.getByRole("button", { name: "Send a new code" });
    await user.tab();
    expect(resend).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign-in is temporarily unavailable.",
    );
    expect(resend).toHaveFocus();
    expect(resend).not.toHaveAttribute("aria-disabled");
  });

  it("returns to the email step with a different email", async () => {
    const { user } = await toCodeStep();
    await user.click(screen.getByRole("button", { name: "Use a different email" }));
    expect(screen.getByLabelText("Email")).toHaveFocus();
  });

  it("puts the user in the me cache so Markets opens without another /me fetch", async () => {
    const fetchMock = stubApi({});
    const view = renderWithClient(<App />);
    const door = await screen.findByRole("button", { name: "Go to sign-in form" });
    await view.user.click(door);
    const email = screen.getByLabelText("Email");
    expect(email).toHaveFocus();
    await view.user.type(email, "a@example.com");
    await view.user.click(screen.getByRole("button", { name: "Send code" }));
    const code = await screen.findByLabelText("6-digit code");
    await view.user.click(door);
    expect(code).toHaveFocus();
    await view.user.type(code, "123456");
    await view.user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Markets" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeVisible();
    const meCalls = fetchMock.mock.calls.filter((c) => c[0] === "/api/v2/me");
    // The signed-out /me is tried twice (401, silent refresh, retry); sign-in adds none.
    expect(meCalls).toHaveLength(2);
  });
});
