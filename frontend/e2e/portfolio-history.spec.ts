// Run only in ephemeral fake-price / console-email CI, never real-email dev/prod.
import { expect, test, type Page } from "@playwright/test";
import { formatQuantity, formatUnitPrice, formatUsd } from "../src/lib/money.js";
import { signInNewUser } from "./helpers.js";

// Wire fields consumed by this Node test; browser API modules use Vite resolution.
type Fill = Record<
  "quantity" | "exec_price" | "fee" | "cash_delta" | "cash_after" | "created_at",
  string
> & { trade_id: number; side: "buy" | "sell" };
type Portfolio = Record<"cash" | "total_value" | "total_pl" | "total_pl_percent", string> & {
  prices_as_of: string | null;
  holdings: Array<
    Record<
      | "quantity"
      | "cost_basis"
      | "average_cost"
      | "mid"
      | "current_value"
      | "unrealized_pl"
      | "unrealized_pl_percent"
      | "allocation_percent"
      | "as_of",
      string
    >
  >;
};
type HistoryPage = {
  items: Array<
    Record<"id" | "quantity" | "exec_price" | "fee" | "total" | "created_at" | "side", string>
  >;
};

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
        await page.keyboard.press("Tab");
        await scroll.focus();
        await expect(scroll).toBeFocused();
        await expect(scroll).toHaveCSS("outline-width", "2px");
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
        await page.keyboard.press("Tab");
        await last.focus();
        await last.scrollIntoViewIfNeeded();
        await expect(last).toBeFocused();
        await expect(last).toHaveCSS("outline-width", "2px");
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
  const cashOnlyMessage = page.getByText("No market prices needed", { exact: true });
  await expect(cashOnlyMessage).toHaveCount(1);
  await expect(cashOnlyMessage).toBeVisible();
});

async function confirmFill(page: Page, side: "buy" | "sell"): Promise<Fill> {
  for (let attempt = 0; attempt < 3; attempt++) {
    const response = page.waitForResponse(
      (r) => r.url().endsWith("/api/v1/trades") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: `Confirm ${side}` }).click();
    const result = await response;
    if (result.ok()) {
      const fill = (await result.json()) as Fill;
      await expect(page.getByRole("heading", { name: "Order filled" })).toBeVisible();
      return fill;
    }
    expect(((await result.json()) as { detail: { code: string } }).detail.code).toBe(
      "price_changed",
    );
    await expect(page.getByText("Price updated. Please review again.")).toBeVisible();
  }
  throw new Error(`No ${side} fill after three price-change confirmations`);
}

