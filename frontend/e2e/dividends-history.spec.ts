import { expect, test, type Locator, type Page, type TestInfo } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { writeFile } from "node:fs/promises";
import { signInNewUser } from "./helpers.js";
import { stockFixture } from "./stock-trade-fixtures.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
type Ledger = {
  cash: string;
  originals: Array<{ id: number; amount: string }>;
  decisions: Array<{ id: number; outcome: string; delta: string; desired: string | null }>;
};
function evidence(operation: string, email: string, symbol = "AMD"): Ledger {
  expect(process.env.COMPOSE_PROJECT_NAME).toBe("birja-phase09-e2e-test");
  return JSON.parse(
    execFileSync(
      "docker",
      [
        "compose",
        "exec",
        "-T",
        "backend",
        "python",
        "/browser-fixtures/dividend-execution-fixture.py",
        operation,
        email,
        symbol,
      ],
      { cwd: root, encoding: "utf8", timeout: 60000 },
    ),
  );
}
const cents = (value: string) => {
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0").slice(0, 2));
};
const activity = (page: Page) =>
  page.getByRole(page.viewportSize()!.width >= 1024 ? "table" : "list", {
    name: "Account activity",
    exact: true,
  });
async function focusedInView(page: Page, target: Locator) {
  await expect(target).toBeFocused();
  const box = await target.boundingBox();
  expect(box).not.toBeNull();
  const viewport = page.viewportSize()!;
  const nav =
    viewport.width < 768
      ? await page.getByRole("navigation", { name: "Main" }).boundingBox()
      : null;
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.y + box!.height).toBeLessThanOrEqual(nav?.y ?? viewport.height);
}
async function history(page: Page) {
  await page.goto("/history");
  await expect(page.getByRole("heading", { name: "Account activity", exact: true })).toBeVisible();
  return (await page.request.get("/api/v1/history")).json();
}
async function cryptoFill(page: Page, side: "buy" | "sell", amount: string) {
  await page.goto("/trade/BTC");
  if (side === "sell") await page.getByRole("radio", { name: "Sell", exact: true }).check();
  await page.getByLabel(side === "buy" ? "Amount" : "Quantity", { exact: true }).fill(amount);
  for (let attempt = 0; attempt < 3; attempt++) {
    const response = page.waitForResponse(
      (r) => r.url().endsWith("/api/v1/trades") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: `Confirm ${side}`, exact: true }).click();
    const result = await response;
    const body = await result.json();
    if (result.ok()) {
      await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
      return body;
    }
    expect(body.detail.code).toBe("price_changed");
  }
  throw new Error("No actual crypto fill after bounded confirmations");
}
async function snapshot(page: Page, info: TestInfo, name: string) {
  let css = await page.evaluate<string>(
    "Array.from(document.styleSheets).flatMap(sheet=>Array.from(sheet.cssRules,rule=>rule.cssText)).join('\\n')",
  );
  const origin = new URL(page.url()).origin;
  for (const match of [...css.matchAll(/url\((["']?)([^)"']+)\1\)/g)]) {
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
  const html = await page.evaluate<string>(
    `((styles)=>{const d=document.cloneNode(true);d.querySelectorAll('script,link,style,iframe,form').forEach(n=>n.remove());const s=d.createElement('style');s.textContent=styles;d.head.append(s);d.querySelectorAll('a').forEach(n=>n.setAttribute('href','#'));d.querySelectorAll('button').forEach(n=>n.setAttribute('type','button'));const p=d.createElement('p');p.textContent='Read-only synthetic Phase 10 review. Actions do not execute. Check native 200% zoom using your browser menu.';p.style.padding='16px';d.body.prepend(p);return '<!doctype html>\\n'+d.documentElement.outerHTML})(${JSON.stringify(css)})`,
  );
  expect(html).not.toMatch(/<script|<form|\s(?:src|href|action)=["']https?:/);
  await writeFile(info.outputPath(name + ".html"), html);
  await page.screenshot({ path: info.outputPath(name + "-viewport.png") });
  await page.screenshot({ path: info.outputPath(name + ".png"), fullPage: true });
}
test.use({ timezoneId: "Europe/Moscow" });
test.beforeEach(() => stockFixture("fresh"));

test("authenticated mixed History starts empty", async ({ page }) => {
  await signInNewUser(page);
  const response = await page.request.get("/api/v1/history");
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ items: [], next_cursor: null });
});

test("real restricted worker credits once and publishes uncertainty with no cash change", async ({
  page,
}, info) => {
  test.setTimeout(120000);
  const email = await signInNewUser(page);
  const paid = evidence("seed", email);
  expect(cents(paid.cash)).toBe(2000000n);
  expect(paid.originals).toHaveLength(1);
  expect(cents(paid.originals[0].amount)).toBe(1000000n);
  expect(evidence("cycle", email)).toEqual(paid);
  const data = await history(page);
  expect(data.items.filter((item: { kind: string }) => item.kind === "dividend")).toHaveLength(1);
  await expect(activity(page)).toContainText("Gross ordinary USD dividend");
  await expect(activity(page)).toContainText("+$10,000.00");
  await snapshot(page, info, "dividend-original");
  // Spend more than the original10000 grant, so these actual purchases need
  // credited dividend funds. No financial success response is intercepted.
  await page.goto("/trade/stocks/AAPL");
  await page.getByLabel("Whole-share quantity").fill("50");
  await page.getByRole("button", { name: "Preview trade", exact: true }).click();
  const stockResponse = page.waitForResponse(
    (r) => r.url().endsWith("/api/v1/stock-trades") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  const stockResult = await stockResponse;
  expect(stockResult.status()).toBe(201);
  expect(cents((await stockResult.json()).cash_after)).toBe(1490000n);
  const bought = await cryptoFill(page, "buy", "10000");
  expect(cents(bought.cash_after)).toBe(490000n);
  expect(cents(evidence("inspect", email).cash)).toBe(490000n);
  const increased = evidence("up", email);
  expect(cents(increased.cash)).toBe(490200n);
  const held = evidence("down", email);
  expect(held.cash).toBe(increased.cash);
  expect(held.decisions.at(-1)?.outcome).toBe("held_unaffordable");
  expect(evidence("cycle", email)).toEqual(held);
  await history(page);
  await expect(activity(page)).toContainText(
    "Not enough available cash for this correction. No cash changed.",
  );
  await snapshot(page, info, "dividend-held-unaffordable");
  const sold = await cryptoFill(page, "sell", bought.quantity);
  const decreased = evidence("cycle", email);
  expect(cents(decreased.cash)).toBe(cents(sold.cash_after) - 1000100n);
  expect(decreased.decisions.at(-1)?.outcome).toBe("applied");
  expect(cents(decreased.decisions.at(-1)!.delta)).toBe(-1000100n);
  const uncertain = evidence("uncertain", email);
  expect(uncertain.cash).toBe(decreased.cash);
  expect(uncertain.decisions.at(-1)?.outcome).toBe("held_uncertain");
  expect(evidence("cycle", email)).toEqual(uncertain);
  await history(page);
  await expect(activity(page)).toContainText(
    "The corrected dividend terms need verification. No cash changed.",
  );
  await snapshot(page, info, "dividend-held-uncertain");
  const resolved = evidence("reconcile", email);
  expect(cents(resolved.cash)).toBe(cents(decreased.cash) + 1000300n);
  expect(resolved.decisions.map((row) => row.outcome)).toEqual([
    "applied",
    "held_unaffordable",
    "applied",
    "held_uncertain",
    "applied",
  ]);
  expect(evidence("cycle", email)).toEqual(resolved);
  const final = await history(page);
  expect(final.items[0].kind).toBe("dividend_correction");
  expect(cents(final.items[0].cash_delta)).toBe(1000300n);
  await snapshot(page, info, "dividend-reconciled");
});

test("actual mixed pages preserve originals, responsive focus and failed-read recovery", async ({
  page,
}, info) => {
  test.setTimeout(180000);
  const email = await signInNewUser(page);
  stockFixture("long-name", "MSFT");
  const bulk = evidence("bulk", email, "MSFT");
  expect(bulk.originals).toHaveLength(28);
  expect(cents(bulk.cash)).toBe(1000000n);
  evidence("up", email, "MSFT");
  await cryptoFill(page, "buy", "1");
  evidence("split", email, "MSFT");
  let release: () => void = () => {};
  const paused = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/history*", async (route) => {
    const response = await route.fetch();
    await paused;
    await route.fulfill({ response });
  });
  await page.goto("/history", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("status", { name: "Loading history" })).toBeVisible();
  await snapshot(page, info, "history-loading");
  release();
  await expect(activity(page)).toBeVisible();
  await page.unroute("**/api/v1/history*");
  const first = await (await page.request.get("/api/v1/history")).json();
  expect(first.items).toHaveLength(25);
  expect(new Set(first.items.map((item: { kind: string }) => item.kind))).toEqual(
    new Set(["trade", "split", "dividend", "dividend_correction"]),
  );
  const split = first.items.find((item: { kind: string }) => item.kind === "split");
  expect(split).toMatchObject({
    ratio_new: "3",
    ratio_old: "2",
    quantity_before: "2.00000000",
    quantity_after: "3.00000000",
  });
  for (const width of [320, 375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await expect(activity(page)).toBeVisible();
    await expect(
      page.getByRole(width >= 1024 ? "list" : "table", { name: "Account activity", exact: true }),
    ).toHaveCount(0);
    expect(await page.evaluate("document.documentElement.scrollWidth<=innerWidth")).toBe(true);
    await expect(activity(page)).toContainText("USD 0.00000001 per share");
    const original = activity(page)
      .getByRole("button", { name: "View original dividend", exact: true })
      .first();
    await original.focus();
    await page.keyboard.press("Enter");
    const heading = activity(page).getByRole("heading", { name: /Original dividend/ });
    await expect(heading).toBeFocused();
    await expect(heading).toBeVisible();
    const back = activity(page).getByRole("button", { name: "Back to correction", exact: true });
    const box = await back.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    await back.focus();
    await back.scrollIntoViewIfNeeded();
    if (width < 768) {
      const nav = await page.getByRole("navigation", { name: "Main" }).boundingBox();
      const target = await back.boundingBox();
      expect(target!.y + target!.height).toBeLessThanOrEqual(nav!.y);
    }
    await snapshot(page, info, `mixed-history-${width}`);
    await page.keyboard.press("Enter");
    await expect(original).toBeFocused();
  }
  await page.route("**/api/v1/history*", (route) =>
    route.fulfill({ status: 503, json: { detail: "synthetic unavailable" } }),
  );
  await page.getByRole("button", { name: "Load more", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Your loaded events are still here");
  await expect(page.getByRole("button", { name: "Try loading more", exact: true })).toBeFocused();
  await focusedInView(page, page.getByRole("button", { name: "Try loading more", exact: true }));
  await expect(activity(page)).toContainText("Forward split");
  await snapshot(page, info, "history-append-error");
  await page.unroute("**/api/v1/history*");
  const end = page.getByText("All events loaded.", { exact: true });
  await page.getByRole("button", { name: "Try loading more", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(end).toBeFocused();
  await focusedInView(page, end);
  const all = await (await page.request.get(`/api/v1/history?limit=100`)).json();
  expect(all.items).toHaveLength(31);
  expect(new Set(all.items.map((item: { id: string }) => item.id)).size).toBe(31);
  await expect(page.getByRole("status")).toContainText("6 more events loaded. 31 events shown.");
  await snapshot(page, info, "history-all-loaded");
  for (const width of [320, 375, 768, 1024]) {
    await page.setViewportSize({ width, height: 900 });
    await page.reload();
    const more = page.getByRole("button", { name: "Load more", exact: true });
    await more.focus();
    await page.keyboard.press("Enter");
    await focusedInView(page, end);
    expect(await page.evaluate("document.documentElement.scrollWidth<=innerWidth")).toBe(true);
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.route("**/api/v1/history*", (route) =>
    route.fulfill({ status: 503, json: { detail: "synthetic unavailable" } }),
  );
  await page.getByRole("button", { name: "Refresh history", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Showing the last successful update");
  await expect(activity(page)).toContainText("Forward split");
  await snapshot(page, info, "history-refresh-error");
  await page.unroute("**/api/v1/history*");
  // Separate read-only presentation fixture: retained real economics with a
  // synthetic common publication time. Actual SQL tie/privacy proof is Plan10;
  // this checks browser order/append only, never creates a cash success.
  const kinds = ["trade", "dividend", "split", "dividend_correction"] as const;
  const tied = kinds.map((kind) => ({
    ...all.items.find((item: { kind: string }) => item.kind === kind),
    recorded_at: all.items[0].recorded_at,
  }));
  const boundary = Buffer.from(
    JSON.stringify({
      v: 2,
      recorded_at: tied[1].recorded_at,
      kind_rank: 3,
      source_id: tied[1].id.split(":")[1],
    }),
  ).toString("base64url");
  await page.route("**/api/v1/history*", (route) =>
    route.fulfill({
      json: new URL(route.request().url()).searchParams.has("cursor")
        ? { items: tied.slice(2), next_cursor: null }
        : { items: tied.slice(0, 2), next_cursor: boundary },
    }),
  );
  await page.reload();
  await expect(activity(page)).toBeVisible();
  await page.getByRole("button", { name: "Load more", exact: true }).click();
  await expect(page.getByText("All events loaded.", { exact: true })).toBeFocused();
  const identities = await activity(page)
    .locator("tbody tr, :scope > li")
    .evaluateAll((nodes) => nodes.map((node) => node.id.replace(/^history-(desktop|mobile)-/, "")));
  expect(identities).toEqual(tied.map((item) => item.id));
  await snapshot(page, info, "history-tied-read-only");
  await page.unroute("**/api/v1/history*");
  // Supplementary enlarged text only; owner native browser zoom remains pending.
  await page.addStyleTag({ content: "html{font-size:200%}" });
  expect(await page.evaluate("document.documentElement.scrollWidth<=innerWidth")).toBe(true);
});

test("pre-anchor uncertainty has no Dividend and late previous-owner reads cannot return", async ({
  page,
}, info) => {
  test.setTimeout(120000);
  const email = await signInNewUser(page);
  const before = evidence("preanchor", email, "NVDA");
  expect(cents(before.cash)).toBe(1000000n);
  expect(before.originals).toEqual([]);
  expect(before.decisions).toEqual([]);
  expect(evidence("cycle", email, "NVDA")).toEqual(before);
  await history(page);
  await expect(page.getByRole("heading", { name: "No activity yet", exact: true })).toBeVisible();
  await snapshot(page, info, "history-empty");
  await page.route("**/api/v1/history*", (route) =>
    route.fulfill({ status: 503, json: { detail: "synthetic unavailable" } }),
  );
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("Can't load your history");
  await snapshot(page, info, "history-initial-error");
  await page.unroute("**/api/v1/history*");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No activity yet", exact: true })).toBeVisible();
  await cryptoFill(page, "buy", "1");
  await history(page);
  await expect(activity(page)).toContainText("−$1.00");
  let release: () => void = () => {};
  const paused = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started: () => void = () => {};
  const observed = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route("**/api/v1/history*", async (route) => {
    const response = await route.fetch();
    started();
    await paused;
    try {
      await route.fulfill({ response });
    } catch {
      /* Navigation aborted the old real read. */
    }
  });
  await page.getByRole("button", { name: "Refresh history", exact: true }).click();
  await observed;
  await page.getByRole("link", { name: "Account", exact: true }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Email", { exact: true })).toBeVisible();
  release();
  await page.unroute("**/api/v1/history*");
  await signInNewUser(page);
  await history(page);
  await expect(page.getByRole("heading", { name: "No activity yet", exact: true })).toBeVisible();
  expect((await (await page.request.get("/api/v1/history")).json()).items).toEqual([]);
});
