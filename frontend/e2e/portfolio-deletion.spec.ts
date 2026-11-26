import { expect, test, type Page, type Route, type APIResponse } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { signInNewUser, portfolioId } from "./helpers.js";
import { stockFixture } from "./stock-trade-fixtures.js";
import { capturePhase14 } from "./portfolio-review-capture.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
const api = "/api/v2/portfolios";
const policy = "freeze_at_closure_v1";
const deletionStorage = "birja:portfolio-deletion:v1";
const button = (page: Page, name: string) => page.getByRole("button", { name, exact: true });
type Book = { id: string; name: string; description?: string };
type Oracle = { read_only: true; roots: Record<string, Record<string, string | string[]>> };

function latch() {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function oracle(email: string): Oracle {
  expect(process.env.COMPOSE_PROJECT_NAME).toBe("birja-phase09-e2e-test");
  const value = JSON.parse(
    execFileSync(
      "docker",
      [
        "compose",
        "exec",
        "-T",
        "backend",
        "python",
        "/e2e/portfolio-browser-fixture.py",
        "lifecycle",
        email,
      ],
      { cwd: root, encoding: "utf8", timeout: 30000 },
    ),
  );
  expect(value.read_only).toBe(true);
  return value;
}
async function headers(page: Page) {
  expect((await page.request.get("/api/v1/auth/csrf")).status()).toBe(204);
  const cookie = (await page.context().cookies()).find((value) => value.name === "bj_csrf");
  expect(cookie).toBeDefined();
  return { "X-CSRF-Token": cookie!.value };
}
async function books(page: Page): Promise<Book[]> {
  const response = await page.request.get(api);
  expect(response.status()).toBe(200);
  return response.json();
}
async function create(page: Page, name: string, description = ""): Promise<Book> {
  const response = await page.request.post(api, {
    headers: { ...(await headers(page)), "Idempotency-Key": crypto.randomUUID() },
    data: { name, description },
  });
  expect(response.status()).toBe(201);
  return response.json();
}
async function rename(page: Page, id: string, name: string, description?: string) {
  const response = await page.request.patch(api + "/" + id, {
    headers: await headers(page),
    data: { name, ...(description === undefined ? {} : { description }) },
  });
  expect(response.status()).toBe(200);
}
async function close(page: Page, id: string, name: string, intentKey = crypto.randomUUID()) {
  const response = await page.request.delete(api + "/" + id, {
    headers: await headers(page),
    data: { intent_key: intentKey, confirmation_name: name, policy_version: policy },
  });
  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ portfolio_id: id, state: "closed" });
}
async function detail(page: Page, id: string) {
  await page.goto("/portfolios/" + id);
  await expect(button(page, "Remove portfolio")).toBeEnabled();
}
async function review(page: Page) {
  await button(page, "Remove portfolio").click();
  await expect(button(page, "Keep portfolio")).toBeFocused();
  await expect(button(page, "Delete portfolio")).toBeEnabled();
}
async function unavailable(page: Page) {
  await expect(
    page.getByRole("heading", { name: "Portfolio unavailable", exact: true }),
  ).toBeVisible();
  await expect(button(page, "Check order result")).toHaveCount(0);
  await expect(button(page, "Confirm buy")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toHaveCount(0);
}
async function buy(page: Page, id: string, amount = "100") {
  await page.goto("/portfolios/" + id + "/trade/BTC");
  await page.getByLabel("Amount", { exact: true }).fill(amount);
  for (let attempt = 0; attempt < 4; attempt++) {
    await expect(button(page, "Confirm buy")).toBeEnabled();
    const received = page.waitForResponse(
      (r) => r.url().endsWith(api + "/" + id + "/trades") && r.request().method() === "POST",
    );
    await button(page, "Confirm buy").click();
    const response = await received;
    if (response.status() === 201) {
      await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
      return { fill: await response.json(), body: response.request().postDataJSON() };
    }
    expect((await response.json()).detail.code).toBe("price_changed");
  }
  throw new Error("No fill after bounded explicit confirmations");
}
async function buyStock(page: Page, id: string) {
  await page.goto("/portfolios/" + id + "/trade/stocks/AAPL");
  await page.getByLabel("Whole-share quantity").fill("1");
  await button(page, "Preview trade").click();
  await expect(button(page, "Confirm buy")).toBeEnabled();
  const received = page.waitForResponse(
    (r) => r.url().endsWith(api + "/" + id + "/stock-trades") && r.request().method() === "POST",
  );
  await button(page, "Confirm buy").click();
  expect((await received).status()).toBe(201);
}
async function logout(page: Page) {
  await button(page, "Sign out").click();
  await expect(page.getByLabel("Email", { exact: true })).toBeVisible();
}
function deliveries(email: string) {
  expect(email).toMatch(/^e2e-[a-z0-9-]+@example\.com$/);
  const logs = execFileSync("docker", ["compose", "logs", "--no-color", "backend"], {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
  });
  return [
    ...logs.matchAll(
      new RegExp("DEV EMAIL to=" + email.replaceAll(".", "\\.") + " code=(\\d{6})", "g"),
    ),
  ];
}
async function signIn(page: Page, email: string) {
  // A fresh delivery event, rather than a different random value, establishes
  // freshness. A legitimate newly generated code may repeat the old digits.
  const cursor = deliveries(email).length;
  await page.goto("/");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await button(page, "Send code").click();
  let code = "";
  await expect
    .poll(
      () => {
        const received = deliveries(email);
        if (received.length <= cursor) return false;
        code = received.at(-1)![1];
        return true;
      },
      { timeout: 20000 },
    )
    .toBe(true);
  await page.getByLabel("6-digit code").fill(code);
  await button(page, "Sign in").click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
}
async function deliver(route: Route, response: APIResponse) {
  // A deliberately abandoned transport may already be cancelled. Its real
  // server response is still inspected; cancellation never asserts rollback.
  await route.fulfill({ response }).catch(() => {});
}
async function assertPrivate(response: APIResponse) {
  expect(response.status()).toBe(404);
  expect(await response.json()).toEqual({ detail: { code: "portfolio_unavailable" } });
  expect(response.headers()["cache-control"]).toContain("no-store");
}
test.beforeEach(() => stockFixture("fresh"));

test("Phase14 keeping a portfolio is a no-op; holdings freeze, stale paths refuse and siblings trade", async ({
  page,
}) => {
  test.setTimeout(120000);
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  await rename(page, id, "Private closed strategy");
  const sibling = await create(page, "Independent strategy");
  const original = await buy(page, id);
  await buy(page, id, "25");
  await buyStock(page, id);
  const oldPage = await (await page.request.get(api + "/" + id + "/event-history?limit=1")).json();
  expect(oldPage.next_cursor).toBeTruthy();
  await detail(page, id);
  const before = oracle(email);
  let deletes = 0;
  page.on("request", (request) => {
    if (request.method() === "DELETE") deletes++;
  });
  await review(page);
  await expect(
    page.getByText("Nothing will be sold or moved to another portfolio.", { exact: false }),
  ).toBeVisible();
  await button(page, "Keep portfolio").press("Enter");
  await expect(button(page, "Remove portfolio")).toBeFocused();
  expect(deletes).toBe(0);
  expect(oracle(email)).toEqual(before);
  await review(page);
  await page.keyboard.press("Escape");
  await expect(button(page, "Remove portfolio")).toBeFocused();
  expect(deletes).toBe(0);
  expect(oracle(email)).toEqual(before);
  await review(page);
  const received = page.waitForResponse((r) => r.request().method() === "DELETE");
  await button(page, "Delete portfolio").click();
  const closed = await received;
  expect(closed.status()).toBe(200);
  expect(await closed.json()).toEqual({ portfolio_id: id, state: "closed" });
  await expect(page).toHaveURL("/portfolios");
  await expect(page.getByRole("heading", { name: "Portfolios", exact: true })).toBeFocused();
  expect((await books(page)).map((book) => book.id)).toEqual([sibling.id]);
  const frozen = oracle(email).roots[id];
  expect(frozen.account_financial).toEqual(before.roots[id].account_financial);
  for (const table of [
    "holdings",
    "trades",
    "stock_fill_facts",
    "stock_ownership_movements",
    "stock_dividend_entitlements",
    "stock_dividend_payments",
    "stock_dividend_decisions",
  ]) {
    expect(frozen[table]).toEqual(before.roots[id][table]);
  }
  expect(frozen.portfolio_lifecycle_closures).toHaveLength(1);
  const originalIntent = closed.request().postDataJSON();
  const replay = await page.request.delete(api + "/" + id, {
    headers: await headers(page),
    data: originalIntent,
  });
  expect(replay.status()).toBe(200);
  expect(await replay.json()).toEqual({ portfolio_id: id, state: "closed" });
  await close(page, id, "Private closed strategy");
  for (const path of [
    "",
    "/metadata",
    "/holdings/BTC",
    "/stock-trades/AAPL/context",
    "/history",
    "/event-history",
    "/event-history?limit=1&cursor=" + encodeURIComponent(oldPage.next_cursor),
  ]) {
    await assertPrivate(await page.request.get(api + "/" + id + path));
  }
  await assertPrivate(
    await page.request.post(api + "/" + id + "/trades", {
      headers: await headers(page),
      data: original.body,
    }),
  );
  await assertPrivate(
    await page.request.post(api + "/" + id + "/trades/quote", {
      headers: await headers(page),
      data: { symbol: "BTC", side: "buy", amount_usd: "10" },
    }),
  );
  await assertPrivate(
    await page.request.post(api + "/" + id + "/stock-trades/quote", {
      headers: await headers(page),
      data: { symbol: "AAPL", side: "buy", quantity: "1" },
    }),
  );
  for (const path of [
    "",
    "/history",
    "/trade/BTC",
    "/trade/stocks/AAPL",
    "/history?cursor=" + encodeURIComponent(oldPage.next_cursor),
  ]) {
    await page.goto("/portfolios/" + id + path);
    await unavailable(page);
    await expect(page.getByText("Private closed strategy", { exact: true })).toHaveCount(0);
  }
  await buy(page, sibling.id, "10");
  expect(oracle(email).roots[id]).toEqual(frozen);
});

test("Phase14 deletion last portfolio preserves signed-in zero through reload sign-in Back and explicit replacement", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  await detail(page, id);
  await review(page);
  await expect(page.getByText(/This is your last active portfolio/)).toBeVisible();
  await button(page, "Delete portfolio").click();
  await expect(page).toHaveURL("/portfolios");
  await expect(page.getByRole("heading", { name: "No portfolios yet", exact: true })).toBeVisible();
  const frozen = oracle(email);
  await page.reload();
  expect(await books(page)).toEqual([]);
  await page.goto("/portfolios/" + id);
  await unavailable(page);
  await page.goBack();
  await expect(page.getByRole("heading", { name: "No portfolios yet", exact: true })).toBeVisible();
  await logout(page);
  await signIn(page, email);
  expect(await books(page)).toEqual([]);
  expect(oracle(email)).toEqual(frozen);
  await page.goto("/portfolios");
  await button(page, "New portfolio").click();
  await page.getByLabel("Portfolio name", { exact: true }).fill("My portfolio");
  await page.locator("form").getByRole("button", { name: "Create portfolio", exact: true }).click();
  await expect(page).toHaveURL(/\/portfolios\/\d+$/);
  const replacement = (await books(page))[0];
  expect(replacement.id).not.toBe(id);
  const statement = await (await page.request.get(api + "/" + replacement.id)).json();
  expect(statement.cash).toBe("10000.00");
  expect(statement.starting_cash).toBe("10000.00");
  expect(oracle(email).roots[id]).toEqual(frozen.roots[id]);
});

