import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { portfolioId, readCodeFromLogs, signInNewUser } from "./helpers.js";
import { stockFixture } from "./stock-trade-fixtures.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
const api = "/api/v2/portfolios";
const button = (page: Page, name: string) => page.getByRole("button", { name, exact: true });
function fixture(mode: "economic" | "inspect", email: string) {
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
        "/e2e/portfolio-browser-fixture.py",
        mode,
        email,
      ],
      { cwd: root, encoding: "utf8" },
    ),
  );
}
async function headers(page: Page) {
  await page.request.get("/api/v1/auth/csrf");
  const csrf = (await page.context().cookies()).find((c) => c.name === "bj_csrf")!;
  return { "X-CSRF-Token": csrf.value };
}
async function create(page: Page, name: string, description = "") {
  const options = {
    headers: { ...(await headers(page)), "Idempotency-Key": crypto.randomUUID() },
    data: { name, description },
  };
  let response = await page.request.post(api, options);
  // These setup calls share the runner's IP across many independent owners.
  // Respect its actual limit rather than changing application limits for CI.
  if (response.status() === 429) {
    const retryAfter = response.headers()["retry-after"];
    expect(retryAfter).toMatch(/^[1-9]\d?$/);
    expect(Number(retryAfter)).toBeLessThanOrEqual(60);
    await new Promise((resolve) => setTimeout(resolve, (Number(retryAfter) + 1) * 1000));
    response = await page.request.post(api, options);
  }
  expect(response.status()).toBe(201);
  return response.json() as Promise<{ id: string; name: string; description: string }>;
}
async function patch(page: Page, id: string, data: { name?: string; description?: string }) {
  const response = await page.request.patch(`${api}/${id}`, { headers: await headers(page), data });
  expect(response.status()).toBe(200);
  return response.json();
}
async function statement(page: Page, id: string) {
  const response = await page.request.get(`${api}/${id}`);
  expect(response.status()).toBe(200);
  return response.json();
}
async function list(page: Page) {
  const response = await page.request.get(api);
  expect(response.status()).toBe(200);
  return response.json() as Promise<Array<{ id: string; name: string }>>;
}
async function closeAllThroughApi(page: Page) {
  for (const book of await list(page)) {
    const response = await page.request.delete(`${api}/${book.id}`, {
      headers: await headers(page),
      data: {
        intent_key: crypto.randomUUID(),
        confirmation_name: book.name,
        policy_version: "freeze_at_closure_v1",
      },
    });
    expect(response.status()).toBe(200);
    expect(await response.json()).toEqual({ portfolio_id: book.id, state: "closed" });
  }
}
async function overview(page: Page) {
  await page.goto("/portfolios");
  await expect(page.getByRole("heading", { name: "Portfolios", exact: true })).toBeVisible();
  await expect(button(page, "New portfolio")).toBeVisible();
}
async function openCreate(page: Page, name: string, description = "") {
  await button(page, "New portfolio").click();
  await expect(
    page.getByLabel("Portfolio name", { exact: true }),
    JSON.stringify(
      await page.evaluate(
        `({active:document.activeElement?.tagName,id:document.activeElement?.id,alert:document.querySelector('[role="alert"]')?.textContent})`,
      ),
    ),
  ).toBeFocused();
  await page.getByLabel("Portfolio name", { exact: true }).fill(name);
  await page.getByLabel("Description (optional)").fill(description);
}
async function submitCreate(page: Page) {
  await page.locator("form").getByRole("button", { name: "Create portfolio", exact: true }).click();
}
async function signIn(page: Page, email: string) {
  await page.goto("/");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await button(page, "Send code").click();
  await page.getByLabel("6-digit code").fill(await readCodeFromLogs(email));
  await button(page, "Sign in").click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
}
async function cryptoBuy(page: Page, id: string, amount = "100") {
  await page.goto(`/portfolios/${id}/trade/BTC`);
  await page.getByLabel("Amount", { exact: true }).fill(amount);
  for (let n = 0; n < 4; n++) {
    const done = page.waitForResponse(
      (r) => r.url().endsWith(`${api}/${id}/trades`) && r.request().method() === "POST",
    );
    await expect(button(page, "Confirm buy")).toBeEnabled();
    await button(page, "Confirm buy").click();
    const response = await done;
    if (response.status() === 201) {
      await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
      return response.json();
    }
    expect((await response.json()).detail.code).toBe("price_changed");
  }
  throw new Error("No fill after bounded explicit confirmations");
}
async function stockBuy(page: Page, id: string, quantity: string) {
  await page.goto(`/portfolios/${id}/trade/stocks/AAPL`);
  await page.getByLabel("Whole-share quantity").fill(quantity);
  await button(page, "Preview trade").click();
  await expect(button(page, "Confirm buy")).toBeEnabled();
  const done = page.waitForResponse(
    (r) => r.url().endsWith(`${api}/${id}/stock-trades`) && r.request().method() === "POST",
  );
  await button(page, "Confirm buy").click();
  expect((await done).status()).toBe(201);
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
}
async function noOverflow(page: Page) {
  expect(await page.evaluate("document.documentElement.scrollWidth <= innerWidth")).toBe(true);
}