test("buy → portfolio → history → whole-position sell preserves actual server values", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await signInNewUser(page);
  await page.getByRole("link", { name: "Portfolio", exact: true }).click();
  await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText("$10,000.00");
  await page.getByRole("link", { name: "Markets", exact: true }).click();
  await page.getByRole("link", { name: "Trade BTC", exact: true }).click();
  await page.getByLabel("Amount").fill("100");
  const buy = await confirmFill(page, "buy");
  expect(buy.cash_delta).toMatch(/^-100\.0+$/);
  expect(buy.cash_after).toMatch(/^9900\.0+$/);

  async function openPortfolio() {
    const response = page.waitForResponse((r) => r.url().endsWith("/api/v1/portfolio") && r.ok());
    await page.getByRole("link", { name: "Portfolio", exact: true }).click();
    const data = (await (await response).json()) as Portfolio;
    await expect(page.getByRole("heading", { name: "Portfolio", level: 1 })).toBeFocused();
    await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText(
      formatUsd(data.cash),
    );
    await expect(
      page.getByRole("region", { name: "Total portfolio value", exact: true }),
    ).toContainText(formatUsd(data.total_value!));
    const result = page.getByRole("region", { name: "Total portfolio value", exact: true });
    await expect(result).toContainText(formatUsd(data.total_pl!.replace(/^-/, "")));
    await expect(result).toContainText(`${data.total_pl_percent!.replace(/^-/, "")}%`);
    return data;
  }
  const portfolio = await openPortfolio();
  expect(portfolio.holdings).toHaveLength(1);
  const held = portfolio.holdings[0]!;
  expect(formatQuantity(held.quantity)).toBe(formatQuantity(buy.quantity));
  expect(formatUsd(held.cost_basis)).toBe("$100.00");
  expect(portfolio.prices_as_of).toBe(held.as_of);
  const row = page.getByRole("table", { name: "Holdings", exact: true }).getByRole("row").nth(1);
  for (const value of [
    formatQuantity(held.quantity),
    formatUnitPrice(held.average_cost),
    formatUnitPrice(held.mid!),
    formatUsd(held.current_value!),
    formatUsd(held.unrealized_pl!.replace(/^-/, "")),
    `${held.unrealized_pl_percent!.replace(/^-/, "")}%`,
    `${held.allocation_percent}%`,
  ]) {
    await expect(row).toContainText(value);
  }
  await expect(row.locator("time")).toHaveAttribute("datetime", held.as_of!);
  const refresh = page.getByRole("button", { name: "Refresh portfolio" });
  await refresh.click();
  await expect(refresh).toBeEnabled();
  await expect(refresh).toBeFocused();

  async function openHistory(expected: Fill[]) {
    const response = page.waitForResponse(
      (r) => /\/api\/v1\/trades(?:\?|$)/.test(r.url()) && r.request().method() === "GET" && r.ok(),
    );
    await page.getByRole("link", { name: "History", exact: true }).click();
    const data = (await (await response).json()) as HistoryPage;
    expect(data.items).toHaveLength(expected.length);
    expect(data.items.map((item) => item.id)).toEqual(
      expected.map((fill) => String(fill.trade_id)),
    );
    const rows = page.getByRole("table", { name: "Trade history", exact: true }).getByRole("row");
    for (const [index, fill] of expected.entries()) {
      const item = data.items[index]!;
      expect(item).toMatchObject({
        quantity: fill.quantity,
        exec_price: fill.exec_price,
        fee: fill.fee,
        total: fill.cash_delta,
        created_at: fill.created_at,
        side: fill.side,
      });
      const row = rows.nth(index + 1);
      for (const value of [
        fill.side === "buy" ? "Buy" : "Sell",
        formatQuantity(fill.quantity),
        formatUnitPrice(fill.exec_price),
        formatUsd(fill.fee),
        `${fill.cash_delta.startsWith("-") ? "−" : "+"}${formatUsd(fill.cash_delta.replace(/^-/, ""))}`,
      ])
        await expect(row).toContainText(value);
      await expect(row.locator("time")).toHaveAttribute("datetime", fill.created_at);
    }
    await expect(page.getByText("All trades loaded.", { exact: true })).toBeVisible();
  }
  await openHistory([buy]);
  await page.getByRole("link", { name: "Markets", exact: true }).click();
  await page.getByRole("link", { name: "Trade BTC", exact: true }).click();
  await page.getByRole("radio", { name: "Sell", exact: true }).click();
  await page.getByLabel("Quantity").fill(held.quantity);
  const sell = await confirmFill(page, "sell");
  expect(formatQuantity(sell.quantity)).toBe(formatQuantity(held.quantity));
  const liquidated = await openPortfolio();
  expect(liquidated.holdings).toEqual([]);
  expect(formatUsd(liquidated.cash)).toBe(formatUsd(sell.cash_after));
  expect(liquidated.total_value).toBe(liquidated.cash);
  expect(liquidated.prices_as_of).toBeNull();
  await expect(page.getByText("No holdings yet", { exact: true })).toBeVisible();
  await expect(page.getByText("No market prices needed", { exact: true })).toBeVisible();
  await openHistory([sell, buy]);
  await page.reload();
  await expect(page.getByRole("heading", { name: "History", level: 1 })).toBeFocused();
  await page.getByRole("link", { name: "Account", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign out", exact: true })).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("heading", { name: "History", level: 1 })).toBeFocused();
});
