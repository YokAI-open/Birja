// Phase 3 happy path. Needs the full compose stack with PRICE_SOURCE=fake (CI sets it).
// Never run it against a stack whose email backend is resend.
import { expect, test } from "@playwright/test";
import { portfolioId, signInNewUser } from "./helpers.js";

test("a signed-in user sees live prices for the curated coins", async ({ page, browser }) => {
  test.setTimeout(90_000);

  await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await expect(page).toHaveURL((url) => url.pathname === "/");

  const assets = page.getByRole("list", { name: "Crypto" });
  const rows = assets.getByRole("button");
  await expect(rows).toHaveCount(15);
  for (const symbol of ["BTC", "ETH", "DOGE"]) {
    await expect(rows.filter({ hasText: symbol })).toBeVisible();
  }
  for (const row of await rows.all()) {
    await expect(row).toContainText(/\$[\d,]+\.\d{2,}/);
  }

  const search = page.getByRole("searchbox", { name: "Search by name or symbol" });
  await search.fill("ethereum");
  await expect(rows).toHaveCount(1);
  await rows.first().click();
  await expect(page.getByRole("heading", { name: "Ethereum" })).toBeVisible();
  await expect(page.getByText(/^Updated \d+s ago$/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Trade ETH" })).toHaveAttribute("href", "/trade/ETH");
  const back = page.getByRole("button", { name: "All assets" });
  if (await back.isVisible()) await back.click();

  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const stocks = page.getByRole("list", { name: "US stocks", exact: true });
  await expect(stocks.getByRole("button")).toHaveCount(20);
  await stocks.getByRole("button", { name: /AAPL/ }).click();
  await expect(page.getByRole("note", { name: "Stock price source" })).toContainText("IEX prices");

  // Refetch without reload (PRICE-03).
  await page.waitForResponse((r) => r.url().endsWith("/api/v1/prices") && r.status() === 200, {
    timeout: 45_000,
  });

  await expect(page.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();
  const id = await portfolioId(page);
  await page.goto(`/portfolios/${id}`);
  await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText("$10,000.00");

  // The redirect from unknown paths happens client-side after load, so wait for it.
  await page.goto("/nope");
  await expect(page).toHaveURL((url) => url.pathname === "/");
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();

  // Signed out (D-02): a fresh context sees sign-in, not Markets.
  const fresh = await browser.newContext();
  const anon = await fresh.newPage();
  await anon.goto("/");
  await expect(anon.getByRole("button", { name: "Send code" })).toBeVisible();
  await expect(anon.getByRole("heading", { name: "Markets" })).toHaveCount(0);
  await fresh.close();
});
