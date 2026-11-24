import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";
import { portfolioId, signInNewUser } from "./helpers.js";
import { stockFixture } from "./stock-trade-fixtures.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
const quotePath = /^\/api\/v2\/stock-catalog\/([1-9]\d*)\/quote$/;
const searchPath = "/api/v1/stock-catalog/search";
const quartz = "Quartz Fixture International Research and Materials Holdings";

type Listing = { catalog_id: string; listing_version: string; company_name: string; state: string };

function catalogFixture(
  operation: "catalog-first" | "catalog-reuse" | "catalog-outage" | "catalog-observed",
) {
  expect(process.env.COMPOSE_PROJECT_NAME).toBe("birja-phase09-e2e-test");
  return execFileSync(
    "docker",
    ["compose", "exec", "-T", "backend", "python", "/e2e/stock-trade-fixture.py", operation],
    { cwd: root, encoding: "utf8", timeout: 20000 },
  );
}

function observedQuotes() {
  return JSON.parse(catalogFixture("catalog-observed")) as string[][];
}

async function openStocks(page: Page) {
  await signInNewUser(page);
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await expect(stock(page, /AAPL/)).toBeVisible();
}

function stock(page: Page, name: RegExp) {
  return page.getByRole("list", { name: "US stocks", exact: true }).getByRole("button", { name });
}

async function searchFor(page: Page, text: string) {
  const result = page.waitForResponse((r) => {
    const url = new URL(r.url());
    return url.pathname === searchPath && url.searchParams.get("q") === text;
  });
  await page.getByRole("searchbox", { name: "Search stocks" }).fill(text);
  const response = await result;
  expect(response.status()).toBe(200);
  return (await response.json()).items as Listing[];
}

function selectedQuote(page: Page) {
  return page.waitForResponse(
    (r) => r.request().method() === "POST" && quotePath.test(new URL(r.url()).pathname),
  );
}

function financialWrites(page: Page) {
  const writes: string[] = [];
  page.on("request", (req) => {
    const path = new URL(req.url()).pathname;
    if (req.method() === "POST" && /\/(stock-trades|trades)(\/|$)/.test(path)) writes.push(path);
  });
  return writes;
}

async function addPortfolio(page: Page) {
  await page.request.get("/api/v1/auth/csrf");
  const csrf = (await page.context().cookies()).find((cookie) => cookie.name === "bj_csrf");
  if (!csrf) throw new Error("Expected authenticated portfolio setup");
  const created = await page.request.post("/api/v2/portfolios", {
    headers: { "X-CSRF-Token": csrf.value, "Idempotency-Key": crypto.randomUUID() },
    data: { name: "Catalog browser proof", description: "" },
  });
  expect(created.status()).toBe(201);
  return (await created.json()).id as string;
}

async function noOverflow(page: Page) {
  // Half a desktop layout viewport is a supplementary check for 200% reflow.
  await expect
    .poll(() =>
      page.evaluate<number>(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth",
      ),
    )
    .toBeLessThanOrEqual(1);
}

test.beforeEach(() => {
  stockFixture("fresh");
  catalogFixture("catalog-first");
});

test("catalog searches names, classes and aliases and prices only a keyboard selection", async ({
  page,
}) => {
  test.setTimeout(60000);
  await openStocks(page);
  await searchFor(page, "Quartz Fixture");
  await expect(stock(page, /FQXA · NASDAQ · Class A/)).toBeVisible();
  await expect(stock(page, /FQXB · NASDAQ · Class B/)).toBeVisible();
  expect(observedQuotes()).toEqual([]);
  const [item] = await searchFor(page, "FQOLD");
  expect(item.company_name).toBe(quartz);
  expect(observedQuotes()).toEqual([]);

  await page.setViewportSize({ width: 390, height: 844 });
  const row = stock(page, /FQXA/);
  await row.focus();
  await expect(row).toBeFocused();
  await noOverflow(page);
  const displayed = selectedQuote(page);
  await row.press("Enter");
  const response = await displayed;
  expect(response.status()).toBe(200);
  const quote = await response.json();
  expect(quote.listing).toMatchObject(item);
  expect(quote.quote).toMatchObject({ mid: "18.00000000", feed: "iex" });
  await expect(page.getByRole("heading", { name: quartz, exact: true })).toBeFocused();
  await expect(page.getByText("$18.00", { exact: true })).toBeVisible();
  expect(observedQuotes()).toEqual([["FQXA"]]);
  await noOverflow(page);

  await page.getByRole("button", { name: "All assets" }).click();
  await expect(row).toBeFocused();
  await expect(page.getByRole("searchbox", { name: "Search stocks" })).toHaveValue("FQOLD");
  await page.setViewportSize({ width: 640, height: 500 });
  await noOverflow(page);
});