test.beforeEach(() => stockFixture("fresh"));

test("Phase13 create view edit clear and escaped astral metadata preserve immutable finances", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const initial = await portfolioId(page);
  expect((await statement(page, initial)).cash).toBe("10000.00");
  await overview(page);
  await expect(page.getByRole("link", { name: "My portfolio", exact: true })).toBeVisible();
  const name = "<Strategy>& " + "🚀".repeat(48);
  await openCreate(page, name, "Plain <script> text & \n" + "🚀".repeat(977));
  await expect(page.getByText("1000 / 1,000 characters", { exact: true })).toBeVisible();
  await submitCreate(page);
  await expect(page).toHaveURL(/\/portfolios\/\d+$/);
  const id = new URL(page.url()).pathname.split("/").at(-1)!;
  expect(id).not.toBe(initial);
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  expect((await statement(page, id)).cash).toBe("10000.00");
  const before = fixture("economic", email);
  await button(page, "Edit portfolio").click();
  await page.getByLabel("Portfolio name", { exact: true }).fill("Renamed strategy");
  await page.getByLabel("Description (optional)").fill("Edited plain text");
  await button(page, "Save changes").click();
  await expect(button(page, "Edit portfolio")).toBeFocused();
  await expect(page.getByText("Edited plain text", { exact: true })).toBeVisible();
  await button(page, "Edit portfolio").click();
  await page.getByLabel("Description (optional)").fill("");
  await button(page, "Save changes").click();
  await expect(page.getByText("No description.", { exact: true })).toHaveCount(0);
  expect(fixture("economic", email)).toEqual(before);
  await page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name: "Portfolios", exact: true })
    .click();
  await expect(page.getByRole("link", { name: "Renamed strategy", exact: true })).toBeVisible();
  expect((await list(page)).map((p) => p.id)).toEqual([initial, id]);
  await expect(page.getByRole("button", { name: /delete|reset|deposit|transfer/i })).toHaveCount(0);
});

test("Phase13 committed lost creation response reload explicitly retries identical original key at cap", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const original = await portfolioId(page);
  for (let n = 0; n < 8; n++) await create(page, `Cap book ${n}`);
  const requests: Array<{ key: string; body: string }> = [];
  let createdId = "";
  await page.route("**/api/v2/portfolios", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    requests.push({
      key: route.request().headers()["idempotency-key"],
      body: route.request().postData()!,
    });
    const response = await route.fetch();
    expect(response.status()).toBe(requests.length === 1 ? 201 : 200);
    const result = await response.json();
    if (!createdId) createdId = result.id;
    expect(result.id).toBe(createdId);
    if (requests.length === 1) await route.abort("failed");
    else await route.fulfill({ response });
  });
  await overview(page);
  await openCreate(page, "Original intent", "Preserved original description");
  await submitCreate(page);
  await expect(button(page, "Retry creation")).toBeVisible();
  expect(await list(page)).toHaveLength(10);
  const before = fixture("economic", email);
  await patch(page, createdId, { name: "Renamed committed result" });
  await page.reload();
  await expect(button(page, "Review original creation")).toBeVisible();
  expect(requests).toHaveLength(1);
  await button(page, "Review original creation").click();
  await expect(page.getByLabel("Portfolio name", { exact: true })).toHaveValue("Original intent");
  await expect(page.getByLabel("Portfolio name", { exact: true })).toHaveAttribute("readonly", "");
  await button(page, "Retry creation").click();
  await expect(page).toHaveURL(`/portfolios/${createdId}`);
  await expect(
    page.getByRole("heading", { name: "Renamed committed result", exact: true }),
  ).toBeVisible();
  expect(requests).toHaveLength(2);
  expect(requests[1]).toEqual(requests[0]);
  expect(fixture("economic", email)).toEqual(before);
  expect((await statement(page, original)).cash).toBe("10000.00");
});

