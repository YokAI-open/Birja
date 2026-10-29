// Phase 4 happy path. Needs the full compose stack with PRICE_SOURCE=fake (CI sets it).
// Never run it against a stack whose email backend is resend: it creates accounts and trades.
import { expect, test, type Page } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

// Fake prices move on each minute boundary, so a legitimate price_changed can happen between
// preview and confirm (TRADE-05). Confirm again, bounded to 3 attempts.
async function confirmUntilFilled(page: Page, button: "Confirm buy" | "Confirm sell") {
  const filled = page.getByRole("heading", { name: "Order filled" });
  const changed = page.getByText("Price updated. Please review again.");
  for (let attempt = 0; attempt < 3; attempt++) {
    await page.getByRole("button", { name: button }).click();
    await expect(filled.or(changed)).toBeVisible();
    if (await filled.isVisible()) {
      return;
    }
  }
  throw new Error(`${button} did not fill after 3 attempts`);
}

test("a signed-in user buys $100 of BTC and sells the whole position", async ({ page }) => {
  test.setTimeout(120_000);

  // (1) Markets row -> trade page.
  await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await page.getByRole("link", { name: "Trade BTC" }).click();
  await expect(page).toHaveURL((url) => url.pathname === "/trade/BTC");
  await expect(page.getByRole("heading", { level: 1, name: "Trade BTC" })).toBeVisible();
  await expect(page.getByText(/^Live · \d+s ago$/).first()).toBeVisible();

  // (2) Buy by amount: preview shows the full cost, cash change equals the typed amount.
  await page.getByLabel("Amount").fill("100");
  const preview = page.getByRole("region", { name: "Preview" });
  for (const row of ["Market price", "Execution price", "Fee", "Quantity", "Total cash change"]) {
    await expect(preview.getByText(row, { exact: true })).toBeVisible();
  }
  await expect(preview.getByText("Total cash change").locator("..")).toContainText("$100.00");

  // (3) Fill: exact cents.
  await confirmUntilFilled(page, "Confirm buy");
  const fill = page.getByRole("region", { name: "Order filled" });
  await expect(fill.getByText("New cash balance").locator("..")).toContainText("$9,900.00");
  await expect(fill.getByText("Fee", { exact: true }).locator("..")).toContainText("$0.25");

  // (4) Sell the whole position by quantity.
  await page.getByRole("button", { name: "New order" }).click();
  await page.getByRole("radio", { name: "Sell" }).click();
  const hold = page.getByText(/You hold ([\d.]+) BTC/);
  await expect(hold).toBeVisible();
  const held = /You hold ([\d.]+) BTC/.exec((await hold.textContent()) ?? "")?.[1];
  expect(held).toBeTruthy();
  expect(Number(held)).toBeGreaterThan(0);
  await page.getByLabel("Quantity").fill(held as string);
  const sellPreview = page.getByRole("region", { name: "Preview" });
  await expect(sellPreview.getByText("Total cash change").locator("..")).toContainText(/\+?\$\d/);
  await confirmUntilFilled(page, "Confirm sell");

  // (5) Round trip costs about 1% of $100.
  const sellFill = page.getByRole("region", { name: "Order filled" });
  await expect(sellFill.getByText("New cash balance").locator("..")).toContainText(
    /\$(9,9\d\d|10,0\d\d)\.\d{2}/,
  );
  await page.getByRole("button", { name: "New order" }).click();
  await expect(page.getByText("You hold 0 BTC")).toBeVisible();

  // (6) Unknown coin goes back to Markets (client-side redirect, so wait for it).
  await page.goto("/trade/NOPE");
  await expect(page).toHaveURL((url) => url.pathname === "/");
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
});
