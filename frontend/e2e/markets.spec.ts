// Phase 3 happy path. Needs the full compose stack with PRICE_SOURCE=fake (CI sets it).
// Never run it against a stack whose email backend is resend.
import { expect, test, type Page } from "@playwright/test";
import { portfolioId, signInNewUser } from "./helpers.js";
import { stocks as stockCatalogue } from "./stock-fixtures.js";

test("a signed-in user sees live prices for the curated coins", async ({ page, browser }) => {
  test.setTimeout(90_000);

  await page.route("**/api/v1/stocks", (route) =>
    route.fulfill({ json: stockCatalogue({ state: "unavailable" }) }),
  );
  await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await expect(page).toHaveURL((url) => url.pathname === "/");
  await expect(page.getByRole("button", { name: "US stocks", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByRole("list", { name: "US stocks" }).getByRole("button")).toHaveCount(20);

  await page.getByRole("button", { name: "Crypto", exact: true }).click();
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
  const back = page.getByRole("button", { name: "Back to results" });
  if (await back.isVisible()) await back.click();

  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const stocks = page.getByRole("list", { name: "US stocks", exact: true });
  await expect(stocks.getByRole("button")).toHaveCount(20);
  await stocks.getByRole("button", { name: /AAPL/ }).click();
  const apple = page.locator('section[aria-labelledby="market-asset"]');
  await expect(apple.getByRole("link", { name: "View details AAPL" })).toBeVisible();
  await expect(apple.getByText("Price unavailable")).toHaveCount(0);
  await expect(apple.getByRole("note", { name: "Stock price source" })).toHaveCount(0);

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

async function expectSingleRowHeader(page: Page) {
  const header = page.getByRole("banner");
  const boxes = await Promise.all([
    header.getByText("Birja", { exact: true }).boundingBox(),
    ...["Markets", "Portfolios", "History"].map((name) =>
      header.getByRole("link", { name, exact: true }).boundingBox(),
    ),
    header.getByRole("button", { name: "Sign out" }).boundingBox(),
  ]);
  const door = boxes.at(-1)!;
  expect(door.width).toBeGreaterThanOrEqual(44);
  expect(door.height).toBeGreaterThanOrEqual(44);
  const rowCenter = door.y + door.height / 2;
  for (const box of boxes) {
    expect(Math.abs(box!.y + box!.height / 2 - rowCenter)).toBeLessThanOrEqual(1);
  }
  const overflow = await page.evaluate<number>(
    "document.documentElement.scrollWidth - document.documentElement.clientWidth",
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

test("Markets workspace keeps a single header row and puts prices beside or below the list", async ({
  page,
}, testInfo) => {
  const now = "2026-11-27T16:00:00Z";
  await page.clock.setFixedTime(new Date(now));
  await page.setViewportSize({ width: 1440, height: 1000 });
  const opened = stockCatalogue({
    now,
    open: "2026-11-27T14:30:00Z",
    close: "2026-11-27T18:00:00Z",
  });
  Object.assign(opened.items[0]!, {
    status: {
      state: "normal",
      observed_at: now,
      valid_until: "2026-11-27T16:00:30Z",
    },
    status_reason: "normal",
    execution_enabled: true,
    execution_reason: "available",
  });
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: opened }));
  await signInNewUser(page);
  const results = page.getByRole("region", { name: "Find an asset" });
  const detail = page.getByRole("region", { name: /^Apple Inc/ });
  await expect(results.getByRole("list", { name: "US stocks" }).getByRole("button")).toHaveCount(
    20,
  );
  await expect(detail.getByText("$101.00", { exact: true })).toBeVisible();
  await expect(detail.getByText("Market open", { exact: true })).toBeVisible();
  const owned = await portfolioId(page);
  const picker = page.getByRole("combobox", { name: "Trading portfolio" });
  await expect(picker).toHaveCount(1);
  await picker.selectOption(owned);
  await expect(detail.getByRole("link", { name: "Trade AAPL" })).toHaveAttribute(
    "href",
    `/portfolios/${owned}/trade/stocks/AAPL`,
  );

  for (const width of [1440, 768, 640, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expectSingleRowHeader(page);
    const listBox = (await results.boundingBox())!;
    const detailBox = (await detail.boundingBox())!;
    if (width >= 768) {
      expect(detailBox.x).toBeGreaterThan(listBox.x + listBox.width);
      expect(Math.abs(detailBox.y - listBox.y)).toBeLessThanOrEqual(1);
    } else {
      expect(detailBox.y).toBeGreaterThan(listBox.y + listBox.height);
    }
    if (width === 1440) {
      await page.screenshot({
        path: testInfo.outputPath("markets-desktop-open.png"),
        fullPage: true,
      });
    }
  }
});

for (const fixture of [
  {
    name: "holiday",
    now: "2026-11-26T18:00:00.000Z",
    mark: "2026-11-25T20:59:00.000Z",
    nextOpen: "2026-11-27T14:30:00.000Z",
    countdown: "Opens in 20 hr 30 min",
  },
  {
    name: "early close",
    now: "2026-11-27T18:00:00.000Z",
    mark: "2026-11-27T17:57:30.000Z",
    nextOpen: "2026-11-30T14:30:00.000Z",
    countdown: "Opens in 68 hr 30 min",
  },
]) {
  test(`Markets displays a verified ${fixture.name} reopening and last price`, async ({
    page,
  }, testInfo) => {
    const { now, mark, nextOpen, countdown } = fixture;
    await page.clock.setFixedTime(new Date(now));
    await page.setViewportSize({ width: 1440, height: 1000 });
    const age = (Date.parse(now) - Date.parse(mark)) / 1000;
    const body = stockCatalogue({ now, age });
    for (const item of body.items) {
      Object.assign(item.session, {
        state: "closed",
        opens_at: null,
        closes_at: null,
        next_open_at: nextOpen,
      });
      Object.assign(item, {
        session_reason: "closed",
        execution_reason: "market_closed",
        quote_reason: "stale",
      });
      item.quote!.collected_at = new Date(Date.parse(mark) + 1000).toISOString();
    }
    await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
    await signInNewUser(page);

    const detail = page.getByRole("region", { name: /^Apple Inc/ });
    await expect(detail.getByText("Market closed", { exact: true })).toBeVisible();
    await expect(detail.getByText(countdown)).toHaveAttribute("datetime", nextOpen);
    const price = detail.getByText(/^\$101\.00/);
    await expect(price).toBeVisible();
    await expect(price.locator("time")).toHaveAttribute("datetime", mark);
    await expect(detail.getByRole("link", { name: "View details AAPL" })).toBeVisible();
    await expect(detail.getByRole("link", { name: "Trade AAPL" })).toHaveCount(0);
    if (fixture.name === "holiday") {
      await page.screenshot({
        path: testInfo.outputPath("markets-desktop-closed.png"),
        fullPage: true,
      });
    }
  });
}
