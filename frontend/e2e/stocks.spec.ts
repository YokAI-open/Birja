import { expect, test, type Page } from "@playwright/test";
import { signInNewUser } from "./helpers.js";
import { stocks } from "./stock-fixtures.js";

const section = (page: Page) => page.getByRole("region", { name: "US stocks · 20" });
const records = (page: Page) =>
  page.viewportSize()!.width >= 1024
    ? section(page)
        .getByRole("row")
        .filter({ has: page.locator("td") })
    : section(page).getByRole("listitem");
async function refocus(page: Page) {
  // Exercise the real TanStack focus/refetch path without reloading its cache.
  await page.evaluate('window.dispatchEvent(new Event("visibilitychange"))');
  await page.evaluate('window.dispatchEvent(new Event("focus"))');
}

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
  await expect(records(page)).toHaveCount(20);
  failed = true;
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(section(page).getByRole("status")).toContainText("Couldn’t refresh stocks");
  await expect(records(page).first()).toContainText("$100.00");
  const retry = section(page).getByRole("button", { name: "Retry stock prices" });
  await expect(retry).toBeVisible();
  await retry.focus();
  await expect(retry).toBeFocused();
  failed = false;
  recovered = true;
  await page.keyboard.press("Enter");
  await expect(section(page).getByRole("status")).not.toContainText("Couldn’t refresh");
  await expect(section(page).getByRole("heading", { name: "US stocks · 20" })).toBeFocused();
  await expect(page.getByRole("link", { name: "Trade BTC" })).toBeVisible();
});

for (const width of [320, 375, 768, 1280])
  test(`read-only catalogue at ${width}px with one accessible representation`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: stocks() }));
    await signInNewUser(page);
    await expect(records(page)).toHaveCount(20);
    await expect(page.getByRole("link", { name: /^Trade / })).toHaveCount(15);
    await expect(section(page).getByRole("link")).toHaveCount(0);
    await expect(section(page).getByRole("button")).toHaveCount(0);
    await expect(section(page).getByRole("table", { name: "US stocks" })).toHaveCount(
      width >= 1024 ? 1 : 0,
    );
    await expect(section(page).getByRole("list", { name: "US stocks" })).toHaveCount(
      width < 1024 ? 1 : 0,
    );
    await expect(section(page).getByRole("note")).toContainText("IEX prices");
    await expect(section(page).getByRole("note")).toContainText("Fixture provider attribution");
    await expect(section(page).getByText(/Stock trading coming later/)).toBeVisible();
    await expect(records(page).first()).toContainText("NASDAQ");
    await expect(records(page).last()).toContainText("NYSE");
    await expect(records(page).first().locator("time").first()).toHaveAttribute(
      "datetime",
      "2026-11-10T14:59:50.000Z",
    );
    expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`stocks-${width}.png`), fullPage: true });
    // Half the effective viewport width is the browser-zoom reflow equivalent.
    if (width === 1280) {
      await page.setViewportSize({ width: 640, height: 450 });
      await expect(section(page).getByRole("listitem")).toHaveCount(20);
      expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
    }
    const trade = page.getByRole("link", { name: "Trade BTC" });
    await trade.focus();
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
  await expect(records(page)).toHaveCount(20);
  await expect(section(page).getByRole("status")).toContainText("permissions are being verified");
  await expect(section(page).getByText("$100.00")).toHaveCount(0);
  body = stocks({ generation: 2, now: "2026-11-10T15:00:31Z" });
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(records(page).first()).toContainText("$100.00");
  body = stocks({ state: "unavailable", generation: 3, now: "2026-11-10T15:01:02Z" });
  await page.clock.fastForward(30_001);
  await page.clock.runFor(100);
  await expect(section(page).getByRole("status")).toContainText("permissions are being verified");
  await expect(section(page).getByText("$100.00")).toHaveCount(0);
  await expect(section(page).locator("time")).toHaveCount(80); // session bounds are public, quote times absent
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
  await expect(records(page).first()).toContainText("$100.00");
  const initialCalls = calls;
  expiredResponse = true;
  await page.clock.fastForward(6000);
  await page.clock.runFor(100);
  await expect(section(page).getByRole("status")).toContainText("permissions are being verified");
  await page.clock.fastForward(30_001);
  await refocus(page);
  await expect.poll(() => calls).toBeGreaterThan(initialCalls);
  await expect(section(page).getByText("$100.00")).toHaveCount(0);
  await expect(records(page)).toHaveCount(20);
});

test("source 119.999 to120 stays nonexecutable and does not announce each second", async ({
  page,
}) => {
  await page.route("**/api/v1/stocks", (route) =>
    route.fulfill({ json: stocks({ age: 119.999 }) }),
  );
  await signInNewUser(page);
  await expect(records(page).first()).not.toContainText("$100.00"); // full RTT cannot extend source age
  await expect(section(page).getByRole("status")).toContainText("Out of date");
  await expect(section(page).getByRole("button")).toHaveCount(0);
  await page.clock.install();
  const before = await section(page).getByRole("status").textContent();
  await page.clock.fastForward(1000);
  expect(await section(page).getByRole("status").textContent()).toBe(before);
});

test("source age crossing120 changes the contextual announcement only at the boundary", async ({
  page,
}) => {
  await page.clock.install();
  await page.route("**/api/v1/stocks", (route) => route.fulfill({ json: stocks({ age: 119 }) }));
  await signInNewUser(page);
  await expect(records(page).first()).toContainText("Recent · 1m ago");
  const recent = await section(page).getByRole("status").textContent();
  await page.clock.runFor(1000);
  await expect(records(page).first()).not.toContainText("$100.00");
  await expect(section(page).getByRole("status")).toContainText("Out of date");
  const stale = await section(page).getByRole("status").textContent();
  expect(stale).not.toBe(recent);
  await page.clock.runFor(1000);
  expect(await section(page).getByRole("status").textContent()).toBe(stale);
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
  await expect(records(page)).toHaveCount(20);
  await expect(records(page).nth(0)).toContainText("Waiting for an IEX quote");
  await expect(records(page).nth(1)).not.toContainText("$100.00");
  await expect(records(page).nth(1)).toContainText("Valuation unavailable");
  await expect(records(page).nth(2)).toContainText("Session unavailable");
  await expect(records(page).nth(3)).toContainText("Last quote");
  await expect(records(page).nth(4)).toContainText("Market open");
  await expect(records(page).nth(4)).toContainText("America/New_York");
  await expect(records(page).nth(4)).toContainText("Stock status unverified");
  await page.clock.fastForward(2000);
  await page.clock.runFor(100);
  await expect(records(page).nth(4)).toContainText("Market closed");
  await expect(records(page).nth(4)).toContainText("Last quote");
});
