import { expect, test, type Page } from "@playwright/test";
import { signInNewUser } from "./helpers.js";
import { stocks } from "./stock-fixtures.js";

const section = (page: Page) => page.getByRole("region", { name: "Find an asset" });
const records = (page: Page) => page.getByRole("list", { name: "US stocks" }).getByRole("listitem");
const selected = (page: Page) => page.locator('section[aria-labelledby="market-asset"]');
const midpoint = "$101.00";
async function refocus(page: Page) {
  // Exercise the real TanStack focus/refetch path without reloading its cache.
  await page.evaluate('window.dispatchEvent(new Event("visibilitychange"))');
  await page.evaluate('window.dispatchEvent(new Event("focus"))');
}

test.describe("market reopening", () => {
  test.use({ timezoneId: "America/Los_Angeles" });

  for (const retainedQuote of [true, false]) {
    test(`verified closure shows a concise countdown ${retainedQuote ? "with the last price" : "when IEX prices are missing"}`, async ({
      page,
    }) => {
      await page.clock.install();
      const now = await page.evaluate(() => Date.now());
      const nextOpen = new Date(now + 119.75 * 60_000).toISOString();
      const body = stocks({
        state: retainedQuote ? "approved" : "unavailable",
        now: new Date(now).toISOString(),
        open: new Date(now - 60_000).toISOString(),
        close: new Date(now + 3_600_000).toISOString(),
      });
      const first = body.items[0]!;
      Object.assign(first, { session_reason: "closed" });
      Object.assign(first.session, {
        state: "closed",
        opens_at: null,
        closes_at: null,
        next_open_at: nextOpen,
      });
      if (retainedQuote) {
        first.quote!.event_at = new Date(now - 300_000).toISOString();
        first.quote!.age_seconds = 300;
        first.quote_reason = "stale";
      }
      await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
      await signInNewUser(page);
      await page.getByRole("button", { name: "US stocks", exact: true }).click();

      const detail = selected(page);
      await expect(detail.getByRole("status")).toHaveText("Market closed");
      const opening = detail.locator(`time[datetime="${nextOpen}"]`);
      await expect(opening).toHaveText("Opens in 2 hr");
      await expect(detail.getByText("Price unavailable")).toHaveCount(0);
      await expect(detail.getByRole("note", { name: "Stock price source" })).toHaveCount(0);
      await expect(detail.getByText(/Last verified IEX midpoint/)).toHaveCount(0);
      if (retainedQuote) {
        await expect(detail.getByText(midpoint, { exact: true })).toBeVisible();
        await expect(section(page).getByText(body.attribution.required_text)).toBeVisible();
      } else {
        await expect(detail.getByText(midpoint, { exact: true })).toHaveCount(0);
      }
      await expect(detail.getByRole("link", { name: "View details AAPL" })).toBeVisible();
      await page.clock.fastForward(60_000);
      await expect(opening).toHaveText("Opens in 1 hr 59 min");

      await records(page).nth(1).getByRole("button").click();
      await expect(detail.getByText("Market closed")).toHaveCount(0);
      await expect(opening).toHaveCount(0);
    });
  }
});

test("independent stock HTTP errors can retry while crypto remains usable", async ({ page }) => {
  await page.clock.install();
  let failed = false;
  let recovered = false;
  await page.route("**/api/v1/stocks", (route) =>
    failed
      ? route.fulfill({ status: 503, json: { detail: "unavailable" } })
      : route.fulfill({
          json: stocks({ now: recovered ? "2026-11-10T15:00:31Z" : "2026-11-10T15:00:00Z" }),
        }),
  );
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page)).toHaveCount(20);
  failed = true;
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(section(page).getByRole("status")).toContainText("Couldn’t refresh");
  await expect(records(page).first()).toContainText(midpoint);
  const retry = section(page).getByRole("button", { name: "Try again" });
  await expect(retry).toBeVisible();
  await retry.focus();
  await expect(retry).toBeFocused();
  failed = false;
  recovered = true;
  await page.keyboard.press("Enter");
  await expect(section(page).getByText(/Couldn’t refresh/)).toHaveCount(0);
  await expect(records(page)).toHaveCount(20);
  await page.getByRole("button", { name: "Crypto", exact: true }).click();
  await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
  await expect(page.getByRole("link", { name: "Trade BTC" })).toBeVisible();
});

for (const width of [320, 375, 768, 1280])
  test(`read-only catalogue at ${width}px with one accessible representation`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: stocks() }));
    await signInNewUser(page);
    await page.getByRole("button", { name: "US stocks", exact: true }).click();
    await expect(records(page)).toHaveCount(20);
    await expect(page.getByText("Stock market details", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("table", { name: "US stocks" })).toHaveCount(0);
    await expect(records(page).first()).toContainText(midpoint);
    await records(page).first().getByRole("button").click();
    await expect(selected(page)).toContainText("NASDAQ");
    await expect(selected(page).getByRole("link", { name: "View details AAPL" })).toBeVisible();
    await expect(selected(page).getByRole("link", { name: /^Trade / })).toHaveCount(0);
    await expect(selected(page).getByRole("note")).toContainText("IEX prices");
    await expect(selected(page).getByRole("note")).toContainText("Fixture provider attribution");
    await expect(selected(page).locator("time")).toHaveAttribute(
      "datetime",
      "2026-11-10T14:59:50.000Z",
    );
    if (width < 768) await page.getByRole("button", { name: "All assets" }).click();
    expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`stocks-${width}.png`), fullPage: true });
    // Half the effective viewport width is the browser-zoom reflow equivalent.
    if (width === 1280) {
      await page.setViewportSize({ width: 640, height: 450 });
      await page.getByRole("button", { name: "All assets" }).click();
      await expect(section(page).getByRole("listitem")).toHaveCount(20);
      expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    }
    await page.getByRole("button", { name: "Crypto", exact: true }).click();
    await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
    if (width < 768 || width === 1280) {
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

test("denied, admitted and revoked generations retain identities and purge provider material", async ({
  page,
}) => {
  await page.clock.install();
  let body = stocks({ state: "unavailable" });
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page)).toHaveCount(20);
  await expect(section(page)).toContainText("Stock prices and trading are currently unavailable");
  await expect(section(page).getByText(midpoint)).toHaveCount(0);
  body = stocks({ generation: 2, now: "2026-11-10T15:00:31Z" });
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(records(page).first()).toContainText(midpoint);
  body = stocks({ state: "unavailable", generation: 3, now: "2026-11-10T15:01:02Z" });
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(section(page)).toContainText("Stock prices and trading are currently unavailable");
  await expect(section(page).getByText(midpoint)).toHaveCount(0);
  await expect(selected(page).locator("time")).toHaveCount(0);
  await expect(records(page)).toHaveCount(20);
});