test("catalog preserves a permitted closed mark in the selected owned portfolio", async ({
  page,
}) => {
  test.setTimeout(60000);
  const writes = financialWrites(page);
  await openStocks(page);
  const original = await portfolioId(page);
  const owned = await addPortfolio(page);
  const [item] = await searchFor(page, "FQXA");
  const displayed = selectedQuote(page);
  await stock(page, /FQXA/).click();
  expect((await displayed).status()).toBe(200);
  await expect(page.getByText("$18.00", { exact: true })).toBeVisible();
  const link = page.getByRole("link", { name: "View details FQXA" });
  await expect(link).toHaveAttribute("href", new RegExp("/trade/catalog/" + item.catalog_id + "$"));
  await link.click();
  await page.getByRole("combobox", { name: "Trading portfolio" }).selectOption(owned);
  await expect(page).toHaveURL("/portfolios/" + owned + "/trade/catalog/" + item.catalog_id);
  await expect(page.getByRole("heading", { name: quartz, level: 1 })).toBeVisible();
  await expect(page.getByText("$18.00", { exact: true })).toBeVisible();
  await expect(page.getByText("Orders aren't available for this stock yet.")).toBeVisible();

  stockFixture("close");
  await page.reload();
  await expect(page.getByText(/^Market closed\./)).toBeVisible();
  await expect(page.locator("time").filter({ hasText: /^Opens in / })).toBeVisible();
  await expect(page.getByText("$18.00", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Confirm|Preview/ })).toHaveCount(0);
  await page.getByRole("combobox", { name: "Trading portfolio" }).selectOption(original);
  await expect(page).toHaveURL("/portfolios/" + original + "/trade/catalog/" + item.catalog_id);
  await expect(page.getByText("$18.00", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 640, height: 500 });
  await noOverflow(page);
  expect(observedQuotes()).toEqual([["FQXA"]]);
  expect(writes).toEqual([]);
});

test("catalog rejects stale selection after ticker reuse and leaves the old identity read-only", async ({
  page,
}) => {
  test.setTimeout(60000);
  const writes = financialWrites(page);
  await openStocks(page);
  const owned = await portfolioId(page);
  const [original] = await searchFor(page, "FQX");
  expect(original.company_name).toBe("Original Fixture");
  await expect(stock(page, /Original Fixture/)).toBeVisible();
  catalogFixture("catalog-reuse");
  const stale = selectedQuote(page);
  await stock(page, /Original Fixture/).click();
  expect((await stale).status()).toBe(409);
  expect(observedQuotes()).toEqual([]);
  await page.goto("/portfolios/" + owned + "/trade/catalog/" + original.catalog_id);
  await expect(page.getByRole("heading", { name: "Original Fixture", level: 1 })).toBeVisible();
  await expect(page.getByText("This listing is no longer active.")).toBeVisible();
  await expect(page.getByText("$32.00", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Confirm|Preview/ })).toHaveCount(0);
  const results = await page.request.get(searchPath + "?q=FQX");
  expect(results.status()).toBe(200);
  const [replacement] = (await results.json()).items as Listing[];
  expect(replacement.company_name).toBe("Replacement Fixture");
  expect(replacement.catalog_id).not.toBe(original.catalog_id);
  expect(writes).toEqual([]);
});

test("catalog provider outage leaves search, curated stocks and crypto available", async ({
  page,
}) => {
  test.setTimeout(60000);
  await openStocks(page);
  catalogFixture("catalog-outage");
  await searchFor(page, "FQXB");
  const displayed = selectedQuote(page);
  await stock(page, /FQXB/).click();
  const response = await displayed;
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({ reason: "source_error", quote: null });
  await expect(page.getByText("Couldn’t load this stock price.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry price" })).toBeEnabled();
  expect(observedQuotes()).toEqual([["FQXB"]]);
  await searchFor(page, "FQOLD");
  await expect(stock(page, /FQXA/)).toBeVisible();
  await page.getByRole("searchbox", { name: "Search stocks" }).clear();
  await stock(page, /AAPL/).click();
  await expect(page.getByRole("link", { name: "Trade AAPL" })).toHaveAttribute(
    "href",
    /trade\/stocks\/AAPL$/,
  );
  await page.getByRole("button", { name: "Crypto", exact: true }).click();
  await expect(page.getByRole("button", { name: /BTC/ })).toBeVisible();
  expect(observedQuotes()).toEqual([["FQXB"]]);
});
