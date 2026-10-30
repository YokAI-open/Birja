// Run only in ephemeral fake-price / console-email CI, never real-email dev/prod.
import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

test("a new user opens their real cash-only portfolio from Markets", async ({ page }) => {
  await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await page.getByRole("link", { name: "Portfolio", exact: true }).click();
  await expect(page).toHaveURL((url) => url.pathname === "/portfolio");
  await expect(page.getByRole("heading", { level: 1, name: "Portfolio" })).toBeVisible();
  await expect(page.getByText("Compared with your $10,000.00 start")).toBeVisible();
  await expect(page.getByRole("region", { name: "Total portfolio value" })).toContainText(
    "$10,000.00",
  );
  await expect(page.getByRole("region", { name: "Cash" })).toContainText("$10,000.00");
  await expect(page.getByText("No market prices needed")).toBeVisible();
});

test("a stored buy appears in History with its exact fill values", async ({ page }) => {
  await signInNewUser(page);
  await page.getByRole("link", { name: "Trade BTC" }).click();
  await page.getByLabel("Amount").fill("100");
  let stored: Record<string, string> | undefined;
  for (let attempt = 0; attempt < 3; attempt++) {
    const response = page.waitForResponse(
      (r) => r.url().endsWith("/api/v1/trades") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Confirm buy" }).click();
    const result = await response;
    if (result.ok()) {
      stored = (await result.json()) as Record<string, string>;
      break;
    }
    expect(((await result.json()) as { detail: { code: string } }).detail.code).toBe(
      "price_changed",
    );
    await expect(page.getByText("Price updated. Please review again.")).toBeVisible();
  }
  expect(stored).toBeDefined();
  await page.getByRole("link", { name: "History", exact: true }).click();
  await expect(page).toHaveURL((url) => url.pathname === "/history");
  const table = page.getByRole("table", { name: "Trade history" });
  await expect(table).toContainText("Buy");
  const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  const quantity = new Intl.NumberFormat("en-US", { maximumFractionDigits: 8, useGrouping: false });
  await expect(table).toContainText(quantity.format(stored!.quantity as `${number}`));
  await expect(table).toContainText(usd.format(stored!.exec_price as `${number}`));
  await expect(table).toContainText(usd.format(stored!.fee as `${number}`));
  expect(stored!.cash_delta).toMatch(/^-100\.0+$/);
  await expect(table).toContainText(`−${usd.format(stored!.cash_delta.slice(1) as `${number}`)}`);
});
