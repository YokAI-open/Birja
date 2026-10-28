// Phase 3 happy path. Needs the full compose stack with PRICE_SOURCE=fake (CI sets it).
// Never run it against a stack whose email backend is resend.
import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

test("a signed-in user sees live prices for the curated coins", async ({ page, browser }) => {
  test.setTimeout(90_000);

  const email = await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  expect(new URL(page.url()).pathname).toBe("/");

  const table = page.getByRole("table", { name: "Markets" });
  await expect(table.getByRole("row")).toHaveCount(16);
  await expect(table.getByRole("row", { name: /BTC/ })).toBeVisible();
  await expect(table.getByRole("row", { name: /ETH/ })).toBeVisible();
  await expect(table.getByRole("row", { name: /DOGE/ })).toBeVisible();

  const priceCol = (await table.getByRole("columnheader").allTextContents()).findIndex((t) =>
    /^Price$/.test(t.trim()),
  );
  expect(priceCol).toBeGreaterThanOrEqual(0);
  const prices = await table.locator(`tbody tr td:nth-child(${priceCol + 1})`).allTextContents();
  expect(prices).toHaveLength(15);
  for (const price of prices) {
    expect(price.trim()).toMatch(/^\$[\d,]+\.\d{2,}$/);
  }

  await expect(page.getByText(/^Live · \d+s ago$/).first()).toBeVisible();

  // Refetch without reload (PRICE-03).
  await page.waitForResponse((r) => r.url().endsWith("/api/v1/prices") && r.status() === 200, {
    timeout: 45_000,
  });

  await page.getByRole("link", { name: "Account" }).click();
  expect(new URL(page.url()).pathname).toBe("/account");
  await expect(page.getByText("$10,000.00")).toBeVisible();
  await expect(page.getByText(email)).toBeVisible();

  await page.goto("/nope");
  expect(new URL(page.url()).pathname).toBe("/");
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();

  // Signed out (D-02): a fresh context sees sign-in, not Markets.
  const fresh = await browser.newContext();
  const anon = await fresh.newPage();
  await anon.goto("/");
  await expect(anon.getByRole("button", { name: "Send code" })).toBeVisible();
  await expect(anon.getByRole("heading", { name: "Markets" })).toHaveCount(0);
  await fresh.close();
});
