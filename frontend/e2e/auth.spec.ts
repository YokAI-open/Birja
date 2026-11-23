import { expect, test } from "@playwright/test";
import { portfolioId, readCodeFromLogs, signInNewUser } from "./helpers.js";

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