test("Phase14 deletion lost committed response reload checks only original despite same-name replacement and sibling trades", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  const sibling = await create(page, "Sibling available while unknown");
  const requests: string[] = [];
  await page.route("**" + api + "/" + id, async (route) => {
    if (route.request().method() !== "DELETE") return route.continue();
    requests.push(route.request().postData()!);
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    expect(await response.json()).toEqual({ portfolio_id: id, state: "closed" });
    if (requests.length === 1) await route.abort("failed");
    else await deliver(route, response);
  });
  await detail(page, id);
  await review(page);
  await button(page, "Delete portfolio").click();
  await expect(
    page.getByRole("heading", { name: "Deletion result unconfirmed", exact: true }),
  ).toBeVisible();
  const frozen = oracle(email).roots[id];
  await page.goto("/portfolios");
  await expect(
    page.getByRole("link", { name: "Review deletion request", exact: true }),
  ).toBeVisible();
  await buy(page, sibling.id, "10");
  const replacement = await create(page, "My portfolio");
  expect(replacement.id).not.toBe(id);
  await page.goto("/portfolios/deletion");
  await page.reload();
  await expect(button(page, "Check deletion result")).toBeEnabled();
  expect(requests).toHaveLength(1);
  const marker = await page.evaluate(
    (key) => JSON.parse(sessionStorage.getItem(key)!),
    deletionStorage,
  );
  expect(marker.attempt.portfolioId).toBe(id);
  expect(marker.attempt.confirmationName).toBe("My portfolio");
  expect(Object.keys(marker.attempt).sort()).toEqual([
    "confirmationName",
    "intentKey",
    "policyVersion",
    "portfolioId",
  ]);
  await button(page, "Check deletion result").click();
  await expect(page).toHaveURL("/portfolios");
  expect(requests).toHaveLength(2);
  expect(requests[1]).toBe(requests[0]);
  expect((await books(page)).map((book) => book.id)).toEqual([sibling.id, replacement.id]);
  expect(oracle(email).roots[id]).toEqual(frozen);
});

