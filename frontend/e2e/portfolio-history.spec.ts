// Run only in ephemeral fake-price / console-email CI, never real-email dev/prod.
import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

for (const width of [375, 768, 1024, 1440]) {
  test(`portfolio and history remain readable and reachable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await signInNewUser(page);
    const timestamp = "2026-10-29T23:59:59.123456Z";
    // Synthetic boundary data tests presentation without creating impossible real balances.
    await page.route("**/api/v1/portfolio", (route) =>
      route.fulfill({
        json: {
          cash: "999999999999.99",
          starting_cash: "10000.00",
          total_value: "1999999999999.98",
          total_pl: "1999999989999.98",
          total_pl_percent: "19999999899.99",
          cash_allocation_percent: "50.00",
          valuation_complete: true,
          valued_at: timestamp,
          prices_as_of: timestamp,
          fresh_seconds: 120,
          stale_seconds: 300,
          holdings: [
            {
              symbol: "BTC",
              name: "Bitcoin",
              is_active: true,
              quantity: "123456789012.12345678",
              cost_basis: "100.00",
              average_cost: "0.00000001",
              mid: "8.10",
              current_value: "999999999999.99",
              unrealized_pl: "999999999899.99",
              unrealized_pl_percent: "999999999899.99",
              allocation_percent: "50.00",
              as_of: timestamp,
              age_seconds: 10,
              status: "fresh",
            },
          ],
        },
      }),
    );
    await page.route("**/api/v1/trades", (route) =>
      route.fulfill({
        json: {
          items: [
            {
              id: "9007199254740993",
              created_at: timestamp,
              symbol: "BTC",
              name: "Bitcoin",
              side: "buy",
              quantity: "123456789012.12345678",
              exec_price: "999999999999.99",
              fee: "100.25",
              total: "-999999999999.99",
            },
          ],
          next_cursor: null,
        },
      }),
    );
    const nav = page.getByRole("navigation", { name: "Main" });
    await expect(nav).toHaveCount(1);
    await expect(nav.getByRole("link")).toHaveCount(3);
    await expect(nav.getByRole("link", { name: "Account" })).toHaveCount(0);
    for (const name of ["Portfolio", "History"]) {
      await nav.getByRole("link", { name, exact: true }).click();
      await expect(page.getByRole("heading", { name, level: 1 })).toBeFocused();
      await expect(nav.getByRole("link", { name, exact: true })).toHaveAttribute(
        "aria-current",
        "page",
      );
      const label = name === "Portfolio" ? "Holdings" : "Trade history";
      const records = page.getByRole(width < 768 ? "list" : "table", { name: label, exact: true });
      await expect(records).toBeVisible();
      await expect(
        page.getByRole(width < 768 ? "table" : "list", { name: label, exact: true }),
      ).toHaveCount(0);
      const fields =
        name === "Portfolio"
          ? [
              "Quantity",
              "Average cost",
              "Mid price",
              "Current value",
              "Unrealized P/L",
              "Allocation",
              "Price updated",
            ]
          : [
              "Date/time",
              "Coin",
              "Side",
              "Quantity",
              "Execution price",
              "Fee",
              "Total cash change",
            ];
      for (const field of fields)
        await expect(records.getByText(field, { exact: true })).toBeVisible();
      await expect(records.locator("time")).toHaveAttribute("datetime", timestamp);
      await expect
        .poll(() =>
          page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth"),
        )
        .toBe(true);
      if (width >= 768) {
        const scroll = page.getByRole("region", {
          name:
            name === "Portfolio"
              ? "Holdings table, scroll to see all columns"
              : "Trade history table",
          exact: true,
        });
        await scroll.focus();
        await expect(scroll).toBeFocused();
        const overflows = await scroll.evaluate((node) => node.scrollWidth > node.clientWidth);
        if (overflows) {
          await page.keyboard.press("ArrowRight");
          await expect.poll(() => scroll.evaluate((node) => node.scrollLeft)).toBeGreaterThan(0);
        }
      } else {
        await expect(nav).toHaveCSS("position", "fixed");
        const last =
          name === "Portfolio"
            ? records.getByRole("link", { name: "Trade BTC" })
            : page.getByText("All trades loaded.", { exact: true });
        await last.focus();
        await last.scrollIntoViewIfNeeded();
        await expect(last).toBeFocused();
        const bottom = await last.boundingBox();
        const tabs = await nav.boundingBox();
        expect(bottom!.y + bottom!.height).toBeLessThanOrEqual(tabs!.y);
      }
    }
    // Browser-equivalent enlarged text; subjective 200% browser zoom remains 05-08.
    await page.addStyleTag({ content: "html { font-size: 200%; }" });
    await expect(page.getByRole("heading", { name: "History", level: 1 })).toBeVisible();
    await expect
      .poll(() => page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth"))
      .toBe(true);
  });
}

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
