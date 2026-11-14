import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { writeFile } from "node:fs/promises";
import { stockFixture } from "./stock-trade-fixtures.js";
import { signInNewUser } from "./helpers.js";
type StockFill = Record<"exec_price" | "cash_after" | "fee" | "held_after", string>;

/** Actual DOM/CSS, frozen for offline owner zoom review; no API, script or navigation. */
async function reviewSnapshot(page: Page, info: TestInfo, name: string) {
  let css = await page.evaluate<string>(String.raw`
    Array.from(document.styleSheets)
      .flatMap((sheet) => Array.from(sheet.cssRules, (rule) => rule.cssText))
      .join("\n")
  `);
  const origin = new URL(page.url()).origin;
  for (const match of Array.from(css.matchAll(/url\((["']?)([^)"']+)\1\)/g))) {
    if (match[2].startsWith("data:")) continue;
    const url = new URL(match[2], page.url());
    expect(url.origin).toBe(origin);
    expect(url.pathname).toMatch(/\.(woff2?|ttf|otf)$/);
    const response = await page.request.get(url.href);
    expect(response.ok()).toBe(true);
    css = css.replaceAll(
      match[0],
      `url("data:font/woff2;base64,${(await response.body()).toString("base64")}")`,
    );
  }
  const snapshotBuilder = String.raw`(styles) => {
    const copy = document.cloneNode(true);
    copy.querySelectorAll("script, link, style, iframe").forEach((el) => el.remove());
    const style = copy.createElement("style");
    style.textContent = styles;
    copy.head.append(style);
    copy.querySelectorAll("form").forEach((form) => {
      const block = copy.createElement("div");
      block.className = form.className;
      block.replaceChildren(...form.childNodes);
      form.replaceWith(block);
    });
    copy.querySelectorAll("a").forEach((el) => el.setAttribute("href", "#"));
    copy.querySelectorAll("button").forEach((el) => el.setAttribute("type", "button"));
    copy.querySelectorAll("input").forEach((el) => el.setAttribute("readonly", ""));
    const note = copy.createElement("p");
    note.textContent =
      "Read-only synthetic Phase 9 review snapshot. Actions do not execute. Use your browser menu to check 200% zoom.";
    note.setAttribute("style", "padding:16px;border:2px solid currentColor");
    copy.body.prepend(note);
    return "<!doctype html>\n" + copy.documentElement.outerHTML;
  }`;
  // A string expression is evaluated as-is; explicitly invoke it rather than
  // asking Playwright to serialize a returned function. CSS is a JSON argument,
  // never interpolated as executable source or passed to a shell.
  const html = await page.evaluate<string>(`(${snapshotBuilder})(${JSON.stringify(css)})`);
  expect(html).not.toContain("<script");
  expect(html).not.toContain("<form");
  expect(html).not.toMatch(/\s(?:src|href|action)=["']https?:/);
  await writeFile(info.outputPath(name + ".html"), html);
}

test.beforeEach(() => stockFixture("fresh"));
const nav = (page: Page) => page.getByRole("navigation", { name: "Main" });
async function ticket(page: Page) {
  await signInNewUser(page);
  const link = page.getByRole("link", { name: "Trade AAPL", exact: true });
  await expect(link).toBeVisible();
  await link.click();
  await expect(page.getByLabel("Whole-share quantity")).toBeVisible();
  await expect(page.getByRole("button", { name: "Buy max" })).toBeEnabled();
}
async function preview(page: Page, quantity = "2") {
  await page.getByLabel("Whole-share quantity").fill(quantity);
  const response = page.waitForResponse((r) => r.url().endsWith("/api/v1/stock-trades/quote"));
  await page.getByRole("button", { name: "Preview trade", exact: true }).click();
  expect((await response).status()).toBe(200);
  await expect(page.getByRole("button", { name: /^Confirm (buy|sell)$/ })).toBeEnabled();
  const confirm = page.getByRole("button", { name: /^Confirm (buy|sell)$/ });
  await confirm.focus();
  await confirm.scrollIntoViewIfNeeded();
  const fixed = await nav(page).evaluate("el => getComputedStyle(el).position === 'fixed'");
  if (fixed) {
    const control = await confirm.boundingBox(),
      tabs = await nav(page).boundingBox();
    expect(control!.y + control!.height).toBeLessThanOrEqual(tabs!.y);
  }
}
async function fill(page: Page): Promise<StockFill> {
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/v1/stock-trades") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: /^Confirm (buy|sell)$/ }).click();
  const r = await response;
  expect(r.status()).toBe(201);
  const result = (await r.json()) as StockFill;
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeFocused();
  return result;
}
async function noOverflow(page: Page) {
  expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
}

test("actual ask buy and bid sale preserve immutable receipt, shared cash and combined allocation", async ({
  page,
}, info) => {
  await ticket(page);
  await page.getByRole("button", { name: "Buy max", exact: true }).click();
  await expect(page.getByLabel("Whole-share quantity")).toHaveValue("98");
  expect((await page.request.get("/api/v1/portfolio")).status()).toBe(200);
  await preview(page);
  const buy = await fill(page);
  expect(buy.exec_price).toBe("102.00000000");
  expect(buy.cash_after).toBe("9796.00000000");
  expect(buy.fee).toBe("0.00000000");
  expect(buy.held_after).toBe("2.00000000");
  await nav(page).getByRole("link", { name: "Portfolio", exact: true }).click();
  const portfolio = await page.request.get("/api/v1/portfolio");
  const p = await portfolio.json();
  expect(p.cash).toBe("9796.00");
  expect(p.known_value).toBe("9998.00");
  expect(p.total_value).toBe("9998.00");
  expect(p.holdings[0].stock_mark.feed).toBe("iex");
  await expect(page.getByRole("list", { name: "Allocation" }).getByRole("listitem")).toHaveCount(3);
  await page.getByRole("link", { name: "Trade AAPL", exact: true }).click();
  await page.getByRole("button", { name: "Trade again", exact: true }).click();
  await page.getByRole("radio", { name: "Sell", exact: true }).check();
  await expect(page.getByRole("button", { name: "Sell all", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Sell all", exact: true }).click();
  await expect(page.getByLabel("Whole-share quantity")).toHaveValue("2");
  await preview(page, "2");
  const sell = await fill(page);
  expect(sell.exec_price).toBe("100.00000000");
  expect(sell.cash_after).toBe("9996.00000000");
  expect(sell.held_after).toBe("0.00000000");
  await page.goto("/trade/BTC");
  await expect(page.getByRole("heading", { name: /Trade BTC/ })).toBeVisible();
  await page.getByLabel("Amount", { exact: true }).fill("100");
  for (let attempt = 0; attempt < 3; attempt++) {
    const confirm = page.getByRole("button", { name: "Confirm buy", exact: true });
    await expect(confirm).toBeEnabled();
    await confirm.click();
    const receipt = page.getByRole("heading", { name: "Order filled", exact: true });
    await expect(receipt.or(page.getByText("Price updated. Please review again."))).toBeVisible();
    if (await receipt.isVisible()) break;
  }
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
  await page.goto("/trade/stocks/AAPL");
  await preview(page, "1");
  const next = await fill(page);
  expect(next.cash_after).toBe("9794.00000000");
  await nav(page).getByRole("link", { name: "Portfolio", exact: true }).click();
  const mixed = await (await page.request.get("/api/v1/portfolio")).json();
  expect(mixed.cash).toBe("9794.00");
  expect(mixed.starting_cash).toBe("10000.00");
  expect(mixed.holdings.map((h: { symbol: string }) => h.symbol)).toEqual(["AAPL", "BTC"]);
  await expect(
    page.getByRole("table", { name: "Holdings", exact: true }).getByText("BTC", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("actual-stock-and-crypto-portfolio.png"),
    fullPage: true,
  });
  await reviewSnapshot(page, info, "combined-portfolio-review");
});

test("actual changed ask requires renewed confirmation with the exact server delta", async ({
  page,
}, info) => {
  await ticket(page);
  await preview(page);
  stockFixture("reprice");
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  const changes = page.getByRole("region", { name: "Price changes" });
  await expect(changes).toBeVisible();
  await expect(changes).toContainText("New execution price$103.00");
  await expect(changes).toContainText("Difference−$2.00");
  const before = await (await page.request.get("/api/v1/portfolio")).json();
  expect(before.cash).toBe("10000.00");
  await page.screenshot({ path: info.outputPath("stock-reprice.png"), fullPage: true });
  await reviewSnapshot(page, info, "stock-reprice-review");
  const saved = await fill(page);
  expect(saved.cash_after).toBe("9794.00000000");
});

test("actual committed lost response resolves the original receipt with the same key after close", async ({
  page,
}, info) => {
  await ticket(page);
  await preview(page);
  const bodies: unknown[] = [];
  let original: unknown;
  await page.route("**/api/v1/stock-trades", async (route) => {
    bodies.push(route.request().postDataJSON());
    const response = await route.fetch();
    if (bodies.length === 1) {
      expect(response.status()).toBe(201);
      original = await response.json();
      await route.abort("failed");
    } else {
      expect(response.status()).toBe(200);
      expect(await response.json()).toEqual(original);
      await route.fulfill({ response });
    }
  });
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  const check = page.getByRole("button", { name: "Check order result", exact: true });
  await expect(check).toBeEnabled();
  stockFixture("close");
  await page.getByRole("button", { name: "Retry stock", exact: true }).click();
  await expect(page.getByLabel("Whole-share quantity")).toBeDisabled();
  await check.click();
  await expect(page.getByRole("heading", { name: "Order filled" })).toBeFocused();
  expect(bodies[1]).toEqual(bodies[0]);
  await page.screenshot({ path: info.outputPath("stock-replayed-receipt.png"), fullPage: true });
  const p = await (await page.request.get("/api/v1/portfolio")).json();
  expect(p.cash).toBe("9796.00");
  expect(p.holdings[0].quantity).toBe("2.00000000");
});

test("actual malformed success preserves the original attempt for safe result recovery", async ({
  page,
}) => {
  await ticket(page);
  await preview(page);
  let count = 0;
  await page.route("**/api/v1/stock-trades", async (route) => {
    const response = await route.fetch();
    if (++count === 1) {
      expect(response.status()).toBe(201);
      await route.fulfill({ status: 201, json: { invalid: true } });
    } else await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  await page.getByRole("button", { name: "Check order result", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Order filled" })).toBeVisible();
  expect(count).toBe(2);
});

test("closed drafts retain quantity and require a fresh explicit preview after reopening", async ({
  page,
}, info) => {
  await ticket(page);
  await preview(page);
  stockFixture("close");
  await page.getByRole("button", { name: "Retry stock", exact: true }).click();
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeDisabled();
  await expect(page.getByLabel("Whole-share quantity")).toHaveValue("2");
  await page.getByLabel("Whole-share quantity").fill("3");
  await expect(page.getByRole("button", { name: "Preview trade", exact: true })).toBeDisabled();
  await page.screenshot({ path: info.outputPath("stock-closed-draft.png"), fullPage: true });
  stockFixture("open");
  await page.getByRole("button", { name: "Retry stock", exact: true }).click();
  await expect(page.getByRole("button", { name: "Preview trade", exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeDisabled();
  expect((await (await page.request.get("/api/v1/portfolio")).json()).cash).toBe("10000.00");
});

test("real historical closed/halted marks survive execution age while uncertain actions make totals incomplete", async ({
  page,
}, info) => {
  await ticket(page);
  await preview(page);
  await fill(page);
  stockFixture("close");
  await nav(page).getByRole("link", { name: "Portfolio", exact: true }).click();
  await expect(
    page
      .getByRole("table", { name: "Holdings", exact: true })
      .getByText("Market closed", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("table", { name: "Holdings", exact: true }).getByText(/Last verified midpoint/),
  ).toBeVisible();
  await page.screenshot({ path: info.outputPath("stock-closed-portfolio.png"), fullPage: true });
  stockFixture("halt");
  await page.getByRole("button", { name: "Refresh portfolio", exact: true }).click();
  await expect(
    page.getByRole("table", { name: "Holdings", exact: true }).getByText("Halted", { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: info.outputPath("stock-halted-portfolio.png"), fullPage: true });
  stockFixture("hold");
  await page.getByRole("button", { name: "Refresh portfolio", exact: true }).click();
  await expect(
    page.getByText("Known value: $9,796.00 — incomplete", { exact: true }),
  ).toBeVisible();
  await expect(page.locator("[data-allocation-fill]")).toHaveCount(0);
  await expect(
    page.getByText("1 holding cannot be valued. Overall gain/loss and allocation are unavailable."),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("stock-incomplete-portfolio.png"),
    fullPage: true,
  });
  await reviewSnapshot(page, info, "incomplete-portfolio-review");
});

for (const width of [320, 375, 768, 1024, 1440]) {
  test(`actual ticket receipt and complete portfolio reflow at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    stockFixture("long-name");
    await ticket(page);
    await preview(page);
    await noOverflow(page);
    expect(
      await page
        .getByRole("button", { name: "Confirm buy", exact: true })
        .evaluate((el) => el.getBoundingClientRect().height),
    ).toBeGreaterThanOrEqual(44);
    await page.screenshot({ path: info.outputPath(`stock-preview-${width}.png`), fullPage: true });
    if (width === 1440) await reviewSnapshot(page, info, "stock-preview-review");
    await fill(page);
    await noOverflow(page);
    await page.screenshot({ path: info.outputPath(`stock-receipt-${width}.png`), fullPage: true });
    if (width === 1440) await reviewSnapshot(page, info, "stock-receipt-review");
    await nav(page).getByRole("link", { name: "Portfolio", exact: true }).click();
    await expect(page.getByRole("table", { name: "Holdings", exact: true })).toHaveCount(
      width >= 1024 ? 1 : 0,
    );
    await expect(page.getByRole("list", { name: "Holdings", exact: true })).toHaveCount(
      width < 1024 ? 1 : 0,
    );
    await noOverflow(page);
    await page.screenshot({
      path: info.outputPath(`mixed-portfolio-${width}.png`),
      fullPage: true,
    });
  });
}
test("keyboard-only ticket controls and stale deadlines never queue an order", async ({
  page,
}, info) => {
  await ticket(page);
  const input = page.getByLabel("Whole-share quantity");
  await input.focus();
  await page.keyboard.type("1.5");
  await expect(input).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("button", { name: "Preview trade", exact: true })).toBeDisabled();
  await input.fill("2");
  const buy = page.getByRole("radio", { name: "Buy", exact: true });
  await buy.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("radio", { name: "Sell", exact: true })).toBeChecked();
  await page.keyboard.press("ArrowLeft");
  await expect(buy).toBeChecked();
  await page.getByRole("button", { name: "Preview trade", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeEnabled();
  stockFixture("stale");
  await page.getByRole("button", { name: "Retry stock", exact: true }).click();
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeDisabled();
  await expect(input).toHaveValue("2");
  expect((await (await page.request.get("/api/v1/portfolio")).json()).cash).toBe("10000.00");
  await noOverflow(page);
  await page.screenshot({
    path: info.outputPath("stock-keyboard-stale-draft.png"),
    fullPage: true,
  });
});

test("a late actual fill response cannot leak into another signed-in account", async ({ page }) => {
  await ticket(page);
  await preview(page);
  let release!: () => void;
  let committed = false;
  await page.route("**/api/v1/stock-trades", async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    committed = true;
    await new Promise<void>((r) => {
      release = r;
    });
    await route.fulfill({ response });
  });
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  await expect.poll(() => committed).toBe(true);
  await page.goto("/account");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("button", { name: "Send code", exact: true })).toBeVisible();
  await signInNewUser(page);
  release();
  await page.goto("/trade/stocks/AAPL");
  await expect(page.getByLabel("Whole-share quantity")).toHaveValue("");
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toHaveCount(0);
  expect((await (await page.request.get("/api/v1/portfolio")).json()).cash).toBe("10000.00");
});

test("checks browser zoom support and captures explicit supplementary reflow", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await ticket(page);
  await preview(page);
  const before = await page.evaluate<{ width: number; ratio: number }>(
    "({width:innerWidth,ratio:devicePixelRatio})",
  );
  for (let i = 0; i < 5; i++) await page.keyboard.press("Control+Equal");
  const after = await page.evaluate<{ width: number; ratio: number }>(
    "({width:innerWidth,ratio:devicePixelRatio})",
  );
  const native = after.width <= before.width * 0.51 && after.ratio >= before.ratio * 1.99;
  console.log("native_browser_zoom_200pct=" + native);
  info.annotations.push({
    type: "native-browser-zoom",
    description: native
      ? "Observed actual 200% browser viewport and pixel-ratio change."
      : "Headless keyboard shortcut did not apply native 200% zoom; true zoom remains an owner check. Following capture is supplementary 640px reflow only.",
  });
  if (!native) await page.setViewportSize({ width: 640, height: 450 });
  await noOverflow(page);
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeVisible();
  await page.screenshot({
    path: info.outputPath(
      native ? "stock-native-200pct.png" : "stock-supplementary-reflow-640.png",
    ),
    fullPage: true,
  });
  await fill(page);
  await nav(page).getByRole("link", { name: "Portfolio", exact: true }).click();
  await noOverflow(page);
  await page.screenshot({
    path: info.outputPath(
      native ? "portfolio-native-200pct.png" : "portfolio-supplementary-reflow-640.png",
    ),
    fullPage: true,
  });
});