test("Phase14 deletion delayed first request remains unknown while active GET cannot cancel original", async ({
  page,
}) => {
  test.setTimeout(90000);
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  const sibling = await create(page, "Delayed sibling");
  const entered = latch(),
    release = latch(),
    finished = latch();
  const requests: string[] = [];
  await page.route("**" + api + "/" + id, async (route) => {
    if (route.request().method() !== "DELETE") return route.continue();
    const first = requests.length === 0;
    requests.push(route.request().postData()!);
    if (first) {
      entered.resolve();
      await release.promise;
    }
    try {
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      if (!first) await deliver(route, response);
      else await route.abort("failed").catch(() => {});
    } finally {
      if (first) finished.resolve();
    }
  });
  try {
    await detail(page, id);
    await review(page);
    await button(page, "Delete portfolio").click();
    await entered.promise;
    await expect(
      page.getByRole("heading", { name: "Deleting portfolio…", exact: true }),
    ).toBeVisible();
    expect((await books(page)).some((book) => book.id === id)).toBe(true);
    await page.goto("/portfolios/deletion");
    await expect(button(page, "Check deletion result")).toBeEnabled();
    expect(requests).toHaveLength(1);
    await page.goto("/portfolios");
    await expect(page.getByRole("link", { name: "My portfolio", exact: true })).toHaveCount(0);
    await buy(page, sibling.id, "10");
    await page.goto("/portfolios/deletion");
    await button(page, "Check deletion result").click();
    await expect(page).toHaveURL("/portfolios");
    expect(requests).toHaveLength(2);
    expect(requests[1]).toBe(requests[0]);
    const frozen = oracle(email).roots[id];
    release.resolve();
    await finished.promise;
    expect(oracle(email).roots[id]).toEqual(frozen);
    expect((await books(page)).map((book) => book.id)).toEqual([sibling.id]);
  } finally {
    release.resolve();
  }
});