test("Phase13 duplicate name and concurrent tenth-slot refusal retain draft and focus linked error", async ({
  page,
}) => {
  await signInNewUser(page);
  await overview(page);
  await openCreate(page, "MY PORTFOLIO", "Keep this draft");
  await submitCreate(page);
  const alert = page.getByRole("alert");
  await expect(alert).toBeFocused();
  await expect(alert).toContainText("You already have an active portfolio");
  await page.getByRole("link", { name: "Review portfolio name", exact: true }).press("Enter");
  await expect(page.getByLabel("Portfolio name", { exact: true })).toBeFocused();
  await expect(page.getByLabel("Description (optional)")).toHaveValue("Keep this draft");
  for (let n = 0; n < 8; n++) await create(page, `Race seed ${n}`);
  await button(page, "Discard draft").click();
  await overview(page);
  await expect(page.getByRole("link", { name: "Race seed 7", exact: true })).toBeVisible();
  await openCreate(page, "Race loser", "Retain after cap race");
  // Both real writes race while the UI still has its nine-book observation.
  const h = await headers(page);
  const winner = page.request.post(api, {
    headers: { ...h, "Idempotency-Key": crypto.randomUUID() },
    data: { name: "Race competitor", description: "" },
  });
  await submitCreate(page);
  const competitor = await winner;
  const all = await list(page);
  expect(all).toHaveLength(10);
  if (competitor.status() === 201) {
    await expect(page.getByRole("alert")).toContainText("10 active portfolios");
    await expect(page.getByLabel("Portfolio name", { exact: true })).toHaveValue("Race loser");
    await expect(page.getByLabel("Description (optional)")).toHaveValue("Retain after cap race");
  } else {
    expect(competitor.status()).toBe(409);
    expect((await competitor.json()).detail.code).toBe("portfolio_limit");
    await expect(page).toHaveURL(/\/portfolios\/\d+$/);
  }
  await overview(page);
  await expect(button(page, "New portfolio")).toBeDisabled();
});

test("Phase13 zero-book returning identity gets no implicit grant and closed name frees new identity", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const old = await portfolioId(page);
  await closeAllThroughApi(page);
  const before = fixture("economic", email);
  await overview(page);
  await expect(page.getByRole("heading", { name: "No portfolios yet", exact: true })).toBeVisible();
  await button(page, "Sign out").click();
  await signIn(page, email);
  expect(await list(page)).toEqual([]);
  expect(fixture("economic", email)).toEqual(before);
  await overview(page);
  await openCreate(page, "My portfolio");
  await submitCreate(page);
  await expect(page).toHaveURL(/\/portfolios\/\d+$/);
  const replacement = (await list(page))[0].id;
  expect(replacement).not.toBe(old);
  expect((await statement(page, replacement)).cash).toBe("10000.00");
  expect((await page.request.get(`${api}/${old}`)).status()).toBe(404);
});

test("Phase13 competing canonical name write refuses UI draft without a grant", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  await overview(page);
  await openCreate(page, "Name race", "Draft survives competing commit");
  let raced = false;
  await page.route("**/api/v2/portfolios", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    expect(raced).toBe(false);
    raced = true;
    await create(page, "NAME RACE");
    const before = fixture("economic", email);
    const response = await route.fetch();
    expect(response.status()).toBe(409);
    expect((await response.json()).detail.code).toBe("name_taken");
    expect(fixture("economic", email)).toEqual(before);
    await route.fulfill({ response });
  });
  await submitCreate(page);
  await expect(page.getByRole("alert")).toBeFocused();
  await expect(page.getByLabel("Description (optional)")).toHaveValue(
    "Draft survives competing commit",
  );
  expect(await list(page)).toHaveLength(2);
});

test("Phase13 closed committed original creation cannot be recreated by its lost key", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  let posts = 0;
  await page.route("**/api/v2/portfolios", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    const response = await route.fetch();
    if (posts === 1) {
      expect(response.status()).toBe(201);
      await route.abort("failed");
    } else {
      expect(response.status()).toBe(404);
      await route.fulfill({ response });
    }
  });
  await overview(page);
  await openCreate(page, "Closed original");
  await submitCreate(page);
  await expect(button(page, "Retry creation")).toBeVisible();
  await closeAllThroughApi(page);
  const before = fixture("economic", email);
  await button(page, "Retry creation").click();
  await expect(page.getByRole("alert")).toContainText("The original portfolio is unavailable");
  expect(posts).toBe(2);
  expect(await list(page)).toEqual([]);
  expect(fixture("economic", email)).toEqual(before);
});

test("Phase13 a late committed creation callback cannot navigate away from another explicit root", async ({
  page,
}) => {
  await signInNewUser(page);
  const original = await portfolioId(page);
  let observed!: () => void, release!: () => void;
  const committed = new Promise<void>((resolve) => {
    observed = resolve;
  });
  const wait = new Promise<void>((resolve) => {
    release = resolve;
  });
  let id = "";
  await page.route("**/api/v2/portfolios", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    id = (await response.json()).id;
    observed();
    await wait;
    await route.fulfill({ response }).catch(() => {});
  });
  await overview(page);
  await openCreate(page, "Late created identity");
  await submitCreate(page);
  await committed;
  await page.getByRole("link", { name: "My portfolio", exact: true }).click();
  await expect(page).toHaveURL(`/portfolios/${original}`);
  release();
  await expect(page.getByRole("heading", { name: "My portfolio", exact: true })).toBeVisible();
  await expect.poll(async () => (await list(page)).length).toBe(2);
  await expect(page).toHaveURL(`/portfolios/${original}`);
  expect((await statement(page, id)).cash).toBe("10000.00");
});

