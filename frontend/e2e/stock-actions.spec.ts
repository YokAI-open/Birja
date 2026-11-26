import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";
import { stocks } from "./stock-fixtures.js";

test("retry remains available after failed refresh and permission expiry", async ({ page }) => {
  await page.clock.install();
  let fail = false;
  let failedRequests = 0;
  await page.route("**/api/v1/stocks", (route) => {
    if (fail) {
      failedRequests++;
      return route.fulfill({ status: 503, json: { detail: "unavailable" } });
    }
    return route.fulfill({ json: stocks({ lifetime: 35 }) });
  });
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const section = page.getByRole("region", { name: "Find an asset" });
  await expect(section.getByText(midpoint).first()).toBeVisible();
  fail = true;
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect.poll(() => failedRequests).toBeGreaterThan(0);
  await expect(section.getByRole("button", { name: "Try again" })).toBeVisible();
  await page.clock.fastForward(5_000);
  await page.clock.runFor(100);
  await expect(section.getByText(midpoint)).toHaveCount(0);
  await expect(section.getByRole("button", { name: "Try again" })).toBeVisible();
});

const BASE = "2026-11-10T15:00:00.000Z";
const snapshot = (seconds = 0) =>
  stocks({ now: new Date(Date.parse(BASE) + seconds * 1000).toISOString() });
const region = (page: import("@playwright/test").Page) =>
  page.getByRole("region", { name: "Find an asset" });
const records = (page: import("@playwright/test").Page) =>
  page.getByRole("list", { name: "US stocks" }).getByRole("listitem");
const selectedStock = (page: import("@playwright/test").Page) =>
  page.locator('section[aria-labelledby="market-asset"]');
const midpoint = "$101.00";
function hold(body: ReturnType<typeof stocks>, index = 0, reason = "unsupported", epoch = 2) {
  const item = body.items[index];
  item.action = {
    state: "suspended",
    reason,
    epoch,
    checked_at: body.server_now,
    valid_until: null,
  };
  item.quote = null;
  item.quote_reason = "missing";
  item.valuation_reason =
    reason === "post_split_quote_missing" ? "post_split_quote_missing" : "action_unavailable";
}
async function poll(page: import("@playwright/test").Page) {
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
}

test.use({ timezoneId: "Europe/Moscow" });

