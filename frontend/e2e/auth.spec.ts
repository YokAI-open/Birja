import { expect, test } from "@playwright/test";
import { portfolioId, readCodeFromLogs, signInNewUser } from "./helpers.js";
import { capturePhase25, testPhase25Reflow } from "./phase25-review-capture.js";

test("a new user signs in, stays signed in, signs out and signs in again", async ({
  page,
  context,
}) => {
  const email = await signInNewUser(page);
  const code = await readCodeFromLogs(email);
  const id = await portfolioId(page);
  async function fundedPortfolio() {
    expect(await portfolioId(page)).toBe(id);
    const response = await page.request.get(`/api/v2/portfolios/${id}`);
    expect(response.status()).toBe(200);
    expect(await response.json()).toMatchObject({
      portfolio_id: id,
      cash: "10000.00",
      starting_cash: "10000.00",
      holdings: [],
    });
    await page.goto(`/portfolios/${id}`);
    await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText(
      "$10,000.00",
    );
  }

  await expect(page.getByRole("heading", { name: "Markets" })).toBeVisible();
  await fundedPortfolio();
  await page.reload();
  await expect(page.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();

  // Use the stable status route before simulating expiration. In-flight
  // portfolio reads can otherwise race the deliberate cookie removal.
  await page.goto("/health");
  await expect(page.getByText("All systems operational")).toBeVisible();

  // Access cookie gone: the app refreshes silently and stays signed in.
  await context.clearCookies({ name: "bj_access" });
  await page.reload();
  await expect(page.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();
  await fundedPortfolio();

  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Cash", exact: true })).toHaveCount(0);
  await page.reload();
  await page.getByRole("button", { name: "Go to sign-in form" }).click();
  await expect(page.getByLabel("Email")).toBeFocused();

  // Signing in again never adds cash.
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send code" }).click();
  const code2 = await readCodeFromLogs(email, code);
  await page.getByLabel("6-digit code").fill(code2);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(`/portfolios/${id}`);
  await expect(page.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();
  await fundedPortfolio();
});

test("Phase 25 email panel matches the reference and a generated code signs in and out", async ({
  page,
}, info) => {
  test.setTimeout(90_000);
  await page.goto("/");
  const emailField = page.getByLabel("Email", { exact: true });
  const send = page.getByRole("button", { name: "Send code", exact: true });
  await expect(emailField).toHaveValue("");
  await expect(emailField).toHaveAttribute("autocomplete", "email");
  await capturePhase25(page, info, "sign-in");

  await emailField.fill("invalid-email");
  await testPhase25Reflow(page, emailField, send, page.getByText("Email", { exact: true }));
  const requestCode = () =>
    page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/v1/auth/request-code" &&
        response.request().method() === "POST",
    );
  const invalid = requestCode();
  await page.keyboard.press("Enter");
  expect((await invalid).status()).toBe(422);
  await expect(page.getByRole("alert")).toContainText("Enter a valid email address.");
  await expect(emailField).toHaveAttribute("aria-invalid", "true");

  const syntheticEmail = `e2e-phase25-${crypto.randomUUID()}@example.com`;
  await emailField.fill(syntheticEmail);
  const sent = requestCode();
  await send.click();
  expect((await sent).status()).toBe(202);
  const codeField = page.getByLabel("6-digit code", { exact: true });
  await expect(codeField).toBeFocused();
  await expect(codeField).toHaveValue("");
  await expect(codeField).toHaveAttribute("autocomplete", "one-time-code");
  await page.screenshot({ path: info.outputPath("sign-in-code-blank.png") });

  const code = await readCodeFromLogs(syntheticEmail);
  await codeField.fill(code);
  const verified = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/v2/auth/verify-code" &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  expect((await verified).status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  const signedOut = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/v1/auth/logout" &&
      response.request().method() === "POST",
  );
  const door = page.getByRole("button", { name: "Sign out", exact: true });
  await door.focus();
  await page.keyboard.press("Enter");
  expect((await signedOut).status()).toBe(204);
  await expect(emailField).toBeFocused();
  await expect(emailField).toHaveValue("");
});