test("Phase13 API-created same-asset strategies keep cash basis history and explicit switch Back separate", async ({
  page,
}) => {
  await signInNewUser(page);
  const a = await create(page, "Crypto and stock A");
  const b = await create(page, "Crypto and stock B");
  await cryptoBuy(page, a.id, "100");
  await stockBuy(page, a.id, "2");
  await cryptoBuy(page, b.id, "200");
  await stockBuy(page, b.id, "1");
  const first = await statement(page, a.id),
    second = await statement(page, b.id);
  expect(first.cash).toBe("9696.00");
  expect(second.cash).toBe("9698.00");
  expect(first.starting_cash).toBe("10000.00");
  expect(second.starting_cash).toBe("10000.00");
  expect(first.holdings.find((h: { symbol: string }) => h.symbol === "AAPL").quantity).toBe(
    "2.00000000",
  );
  expect(second.holdings.find((h: { symbol: string }) => h.symbol === "AAPL").quantity).toBe(
    "1.00000000",
  );
  expect(first.holdings.find((h: { symbol: string }) => h.symbol === "BTC").cost_basis).toBe(
    "100.00",
  );
  expect(second.holdings.find((h: { symbol: string }) => h.symbol === "BTC").cost_basis).toBe(
    "200.00",
  );
  await page.goto(`/portfolios/${a.id}`);
  await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText("$9,696.00");
  await page.getByLabel("Open portfolio", { exact: true }).selectOption(b.id);
  await expect(page).toHaveURL(`/portfolios/${b.id}`);
  await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
  await expect(page.getByRole("region", { name: "Cash", exact: true })).toContainText("$9,698.00");
  await page.goBack();
  await expect(page).toHaveURL(`/portfolios/${a.id}`);
  for (const id of [a.id, b.id]) {
    const history = await page.request.get(`${api}/${id}/event-history?limit=1`);
    const data = await history.json();
    expect(data.items).toHaveLength(1);
    expect(data.next_cursor).toBeTruthy();
    const crossed = await page.request.get(
      `${api}/${id === a.id ? b.id : a.id}/event-history?limit=1&cursor=${encodeURIComponent(data.next_cursor)}`,
    );
    expect(crossed.status()).toBe(422);
  }
});

test("Phase13 two real tabs preserve dirty metadata and require latest-authoritative review", async ({
  page,
  context,
}) => {
  await signInNewUser(page);
  const id = await portfolioId(page);
  await page.goto(`/portfolios/${id}`);
  await button(page, "Edit portfolio").click();
  await page.getByLabel("Portfolio name", { exact: true }).fill("Private dirty draft");
  const other = await context.newPage();
  await other.goto(`/portfolios/${id}`);
  await button(other, "Edit portfolio").click();
  await other.getByLabel("Portfolio name", { exact: true }).fill("Other tab authoritative");
  await button(other, "Save changes").click();
  await expect(button(other, "Edit portfolio")).toBeVisible();
  await page.bringToFront();
  await expect(
    page.getByText(
      "This portfolio changed. Your draft is kept below. Review the latest details before saving.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(page.getByLabel("Portfolio name", { exact: true })).toHaveValue(
    "Private dirty draft",
  );
  await expect(
    page.getByText("Latest portfolio name: Other tab authoritative", { exact: true }),
  ).toBeVisible();
  await expect(button(page, "Save changes")).toBeDisabled();
  await button(page, "I have reviewed the latest details").click();
  await expect(button(page, "Save changes")).toBeEnabled();
  await button(page, "Discard changes").click();
  await expect(
    page.getByRole("heading", { name: "Other tab authoritative", exact: true }),
  ).toBeVisible();
  await other.close();
});

test("Phase13 renewal and logout cannot replay private unresolved creation into another owner", async ({
  page,
  context,
}) => {
  const email = await signInNewUser(page);
  const id = await portfolioId(page);
  const before = fixture("economic", email);
  await context.clearCookies({ name: "bj_access" });
  await overview(page);
  expect(fixture("economic", email)).toEqual(before);
  let posts = 0;
  await page.route("**/api/v2/portfolios", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    const result = await route.fetch();
    expect(result.status()).toBe(201);
    await route.abort("failed");
  });
  await openCreate(page, "Owner private unresolved");
  await submitCreate(page);
  await expect(button(page, "Retry creation")).toBeVisible();
  await button(page, "Sign out").click();
  await signInNewUser(page);
  await overview(page);
  await expect(button(page, "Review original creation")).toHaveCount(0);
  await expect(page.getByText("Owner private unresolved", { exact: true })).toHaveCount(0);
  expect(posts).toBe(1);
  expect((await page.request.get(`${api}/${id}`)).status()).toBe(404);
});