for (const width of [320, 375, 768, 1280]) {
  test(`corporate-action suspension remains readable at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const body = snapshot();
    body.items[0].company_name = "Apple Long Company Name " + "UnbrokenReferenceName".repeat(5);
    hold(body, 0, "conflicting");
    await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
    await signInNewUser(page);
    await page.getByRole("button", { name: "US stocks", exact: true }).click();
    await expect(records(page)).toHaveCount(20);
    await expect(records(page).first()).not.toContainText(midpoint);
    await expect(records(page).nth(1)).toContainText(midpoint);
    await page.getByRole("button", { name: /AAPL/ }).click();
    const selected = selectedStock(page);
    await expect(selected).toContainText("Suspended for corporate-action review.");
    await expect(selected).toContainText("has changed or conflicts and needs review");
    await expect(selected.getByText("Price unavailable")).toHaveCount(0);
    await expect(selected.getByRole("link", { name: "View details AAPL" })).toBeVisible();
    await expect(selected.getByText(/Quotes come from IEX/)).toHaveCount(0);
    const backToResults = page.getByRole("button", { name: "Back to results" });
    if (width < 768) await backToResults.click();
    await expect(region(page).getByText("IEX prices · Midpoint", { exact: false })).toBeVisible();
    await expect(
      region(page).getByText(body.attribution.required_text, { exact: true }),
    ).toBeVisible();
    expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    expect(
      await region(page)
        .getByRole("listitem")
        .evaluateAll((items) =>
          items.every(
            (item) =>
              item.scrollWidth <= item.clientWidth + 1 &&
              item.scrollHeight <= item.clientHeight + 1,
          ),
        ),
    ).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`actions-${width}.png`), fullPage: true });
    await records(page)
      .first()
      .screenshot({ path: testInfo.outputPath(`actions-${width}-first-stock.png`) });
    await page.getByRole("button", { name: "Crypto", exact: true }).click();
    await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
    if (width < 768) {
      await expect(
        page.getByRole("heading", { name: "Bitcoin", exact: true, level: 2 }),
      ).toBeFocused();
    }
    const trade = page.getByRole("link", { name: "Trade BTC" });
    await trade.focus();
    await expect(trade).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/trade\/BTC$/);
  });
}

test("global monitor loss and repeated healthy refresh cannot clear a persistent hold", async ({
  page,
}) => {
  await page.clock.install();
  let body = snapshot();
  hold(body);
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const first = records(page).first();
  const quoteStatus = selectedStock(page).locator(".market-quote").getByRole("status");
  await expect(quoteStatus).toContainText("Suspended for corporate-action review.");
  const announcement = await quoteStatus.textContent();
  await page.clock.runFor(1000);
  expect(await quoteStatus.textContent()).toBe(announcement);
  body = snapshot(31);
  hold(body, 0, "unsupported", 2);
  await poll(page);
  await expect(first).not.toContainText(midpoint);
  await expect(quoteStatus).toContainText("Suspended for corporate-action review.");
  await expect(records(page).nth(1)).toContainText(midpoint);
  body = snapshot(62);
  for (const item of body.items) {
    item.action = {
      state: "unknown",
      reason: "source_gap",
      epoch: 3,
      checked_at: body.server_now,
      valid_until: null,
    };
    item.quote = null;
    item.quote_reason = "missing";
    item.valuation_reason = "action_unavailable";
  }
  await poll(page);
  await expect(region(page).getByText(midpoint)).toHaveCount(0);
  await expect(records(page)).toHaveCount(20);
  await expect(region(page).getByRole("link", { name: /^Trade / })).toHaveCount(0);
  await expect(quoteStatus).toContainText("Corporate-action checks unavailable.");
  body = snapshot(93);
  for (const item of body.items) item.action.epoch = 4;
  hold(body, 0, "unsupported", 4);
  await poll(page);
  await expect(quoteStatus).toContainText("Suspended for corporate-action review.");
  await expect(records(page).nth(1)).toContainText(midpoint);
});

test("a post-split waiting mark recovers only through a newer compatible response", async ({
  page,
}) => {
  await page.clock.install();
  let body = snapshot();
  hold(body, 0, "post_split_quote_missing", 2);
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(selectedStock(page)).toContainText("Waiting for a post-split quote.");
  await expect(records(page).first()).not.toContainText(midpoint);
  body = snapshot(31);
  body.items[0].action.epoch = 3;
  body.items[0].quote!.bid = "103.00000000";
  body.items[0].quote!.ask = "105.00000000";
  body.items[0].quote!.mid = "104.00000000";
  await poll(page);
  await expect(records(page).first()).toContainText("$104.00");
  await expect(selectedStock(page).getByRole("link", { name: "View details AAPL" })).toBeVisible();
});

test("nearest action deadline removes prices before polling and stale replies cannot revive them", async ({
  page,
}) => {
  await page.clock.install();
  let calls = 0;
  let body = snapshot();
  // Leave initial transport/render headroom. Exact subsecond cache expiry has
  // independent fake-clock unit coverage; this browser check must expire
  // before polling without assuming a sub-500ms page bootstrap.
  body.items[0].action.valid_until = "2026-11-10T15:00:03.000Z";
  await page.route("**/api/v1/stocks", (route) => {
    calls++;
    return route.fulfill({ json: body });
  });
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page).first()).toContainText(midpoint);
  const initialCalls = calls;
  await page.clock.runFor(3000);
  await expect(records(page).first()).not.toContainText(midpoint);
  await expect(selectedStock(page)).toContainText("Corporate-action checks unavailable.");
  expect(calls).toBe(initialCalls);
  // Repeated original current snapshot cannot reanchor the elapsed cache clock.
  await poll(page);
  await expect(records(page).first()).not.toContainText(midpoint);
  body = snapshot(31);
  body.items[0].action.epoch = 2;
  const retry = region(page).getByRole("button", { name: "Try again" });
  if (await retry.count()) await retry.click();
  else await poll(page);
  await expect(records(page).first()).toContainText(midpoint);
});

test("source 119.999/120 boundary cannot retain numeric marks or source times", async ({
  page,
}) => {
  await page.clock.install();
  const body = stocks({ age: 119.999 });
  await page.route("**/api/v1/stocks", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 20));
    await route.fulfill({ json: body });
  });
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await page.clock.runFor(1);
  await expect(region(page).getByText(midpoint)).toHaveCount(0);
  await expect(records(page).first()).not.toContainText("Recent ·");
  await expect(
    selectedStock(page).locator('time[datetime="2026-11-10T14:58:00.001Z"]'),
  ).toHaveCount(0);
});

test("keyboard retry remains available after another failure and restores the stock list", async ({
  page,
}) => {
  let fail = true;
  await page.route("**/api/v1/stocks", (route) =>
    fail
      ? route.fulfill({ status: 503, json: { detail: "unavailable" } })
      : route.fulfill({ json: snapshot() }),
  );
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const retry = region(page).getByRole("button", { name: "Try again" });
  await retry.focus();
  const failedRetry = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/stocks") && response.status() === 503,
  );
  await page.keyboard.press("Enter");
  await failedRetry;
  await expect(retry).toBeEnabled();
  await retry.focus();
  await expect(retry).toBeFocused();
  fail = false;
  await page.keyboard.press("Enter");
  await expect(records(page)).toHaveCount(20);
  await expect(retry).toHaveCount(0);
});

test("200 percent reflow equivalent keeps warnings and crypto keyboard navigation readable", async ({
  browser,
}, testInfo) => {
  const context = await browser.newContext({
    baseURL: process.env.E2E_BASE_URL,
    viewport: { width: 640, height: 450 },
    deviceScaleFactor: 2,
    reducedMotion: "reduce",
    timezoneId: "Europe/Moscow",
  });
  try {
    const page = await context.newPage();
    const body = snapshot();
    hold(body, 0, "identity_change");
    await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
    await signInNewUser(page);
    await page.getByRole("button", { name: "US stocks", exact: true }).click();
    await expect(records(page)).toHaveCount(20);
    await records(page).first().getByRole("button").click();
    await expect(selectedStock(page)).toContainText(
      "This stock’s identity is changing and needs review.",
    );
    await page.getByRole("button", { name: "Back to results" }).click();
    expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    expect(await page.evaluate("devicePixelRatio")).toBe(2);
    await page.screenshot({
      path: testInfo.outputPath("actions-200pct-reflow.png"),
      fullPage: true,
    });
    // CSS zoom is distinct from the high-density reflow emulation above.
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.evaluate('document.documentElement.style.zoom = "2"');
    expect(await page.evaluate("getComputedStyle(document.documentElement).zoom")).toBe("2");
    expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    await expect(region(page).getByRole("table")).toHaveCount(0);
    await expect(records(page)).toHaveCount(20);
    expect(
      await region(page)
        .getByRole("listitem")
        .evaluateAll((items) =>
          items.every(
            (item) =>
              item.scrollWidth <= item.clientWidth + 1 &&
              item.scrollHeight <= item.clientHeight + 1,
          ),
        ),
    ).toBe(true);
    await records(page)
      .first()
      .screenshot({ path: testInfo.outputPath("actions-css-zoom-200pct-first-stock.png") });
    await page.getByRole("button", { name: "Crypto", exact: true }).click();
    await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
    const trade = page.getByRole("link", { name: "Trade BTC" });
    await trade.focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/trade\/BTC$/);
  } finally {
    await context.close();
  }
});