test("Phase14 deletion rename refusal is durable until explicit latest-name review and new confirmation", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  const requests: Array<Record<string, string>> = [];
  await detail(page, id);
  await review(page);
  await page.route("**" + api + "/" + id, async (route) => {
    if (route.request().method() !== "DELETE") return route.continue();
    requests.push(route.request().postDataJSON());
    if (requests.length === 1) await rename(page, id, "Renamed before commit");
    const response = await route.fetch();
    expect(response.status()).toBe(requests.length === 1 ? 409 : 200);
    if (requests.length === 1)
      expect(await response.json()).toEqual({ detail: { code: "portfolio_confirmation_changed" } });
    await deliver(route, response);
  });
  const before = oracle(email).roots[id];
  await button(page, "Delete portfolio").click();
  await expect(page.getByText(/This portfolio's name changed/)).toBeVisible();
  expect((await books(page))[0].name).toBe("Renamed before commit");
  expect(oracle(email).roots[id].holdings).toEqual(before.holdings);
  expect(oracle(email).roots[id].trades).toEqual(before.trades);
  await button(page, "Review latest portfolio").click();
  await expect(button(page, "Remove portfolio")).toBeEnabled();
  expect(requests).toHaveLength(1);
  await review(page);
  await expect(
    page.getByRole("heading", { name: "Delete “Renamed before commit”?", exact: true }),
  ).toBeVisible();
  await button(page, "Delete portfolio").click();
  await expect(page).toHaveURL("/portfolios");
  expect(requests).toHaveLength(2);
  expect(requests[0].intent_key).not.toBe(requests[1].intent_key);
  expect(requests[1].confirmation_name).toBe("Renamed before commit");
});

test("Phase14 deletion storage failure refuses before sending and leaves finances unchanged", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  await detail(page, id);
  const before = oracle(email);
  let deletes = 0;
  page.on("request", (request) => {
    if (request.method() === "DELETE") deletes++;
  });
  await review(page);
  await page.evaluate(
    "window.__p14SetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='birja:portfolio-deletion:v1')throw new Error('Synthetic unavailable storage');return window.__p14SetItem.call(this,k,v)}",
  );
  await button(page, "Delete portfolio").click();
  await expect(page.getByRole("alert")).toContainText("No deletion was sent");
  expect(deletes).toBe(0);
  expect(oracle(email)).toEqual(before);
  await page.evaluate("Storage.prototype.setItem=window.__p14SetItem;delete window.__p14SetItem");
});