test("Phase13 late actual old-root response cannot publish over explicit newly created strategy", async ({
  page,
}) => {
  await signInNewUser(page);
  const a = await create(page, "Delayed root"),
    b = await create(page, "Current root");
  let release!: () => void, observed!: () => void;
  const waiting = new Promise<void>((resolve) => {
    release = resolve;
  });
  const started = new Promise<void>((resolve) => {
    observed = resolve;
  });
  await page.route(`**${api}/${a.id}`, async (route) => {
    const response = await route.fetch();
    observed();
    await waiting;
    await route.fulfill({ response }).catch(() => {});
  });
  await page.goto(`/portfolios/${a.id}`);
  await started;
  await page.getByLabel("Open portfolio", { exact: true }).selectOption(b.id);
  await expect(page).toHaveURL(`/portfolios/${b.id}`);
  release();
  await expect(page.getByRole("heading", { name: "Current root", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Delayed root", exact: true })).toHaveCount(0);
});

test("Phase13 renamed original unknown trade recovers identical payload without sibling debit", async ({
  page,
}) => {
  await signInNewUser(page);
  const a = await create(page, "Original order label"),
    b = await create(page, "Unspent sibling");
  const attempts: string[] = [];
  await page.route(`**${api}/${a.id}/trades`, async (route) => {
    const response = await route.fetch();
    if (response.status() === 409) return route.fulfill({ response });
    expect(response.status()).toBe(attempts.length ? 200 : 201);
    attempts.push(route.request().postData()!);
    if (attempts.length === 1) await route.abort("failed");
    else await route.fulfill({ response });
  });
  await page.goto(`/portfolios/${a.id}/trade/BTC`);
  await page.getByLabel("Amount", { exact: true }).fill("100");
  for (let n = 0; n < 4 && attempts.length === 0; n++) {
    const response = page
      .waitForResponse((r) => r.url().endsWith(`${api}/${a.id}/trades`))
      .catch(() => null);
    await expect(button(page, "Confirm buy")).toBeEnabled();
    await button(page, "Confirm buy").click();
    await expect
      .poll(
        async () =>
          attempts.length ||
          (await page.getByText("Price updated. Please review again.", { exact: true }).count()),
      )
      .toBeGreaterThan(0);
    if (!attempts.length) await response;
  }
  await expect(button(page, "Check order result")).toBeVisible();
  await patch(page, a.id, { name: "Renamed current order root" });
  await page.getByLabel("Open portfolio", { exact: true }).selectOption(b.id);
  await page.getByRole("link", { name: "Markets", exact: true }).click();
  await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
  await page.getByRole("link", { name: "Trade BTC", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/portfolios/${b.id}/trade/BTC$`));
  await expect(button(page, "Check order result")).toHaveCount(0);
  await page.getByLabel("Open portfolio", { exact: true }).selectOption(a.id);
  await page.getByRole("link", { name: "Markets", exact: true }).click();
  await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
  await page.getByRole("link", { name: "Trade BTC", exact: true }).click();
  await expect(button(page, "Check order result")).toBeVisible();
  await button(page, "Check order result").click();
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toBe(attempts[0]);
  expect((await statement(page, a.id)).cash).toBe("9900.00");
  expect((await statement(page, b.id)).cash).toBe("10000.00");
});

test("Phase13 real incomplete strategy and failed refresh preserve sibling and source-time semantics", async ({
  page,
}) => {
  await signInNewUser(page);
  const a = await create(page, "Mixed unsafe marks"),
    b = await create(page, "Cash remains complete");
  await cryptoBuy(page, a.id);
  await stockBuy(page, a.id, "1");
  stockFixture("hold");
  const first = await statement(page, a.id),
    second = await statement(page, b.id);
  expect(first.valuation_complete).toBe(false);
  expect(first.total_value).toBeNull();
  expect(first.total_pl).toBeNull();
  expect(first.unvalued_holding_count).toBe(1);
  expect(second.valuation_complete).toBe(true);
  const rows = await (await page.request.get(`${api}/overview`)).json();
  const row = rows.find((r: { id: string }) => r.id === a.id);
  for (const key of [
    "cash",
    "known_value",
    "total_value",
    "total_pl",
    "valuation_complete",
    "unvalued_holding_count",
    "prices_as_of",
  ])
    expect(row[key]).toEqual(first[key]);
  await page.clock.install();
  await overview(page);
  await expect(page.getByText(/Known value: .* incomplete/)).toBeVisible();
  await expect(page.getByText("Return unavailable", { exact: true })).toBeVisible();
  await page.route(`**${api}/overview`, (route) => route.abort("failed"));
  await page.clock.fastForward(31_000);
  await expect(page.getByRole("alert")).toContainText("Couldn't refresh your portfolios");
  await expect(
    page.getByRole("link", { name: "Cash remains complete", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Known value: .* incomplete/)).toBeVisible();
  await noOverflow(page);
});

test("Phase13 failed refresh suppresses expired stock proof while cash sibling remains usable", async ({
  page,
}) => {
  await signInNewUser(page);
  const a = await create(page, "Expiring stock evidence"),
    b = await create(page, "Unaffected cash");
  await stockBuy(page, a.id, "1");
  const value = await statement(page, a.id);
  expect(value.valuation_complete).toBe(true);
  const mark = value.holdings[0].stock_mark;
  expect(mark.mark_mode).toBe("fresh");
  expect(Date.parse(mark.valid_until)).toBeGreaterThan(Date.now());
  await page.clock.install();
  await overview(page);
  await page.route(`**${api}/overview`, (route) => route.abort("failed"));
  await page.clock.fastForward(31_000);
  await expect(page.getByRole("alert")).toContainText("Couldn't refresh");
  await page.clock.fastForward(Math.max(1, Date.parse(mark.valid_until) - Date.now() + 2000));
  await expect(page.getByText("Return unavailable", { exact: true })).toBeVisible();
  const cards = page.getByRole("list", { name: "Portfolios", exact: true }).getByRole("listitem");
  const expired = cards.filter({
    has: page.getByRole("link", { name: "Expiring stock evidence", exact: true }),
  });
  await expect(expired.getByText("Value unavailable — refresh required")).toBeVisible();
  await expect(expired.getByText("$9,898.00", { exact: true })).toHaveCount(1);
  await expect(expired.getByText("$9,999.00", { exact: true })).toHaveCount(0);
  const cashSibling = cards.filter({
    has: page.getByRole("link", { name: "Unaffected cash", exact: true }),
  });
  await expect(cashSibling.getByText("$10,000.00", { exact: true })).toHaveCount(2);
  await expect(page.getByRole("link", { name: "Unaffected cash", exact: true })).toHaveAttribute(
    "href",
    `/portfolios/${b.id}`,
  );
});

async function reviewedLayout(page: Page, state: string, width: number) {
  const dimensions: Record<string, number> = {};
  const navigation = page.getByRole("region", { name: "Portfolio navigation", exact: true });
  if (width < 768 && (await navigation.isVisible())) {
    const select = navigation.getByLabel("Open portfolio", { exact: true });
    const [regionBox, fieldBox] = await Promise.all([
      navigation.boundingBox(),
      select.boundingBox(),
    ]);
    expect(fieldBox!.width).toBeGreaterThanOrEqual(regionBox!.width - 1);
    expect(fieldBox!.height).toBeGreaterThanOrEqual(48);
    await expect(navigation.getByRole("button")).toHaveCount(0);
    await expect(navigation.getByRole("link")).toHaveCount(0);
    Object.assign(dimensions, {
      select_width: fieldBox!.width,
      select_height: fieldBox!.height,
    });
  }
  if (state === "unknown") {
    await expect(
      page.getByText(
        "We couldn't confirm whether your portfolio was created. Retry this creation to check its original result.",
        { exact: true },
      ),
    ).toHaveCount(1);
  }
  if (state === "keyboard-error-focus" || state === "unknown") {
    const icon = page.getByRole("alert").locator("svg");
    const box = (await icon.boundingBox())!;
    expect(box.width).toBe(20);
    expect(box.height).toBe(20);
    Object.assign(dimensions, { error_icon_width: box.width, error_icon_height: box.height });
  }
  return dimensions;
}

/** Freeze only the actual public DOM/styles/fonts; no cookies, storage or scripts. */
async function capture(page: Page, info: TestInfo, state: string, width: number) {
  await noOverflow(page);
  const layout = await reviewedLayout(page, state, width);
  const name = `phase13-${state}-${width}`;
  const destination = process.env.BIRJA_PHASE12_REVIEW_DIR;
  const path = (suffix: string) =>
    destination ? `${destination}/${name}.${suffix}` : info.outputPath(`${name}.${suffix}`);
  await page.screenshot({ path: path("png"), fullPage: true });
  let css = await page.evaluate<string>(
    "Array.from(document.styleSheets).flatMap(s=>Array.from(s.cssRules,r=>r.cssText)).join('\\n')",
  );
  for (const match of [...css.matchAll(/url\((["']?)([^)"']+)\1\)/g)]) {
    if (match[2].startsWith("data:")) continue;
    const url = new URL(match[2], page.url());
    expect(url.origin).toBe(new URL(page.url()).origin);
    expect(url.pathname).toMatch(/\.(woff2?|ttf|otf)$/);
    const response = await page.request.get(url.href);
    expect(response.ok()).toBe(true);
    css = css.replaceAll(
      match[0],
      `url("data:font/woff2;base64,${(await response.body()).toString("base64")}")`,
    );
  }
  const browser = page.context().browser()!;
  const render = () =>
    page.evaluate<string>(`(styles => {
    const d=document.cloneNode(true);
    d.querySelectorAll('script,link,style,iframe').forEach(n=>n.remove());
    for(const tag of ['input','textarea','select']) {
      const live=document.querySelectorAll(tag);
      d.querySelectorAll(tag).forEach((n,i)=>{
        if(tag==='textarea')n.textContent=live[i].value;
        else if(tag==='select')n.querySelectorAll('option').forEach(o=>o.toggleAttribute('selected',o.value===live[i].value));
        else n.setAttribute('value',live[i].value);
        n.setAttribute('readonly','');
      });
    }
    d.querySelectorAll('form').forEach(n=>{const v=d.createElement('div');v.className=n.className;v.replaceChildren(...n.childNodes);n.replaceWith(v);});
    d.querySelectorAll('a').forEach(n=>n.setAttribute('href','#'));
    d.querySelectorAll('button').forEach(n=>n.setAttribute('type','button'));
    d.querySelectorAll('*').forEach(n=>Array.from(n.attributes).filter(a=>a.name.startsWith('on')).forEach(a=>n.removeAttribute(a.name)));
    const s=d.createElement('style');s.textContent=styles;d.head.append(s);
    const c=d.createElement('meta');c.httpEquiv='Content-Security-Policy';c.content="default-src 'none';style-src 'unsafe-inline';font-src data:;img-src data:;base-uri 'none';form-action 'none'";d.head.prepend(c);
    return '<!doctype html>\\n'+d.documentElement.outerHTML;
  })(${JSON.stringify(css)})`);
  let rendered = await render();
  if (width >= 768) {
    const viewport = page.viewportSize()!;
    await page.setViewportSize({ width: Math.floor(width / 2), height: 480 });
    await expect.poll(() => page.evaluate("matchMedia('(min-width: 768px)').matches")).toBe(false);
    await noOverflow(page);
    await reviewedLayout(page, state, Math.floor(width / 2));
    const narrow = await render();
    await page.screenshot({ path: path("reflow.png"), fullPage: true });
    await page.setViewportSize(viewport);
    rendered = await page.evaluate<string>(`(([wide,narrow])=>{
      const parser=new DOMParser(),d=parser.parseFromString(wide,'text/html');
      const small=parser.parseFromString(narrow,'text/html');
      function variant(doc,mode){
        const wrapper=d.createElement('div');wrapper.setAttribute('data-review-mode',mode);
        const ids=new Map();
        doc.body.querySelectorAll('[id]').forEach(n=>{const old=n.id; n.id=mode+'-'+old;ids.set(old,n.id);});
        doc.body.querySelectorAll('*').forEach(n=>{
          for(const attribute of ['for','aria-describedby','aria-labelledby','aria-controls']){
            const value=n.getAttribute(attribute);if(value)n.setAttribute(attribute,value.split(' ').map(v=>ids.get(v)||v).join(' '));
          }
        });
        wrapper.replaceChildren(...doc.body.childNodes);return wrapper;
      }
      const large=variant(d,'wide'),compact=variant(small,'narrow');
      d.body.replaceChildren(large,compact);
      const style=d.createElement('style');style.textContent='[data-review-mode="narrow"]{display:none}@media(max-width:767px){[data-review-mode="wide"]{display:none}[data-review-mode="narrow"]{display:block}}';d.head.append(style);
      return '<!doctype html>\\n'+d.documentElement.outerHTML;
    })(${JSON.stringify([rendered, narrow])})`);
  }
  const metadata = {
    phase: 13,
    state,
    width,
    browser: browser.browserType().name(),
    version: browser.version(),
    synthetic: true,
    source: process.env.BIRJA_PHASE12_SOURCE,
    native_200_percent_verified: false,
    layout,
    artifacts: {
      html: name + ".html",
      png: name + ".png",
      trace: name + ".trace.json",
      ...(width >= 768 ? { reflow_png: name + ".reflow.png" } : {}),
    },
    scope: createHash("sha256")
      .update(JSON.stringify(await (await page.request.get("/api/v2/me")).json()))
      .digest("hex"),
    trace: await page.evaluate<Array<{ path: string; start: number; duration: number }>>(
      `performance.getEntriesByType('resource').map(e=>({path:new URL(e.name).pathname,start:e.startTime,duration:e.duration}))`,
    ),
  };
  const html = rendered.replace(
    "</head>",
    `<meta name="birja-evidence" content="${JSON.stringify(metadata).replaceAll('"', "&quot;")}"></head>`,
  );
  expect(html).not.toMatch(/<script|<form|\s(?:src|href|action)=["']https?:/);
  expect(html).not.toContain("bj_access");
  await writeFile(path("html"), html, { flag: "wx" });
}

for (const width of [320, 375, 768, 1024, 1280, 1440]) {
  test(`Phase13 capture actual management states ${width}px`, async ({ page, context }, info) => {
    test.setTimeout(150_000);
    await page.setViewportSize({ width, height: 960 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await signInNewUser(page);
    await portfolioId(page);
    // Capture a genuinely empty returning owner BEFORE opening any stock
    // holding. Never fabricate a terminal stock closure without its lineage.
    await closeAllThroughApi(page);
    await overview(page);
    await expect(
      page.getByRole("heading", { name: "No portfolios yet", exact: true }),
    ).toBeVisible();
    await capture(page, info, "empty", width);
    const id = (await create(page, "My portfolio")).id;
    await overview(page);
    await capture(page, info, "overview", width);
    const longName = "<Long>&" + "🚀".repeat(52);
    await openCreate(page, longName, "Escaped <b>plain text</b>\n" + "🚀".repeat(950));
    await capture(page, info, "create-long-astral", width);
    await page.getByLabel("Portfolio name", { exact: true }).fill("MY PORTFOLIO");
    await submitCreate(page);
    await expect(page.getByRole("alert")).toBeFocused();
    await page.getByRole("alert").scrollIntoViewIfNeeded();
    await capture(page, info, "keyboard-error-focus", width);
    await page.getByRole("link", { name: "Review portfolio name", exact: true }).press("Enter");
    await expect(page.getByLabel("Portfolio name", { exact: true })).toBeFocused();
    await page.getByLabel("Portfolio name", { exact: true }).fill(longName);
    let lost = false;
    await page.route("**/api/v2/portfolios", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      const response = await route.fetch();
      if (!lost) {
        expect(response.status()).toBe(201);
        lost = true;
        await route.abort("failed");
      } else await route.fulfill({ response });
    });
    await submitCreate(page);
    await expect(button(page, "Retry creation")).toBeVisible();
    await capture(page, info, "unknown", width);
    await button(page, "Retry creation").click();
    await expect(page).toHaveURL(/\/portfolios\/\d+$/);
    const sibling = (await list(page)).find((r) => r.id !== id)!.id;
    await button(page, "Edit portfolio").click();
    await page.getByLabel("Description (optional)").fill("Dirty " + "🚀".repeat(990));
    await capture(page, info, "edit", width);
    const other = await context.newPage();
    await other.goto(`/portfolios/${sibling}`);
    await button(other, "Edit portfolio").click();
    await other.getByLabel("Description (optional)").fill("Other tab latest description");
    await button(other, "Save changes").click();
    await expect(button(other, "Edit portfolio")).toBeVisible();
    await page.bringToFront();
    await expect(button(page, "I have reviewed the latest details")).toBeVisible();
    await capture(page, info, "stale-draft", width);
    await other.close();
    await button(page, "Discard changes").click();
    await page.getByLabel("Open portfolio", { exact: true }).selectOption(id);
    await capture(page, info, "switch", width);
    await stockBuy(page, id, "1");
    stockFixture("hold");
    await page.clock.install();
    await overview(page);
    await expect(page.getByText(/Known value: .* incomplete/)).toBeVisible();
    await capture(page, info, "incomplete", width);
    await page.route(`**${api}/overview`, (route) => route.abort("failed"));
    await page.clock.fastForward(31_000);
    await expect(page.getByRole("alert")).toContainText("Couldn't refresh");
    await capture(page, info, "failed-refresh", width);
    await page.unroute(`**${api}/overview`);
    for (let n = 0; n < 8; n++) await create(page, `Capture cap ${width} ${n}`);
    await overview(page);
    await expect(page.getByText("You have 10 active portfolios.", { exact: false })).toBeVisible();
    await capture(page, info, "cap", width);
    await page.route(`**${api}/overview`, (route) => route.abort("failed"));
    await page.reload();
    await expect(page.getByRole("alert")).toContainText("Can't load your portfolios");
    await capture(page, info, "error", width);
  });
}
