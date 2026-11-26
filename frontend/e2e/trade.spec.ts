// Phase 4 happy path. Needs the full compose stack with PRICE_SOURCE=fake (CI sets it).
// Never run it against a stack whose email backend is resend: it creates accounts and trades.
import { expect, test, type Page } from "@playwright/test";
import { formatUsd } from "../src/lib/money.js";
import { portfolioApi, portfolioId, signInNewUser } from "./helpers.js";
import {
  capturePhase25,
  testPhase25Reflow,
  verifyOwnedReceipt,
  type TradeReceipt,
} from "./phase25-review-capture.js";

// Fake prices move on each minute boundary, so a legitimate price_changed can happen between
// preview and confirm (TRADE-05). Confirm again, bounded to 3 attempts.
async function confirmUntilFilled(
  page: Page,
  button: "Confirm buy" | "Confirm sell",
): Promise<TradeReceipt> {
  const filled = page.getByRole("heading", { name: "Order filled" });
  const changed = page.getByText("Price updated. Please review again.");
  const endpoint = await portfolioApi(page, "/trades");
  for (let attempt = 0; attempt < 3; attempt++) {
    const reply = page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === endpoint && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: button }).click();
    const result = await reply;
    await expect(filled.or(changed)).toBeVisible();
    if (result.status() === 201) {
      await expect(filled).toBeFocused();
      return result.json();
    }
    expect(result.status()).toBe(409);
    expect((await result.json()).detail.code).toBe("price_changed");
  }
  throw new Error(`${button} did not fill after 3 attempts`);
}

test("a signed-in user buys $100 of BTC and sells the whole position", async ({ page }) => {
  test.setTimeout(120_000);

  // (1) Markets row -> trade page.
  await signInNewUser(page);
  const id = await portfolioId(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await page.getByRole("button", { name: "Crypto", exact: true }).click();
  await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
  await page.getByRole("link", { name: "Trade BTC" }).click();
  await expect(page).toHaveURL((url) => url.pathname === `/portfolios/${id}/trade/BTC`);
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
  const bought = await confirmUntilFilled(page, "Confirm buy");
  const fill = page.getByRole("region", { name: "Order filled" });
  await expect(fill.getByText("New cash balance").locator("..")).toContainText("$9,900.00");
  await expect(fill.getByText("Fee", { exact: true }).locator("..")).toContainText("$0.25");
  await verifyOwnedReceipt(page, bought, "crypto");

  // (4) Sell the whole position by quantity.
  await page.getByRole("button", { name: "Trade again" }).click();
  await page.getByRole("radio", { name: "Sell" }).click();
  const hold = page.getByText(/You hold ([\d.]+) BTC/);
  await expect(hold).toBeVisible();
  const held = /You hold ([\d.]+) BTC/.exec((await hold.textContent()) ?? "")?.[1];
  expect(held).toBeTruthy();
  expect(Number(held)).toBeGreaterThan(0);
  await page.getByLabel("Quantity").fill(held as string);
  const sellPreview = page.getByRole("region", { name: "Preview" });
  await expect(sellPreview.getByText("Total cash change").locator("..")).toContainText(/\+?\$\d/);
  const sold = await confirmUntilFilled(page, "Confirm sell");

  // (5) Round trip costs about 1% of $100.
  const sellFill = page.getByRole("region", { name: "Order filled" });
  await expect(sellFill.getByText("New cash balance").locator("..")).toContainText(
    /\$(9,9\d\d|10,0\d\d)\.\d{2}/,
  );
  await verifyOwnedReceipt(page, sold, "crypto");
  await page.getByRole("button", { name: "Trade again" }).click();
  await expect(page.getByText("You hold 0 BTC")).toBeVisible();

  // (6) Unknown coin goes back to Markets (client-side redirect, so wait for it).
  await page.goto("/trade/NOPE");
  await expect(page).toHaveURL((url) => url.pathname === "/");
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
});

test("Phase 25 crypto draft matches the reference and a quantity fill reconciles with History", async ({
  page,
}, info) => {
  test.setTimeout(90_000);
  await signInNewUser(page);
  const id = await portfolioId(page);
  await page.goto(`/portfolios/${id}/trade/BTC`);
  const chooser = page.getByRole("combobox", { name: "Trading portfolio" });
  await expect(page.getByRole("combobox")).toHaveCount(1);
  await expect(chooser).toHaveValue(id);
  const portfolioName = await chooser.locator("option:checked").innerText();
  const ticket = page.getByRole("region", { name: "Trade ticket", exact: true });
  const preview = page.getByRole("region", { name: "Preview", exact: true });
  await expect(ticket).toContainText("Cash available $10,000.00");
  await expect(ticket).toContainText("You hold 0 BTC");
  await expect(ticket).not.toContainText(portfolioName);
  await expect(preview).not.toContainText(portfolioName);
  await capturePhase25(page, info, "trade");
  await testPhase25Reflow(page, chooser, ticket.getByRole("radio", { name: "Buy", exact: true }));

  const quantityMode = ticket.getByRole("button", { name: "Quantity", exact: true });
  await quantityMode.click();
  await expect(quantityMode).toHaveAttribute("aria-pressed", "true");
  await ticket.getByLabel("Quantity", { exact: true }).fill("0.001");
  await expect(page.getByRole("region", { name: "Preview", exact: true })).toContainText(
    "0.001 BTC",
  );
  const bought = await confirmUntilFilled(page, "Confirm buy");
  expect(bought).toMatchObject({
    portfolio_id: id,
    input_kind: "quantity",
    symbol: "BTC",
    side: "buy",
  });
  const receipt = page.getByRole("region", { name: "Order filled", exact: true });
  await expect(receipt.getByText("New cash balance").locator("..")).toContainText(
    formatUsd(bought.cash_after),
  );
  await expect(receipt).not.toContainText(portfolioName);
  await verifyOwnedReceipt(page, bought, "crypto");
});