test("Phase14 deletion two-tab revocation hides committed unknown trade without replacement retry", async ({
  page,
  context,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  await rename(page, id, "Old confidential strategy");
  const sibling = await create(page, "Independent remaining strategy");
  let posts = 0;
  await page.route("**" + api + "/" + id + "/trades", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    await route.abort("failed");
  });
  await page.goto("/portfolios/" + id + "/trade/BTC");
  await page.getByLabel("Amount", { exact: true }).fill("100");
  await expect(button(page, "Confirm buy")).toBeEnabled();
  await button(page, "Confirm buy").click();
  await expect(button(page, "Check order result")).toBeVisible();
  const other = await context.newPage();
  await detail(other, id);
  await review(other);
  await button(other, "Delete portfolio").click();
  await expect(other).toHaveURL("/portfolios");
  await page.bringToFront();
  await unavailable(page);
  await expect(page.getByText(/An earlier order's result is unconfirmed/)).toBeVisible();
  await expect(page.getByText("Old confidential strategy", { exact: true })).toHaveCount(0);
  const frozen = oracle(email).roots[id];
  await page.getByLabel("Open portfolio", { exact: true }).selectOption(sibling.id);
  await buy(page, sibling.id, "10");
  expect(posts).toBe(1);
  expect(oracle(email).roots[id]).toEqual(frozen);
  await other.close();
});

test("Phase14 deletion late committed callback cannot cross owner change or same-owner new session ABA", async ({
  page,
}) => {
  test.setTimeout(90000);
  const emailA = await signInNewUser(page),
    idA = await portfolioId(page);
  const entered = latch(),
    release = latch(),
    finished = latch();
  let deletes = 0;
  await page.route("**" + api + "/" + idA, async (route) => {
    if (route.request().method() !== "DELETE") return route.continue();
    deletes++;
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    entered.resolve();
    await release.promise;
    try {
      await deliver(route, response);
    } finally {
      finished.resolve();
    }
  });
  try {
    await detail(page, idA);
    await review(page);
    await button(page, "Delete portfolio").click();
    await entered.promise;
    await logout(page);
    const emailB = await signInNewUser(page),
      idB = await portfolioId(page);
    expect(emailB).not.toBe(emailA);
    await page.goto("/portfolios/deletion");
    await expect(page.getByText("No deletion request to check.", { exact: true })).toBeVisible();
    await logout(page);
    await signIn(page, emailA);
    release.resolve();
    await finished.promise;
    await expect(page).toHaveURL("/");
    expect(await books(page)).toEqual([]);
    await page.goto("/portfolios/deletion");
    await expect(page.getByText("No deletion request to check.", { exact: true })).toBeVisible();
    expect(deletes).toBe(1);
    await logout(page);
    await signIn(page, emailB);
    expect((await books(page)).map((book) => book.id)).toEqual([idB]);
    expect((await (await page.request.get(api + "/" + idB)).json()).cash).toBe("10000.00");
  } finally {
    release.resolve();
  }
});

for (const width of [320, 375, 768, 1024, 1280, 1440]) {
  test(
    "Phase14 deletion capture actual lifecycle states " + width + "px",
    async ({ page, context }, info) => {
      test.setTimeout(240000);
      await page.setViewportSize({ width, height: 960 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      const email = await signInNewUser(page),
        id = await portfolioId(page);
      const capture = (state: string) => capturePhase14(page, info, state, width);
      await detail(page, id);
      await capture("collapsed");
      await review(page);
      await capture("confirmation");
      await expect(page.getByText(/This is your last active portfolio/)).toBeVisible();
      await capture("last-confirmation");
      await button(page, "Keep portfolio").click();
      await expect(button(page, "Remove portfolio")).toBeFocused();
      await capture("cancel");
      const longName = "<Long>&" + "🚀".repeat(53);
      expect([...longName]).toHaveLength(60);
      await rename(page, id, longName, "Description " + "🚀".repeat(988));
      await detail(page, id);
      await review(page);
      await capture("confirmation-long");
      await button(page, "Keep portfolio").click();
      const sibling = await create(page, "Independent strategy " + width);
      await buyStock(page, id);
      stockFixture("hold");
      await detail(page, id);
      await review(page);
      await capture("uncertain-stock");
      await button(page, "Keep portfolio").click();
      stockFixture("fresh");
      await page.route("**" + api + "/" + id, async (route) => {
        if (route.request().method() !== "DELETE") return route.continue();
        await rename(page, id, "Renamed capture " + width);
        const response = await route.fetch();
        expect(response.status()).toBe(409);
        await deliver(route, response);
      });
      await review(page);
      await button(page, "Delete portfolio").click();
      await expect(page.getByText(/This portfolio's name changed/)).toBeVisible();
      await capture("rename-conflict");
      await page.unroute("**" + api + "/" + id);
      await button(page, "Review latest portfolio").click();
      await expect(button(page, "Remove portfolio")).toBeEnabled();
      const observed = latch(),
        release = latch();
      await page.clock.install();
      await page.route("**" + api + "/" + id, async (route) => {
        if (route.request().method() !== "DELETE") return route.continue();
        observed.resolve();
        await release.promise;
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          headers: { "Retry-After": "30", "Cache-Control": "private, no-store" },
          body: JSON.stringify({ detail: { code: "service_unavailable" } }),
        });
      });
      await review(page);
      await button(page, "Delete portfolio").click();
      await observed.promise;
      await capture("submitting");
      release.resolve();
      await expect(
        page.getByRole("heading", { name: "Deletion result unconfirmed", exact: true }),
      ).toBeVisible();
      await capture("consistency-refusal");
      await expect(button(page, "Check deletion result")).toBeDisabled();
      await capture("retry-waiting");
      await page.unroute("**" + api + "/" + id);
      await page.clock.fastForward(31000);
      await expect(button(page, "Check deletion result")).toBeEnabled();
      const checking = latch(),
        checked = latch();
      await page.route("**" + api + "/" + id, async (route) => {
        if (route.request().method() !== "DELETE") return route.continue();
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        checking.resolve();
        await checked.promise;
        await deliver(route, response);
      });
      await button(page, "Check deletion result").click();
      await checking.promise;
      await capture("checking");
      checked.resolve();
      await expect(page).toHaveURL("/portfolios");
      await expect(page.getByRole("link", { name: sibling.name, exact: true })).toBeVisible();
      await capture("confirmed-overview");
      await page.unroute("**" + api + "/" + id);
      await page.route("**" + api + "/overview", (route) => route.abort("failed"));
      await page.clock.fastForward(31_000);
      await expect(page.getByRole("alert")).toContainText("Couldn't refresh");
      await capture("discovery-error");
      await page.unroute("**" + api + "/overview");
      await page.goto("/portfolios/" + id + "/history");
      await unavailable(page);
      await capture("stale-unavailable");
      const network = await create(page, "Network original " + width);
      let sends = 0;
      await page.route("**" + api + "/" + network.id, async (route) => {
        if (route.request().method() !== "DELETE") return route.continue();
        sends++;
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        if (sends === 1) await route.abort("failed");
        else await deliver(route, response);
      });
      await detail(page, network.id);
      await review(page);
      await button(page, "Delete portfolio").click();
      await expect(button(page, "Check deletion result")).toBeEnabled();
      await capture("unknown");
      await page.reload();
      await expect(button(page, "Check deletion result")).toBeEnabled();
      expect(sends).toBe(1);
      await capture("restored-unknown");
      await button(page, "Check deletion result").click();
      await expect(page).toHaveURL("/portfolios");
      expect(sends).toBe(2);
      await page.unroute("**" + api + "/" + network.id);
      const unknownStatuses: number[] = [];
      await page.route("**" + api + "/" + sibling.id + "/trades", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        const response = await route.fetch();
        if (response.status() === 409) {
          expect((await response.json()).detail.code).toBe("price_changed");
          await deliver(route, response);
          unknownStatuses.push(409);
          return;
        }
        expect(response.status()).toBe(201);
        await route.abort("failed");
        unknownStatuses.push(201);
      });
      await page.goto("/portfolios/" + sibling.id + "/trade/BTC");
      await page.getByLabel("Amount", { exact: true }).fill("10");
      for (let attempt = 0; attempt < 4; attempt++) {
        await expect(button(page, "Confirm buy")).toBeEnabled();
        await button(page, "Confirm buy").click();
        await expect.poll(() => unknownStatuses.length).toBe(attempt + 1);
        if (unknownStatuses.at(-1) === 201) break;
      }
      expect(unknownStatuses.at(-1)).toBe(201);
      await expect(button(page, "Check order result")).toBeVisible();
      const other = await context.newPage();
      await detail(other, sibling.id);
      await review(other);
      await button(other, "Delete portfolio").click();
      await expect(other).toHaveURL("/portfolios");
      await page.bringToFront();
      await unavailable(page);
      await expect(page.getByText(/An earlier order's result is unconfirmed/)).toBeVisible();
      await capture("cross-tab");
      await capture("stale-unresolved-order");
      await other.close();
      await page.goto("/portfolios");
      await expect(
        page.getByRole("heading", { name: "No portfolios yet", exact: true }),
      ).toBeVisible();
      await capture("empty");
      expect(await books(page)).toEqual([]);
      const frozen = oracle(email);
      expect(
        Object.values(frozen.roots).every(
          (book) => (book.portfolio_lifecycle_closures as string[]).length === 1,
        ),
      ).toBe(true);
    },
  );
}