test("local admission expiry and a late expired response cannot reintroduce quote values", async ({
  page,
}) => {
  await page.clock.install();
  let calls = 0;
  let expiredResponse = false;
  await page.route("**/api/v1/stocks", async (route) => {
    calls++;
    if (expiredResponse) await new Promise((resolve) => setTimeout(resolve, 100));
    await route.fulfill({ json: stocks({ lifetime: expiredResponse ? -1 : 5 }) });
  });
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page).first()).toContainText(midpoint);
  const initialCalls = calls;
  expiredResponse = true;
  await page.clock.fastForward(6000);
  await page.clock.runFor(100);
  await expect(section(page)).toContainText("Stock prices and trading are currently unavailable");
  await page.clock.fastForward(30_001);
  await refocus(page);
  await expect.poll(() => calls).toBeGreaterThan(initialCalls);
  await expect(section(page).getByText(midpoint)).toHaveCount(0);
  await expect(records(page)).toHaveCount(20);
});

test("source 119.999 to120 stays nonexecutable and does not announce each second", async ({
  page,
}) => {
  await page.route("**/api/v1/stocks", (route) =>
    route.fulfill({ json: stocks({ age: 119.999 }) }),
  );
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page).first()).not.toContainText(midpoint); // full RTT cannot extend source age
  await expect(selected(page).getByRole("status")).toContainText("This quote is out of date");
  await expect(selected(page).getByRole("link", { name: /^Trade / })).toHaveCount(0);
  await page.clock.install();
  const before = await selected(page).getByRole("status").textContent();
  await page.clock.fastForward(1000);
  expect(await selected(page).getByRole("status").textContent()).toBe(before);
});

test("source age crossing120 changes the contextual announcement only at the boundary", async ({
  page,
}) => {
  await page.clock.install();
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: stocks({ age: 119 }) }));
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page).first()).toContainText(midpoint);
  const recent = await selected(page).getByRole("status").textContent();
  await page.clock.runFor(1000);
  await expect(records(page).first()).not.toContainText(midpoint);
  await expect(selected(page).getByRole("status")).toContainText("This quote is out of date");
  const stale = await selected(page).getByRole("status").textContent();
  expect(stale).not.toBe(recent);
  await page.clock.runFor(1000);
  expect(await selected(page).getByRole("status").textContent()).toBe(stale);
});

test("missing, previous-session, early-close, DST and unknown calendars remain separate from status", async ({
  page,
}) => {
  await page.clock.install();
  const body = stocks({
    now: "2026-11-27T17:59:59Z",
    close: "2026-11-27T18:00:00Z",
    open: "2026-11-27T14:30:00Z",
  });
  body.items[0].quote = null;
  body.items[0].quote_reason = "missing";
  body.items[0].valuation_reason = "quote_unavailable";
  body.items[1].quote_reason = "session_unavailable";
  body.items[1].quote!.event_at = "2026-11-25T20:59:00Z";
  body.items[1].quote!.age_seconds = Math.floor(
    (Date.parse(body.server_now) - Date.parse(body.items[1].quote!.event_at)) / 1000,
  );
  body.items[2].session = {
    ...body.items[2].session,
    state: "unknown",
    opens_at: null,
    closes_at: null,
    valid_until: null,
  };
  body.items[2].session_reason = "unknown";
  body.items[2].quote = null;
  body.items[2].quote_reason = "missing";
  body.items[2].valuation_reason = "quote_unavailable";
  // Winter NY session14:30Z and summer13:30Z are explicit server-provided bounds.
  body.items[3].session.opens_at = "2026-07-06T13:30:00Z";
  body.items[3].session.closes_at = "2026-07-06T20:00:00Z";
  body.items[3].session.state = "closed";
  body.items[3].session_reason = "closed";
  body.items[3].quote_reason = "session_unavailable";
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: body }));
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(records(page)).toHaveCount(20);
  await expect(selected(page).getByRole("status")).toContainText(
    "Waiting for a verified IEX quote",
  );
  await expect(records(page).nth(1)).not.toContainText(midpoint);
  await records(page).nth(2).getByRole("button").click();
  await expect(selected(page).getByRole("status")).toContainText("Session unavailable");
  await records(page).nth(3).getByRole("button").click();
  await expect(selected(page).getByRole("status")).toContainText("Market closed");
  await records(page).nth(4).getByRole("button").click();
  await expect(selected(page).locator("time")).toHaveAttribute(
    "datetime",
    body.items[4].quote!.event_at,
  );
  await page.clock.fastForward(2000);
  await page.clock.runFor(100);
  await expect(selected(page).getByRole("status")).toContainText("Market closed");
  await expect(selected(page).getByRole("link", { name: "View details GOOGL" })).toBeVisible();
});
