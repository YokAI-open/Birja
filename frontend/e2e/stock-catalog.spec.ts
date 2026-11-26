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
  operation:
    | "catalog-first"
    | "catalog-reuse"
    | "catalog-traded-reuse"
    | "catalog-outage"
    | "catalog-observed"
    | "catalog-finance"
    | "catalog-finance-mixed"
    | "catalog-cold-close"
    | "catalog-expire-mark"
    | "catalog-reprice"
    | "catalog-halt"
    | "catalog-resume"
    | "catalog-stale"
    | "catalog-hold"
    | "catalog-dividend"
    | "catalog-split",
  openingOwner?: string,
) {
  expect(process.env.COMPOSE_PROJECT_NAME).toBe("birja-phase09-e2e-test");
  return execFileSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "backend",
      "python",
      "/e2e/stock-trade-fixture.py",
      operation,
      ...(openingOwner === undefined ? [] : [openingOwner]),
    ],
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
    if (
      req.method() === "POST" &&
      (/\/(stock-trades|trades)(\/|$)/.test(path) ||
        /\/portfolios\/\d+\/stock-catalog\/\d+\/(preview|confirm)$/.test(path))
    ) {
      writes.push(path);
    }
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
}, testInfo) => {
  test.setTimeout(60000);
  await openStocks(page);
  const initial = await portfolioId(page);
  const owned = await addPortfolio(page);
  await page.reload();
  await searchFor(page, "Quartz Fixture");
  await expect(stock(page, /FQXA · NASDAQ · Class A/)).toBeVisible();
  await expect(stock(page, /FQXB · NASDAQ · Class B/)).toBeVisible();
  expect(observedQuotes()).toEqual([]);
  const [exact] = await searchFor(page, "FQXA");
  const [item] = await searchFor(page, "FQOLD");
  expect(item).toEqual(exact);
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

  await page.getByRole("button", { name: "Back to results" }).click();
  await expect(row).toBeFocused();
  const search = page.getByRole("searchbox", { name: "Search stocks" });
  await expect(search).toHaveValue("FQOLD");
  const picker = page.getByRole("combobox", { name: "Trading portfolio" });
  const link = page.getByRole("link", { name: "View details FQXA" });
  await picker.selectOption(initial);
  await expect(link).toHaveAttribute(
    "href",
    `/portfolios/${initial}/trade/catalog/${item.catalog_id}`,
  );
  await picker.selectOption(owned);
  await expect(link).toHaveAttribute(
    "href",
    `/portfolios/${owned}/trade/catalog/${item.catalog_id}`,
  );
  await expect(search).toHaveValue("FQOLD");
  expect(observedQuotes()).toEqual([["FQXA"]]);
  await row.press("Enter");
  await expect(page.getByRole("heading", { name: quartz, exact: true })).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("markets-mobile-detail.png"), fullPage: true });
  await page.setViewportSize({ width: 640, height: 500 });
  await noOverflow(page);
  await link.click();
  await expect(page).toHaveURL(`/portfolios/${owned}/trade/catalog/${item.catalog_id}`);
});

test("catalog preserves a permitted closed mark in the selected owned portfolio", async ({
  page,
}) => {
  test.setTimeout(60000);
  const writes = financialWrites(page);
  await openStocks(page);
  const original = await portfolioId(page);
  const owned = await addPortfolio(page);
  // Portfolio setup uses a direct API request, outside the app query cache.
  await page.reload();
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
  await page.route(`**${searchPath}?*`, (route) =>
    route.fulfill({ status: 503, json: { detail: "unavailable" } }),
  );
  const search = page.getByRole("searchbox", { name: "Search stocks" });
  await search.fill("AAPL");
  await expect(
    page.getByText("Catalog search is unavailable. The original stocks are still available."),
  ).toBeVisible();
  await expect(stock(page, /AAPL/)).toBeVisible();
  await search.clear();
  await expect(page.getByRole("list", { name: "US stocks" }).getByRole("button")).toHaveCount(20);
  await stock(page, /AAPL/).click();
  await expect(page.getByRole("link", { name: "Trade AAPL" })).toHaveAttribute(
    "href",
    /trade\/stocks\/AAPL$/,
  );
  await page.getByRole("button", { name: "Crypto", exact: true }).click();
  await expect(page.getByRole("button", { name: /BTC/ })).toBeVisible();
  expect(observedQuotes()).toEqual([["FQXB"]]);
});

async function selectPromotedStock(page: Page, symbol = "FQZT") {
  const [item] = await searchFor(page, symbol);
  const selected = selectedQuote(page);
  const row = stock(page, new RegExp(symbol));
  await row.focus();
  await row.press("Enter");
  const response = await selected;
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({
    listing: item,
    read_only: false,
    execution_reason: "available",
    quote: { feed: "iex" },
  });
  return item;
}

test("catalog buys and sells a promoted out-of-list stock with repricing and replay", async ({
  page,
  browser,
}) => {
  test.setTimeout(120000);
  const writes = financialWrites(page);
  catalogFixture("catalog-finance");
  await openStocks(page);
  const portfolio = await portfolioId(page);
  const scope = "/api/v2/portfolios/" + portfolio;
  const item = await selectPromotedStock(page);
  const endpoint = scope + "/stock-catalog/" + item.catalog_id;
  const ticket = "/portfolios/" + portfolio + "/trade/catalog/" + item.catalog_id;
  await page.getByRole("link", { name: "Trade FQZT", exact: true }).click();
  await expect(page).toHaveURL(ticket);
  await expect(page.getByRole("combobox", { name: "Trading portfolio" })).toHaveCount(1);
  await expect(page.getByText("Cash available $10,000.00", { exact: true })).toBeVisible();
  const quantity = page.getByLabel("Whole-share quantity");
  await page.getByRole("button", { name: "Buy max" }).click();
  await expect(quantity).toHaveValue("97");
  await quantity.fill("2");
  await page.getByRole("button", { name: "Preview trade" }).click();
  const confirm = page.getByRole("button", { name: "Confirm buy" });
  await expect(confirm).toBeEnabled();
  catalogFixture("catalog-reprice");
  const changed = page.waitForResponse((r) => new URL(r.url()).pathname === endpoint + "/confirm");
  await confirm.click();
  expect((await changed).status()).toBe(409);
  await expect(
    page.getByText("Price updated. Review the changes before confirming again."),
  ).toBeVisible();
  let firstBody: unknown;
  let committed: unknown;
  const discardResult = "**" + endpoint + "/confirm";
  await page.route(discardResult, async (route) => {
    firstBody = route.request().postDataJSON();
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    committed = await response.json();
    await route.abort("failed");
  });
  await confirm.click();
  const check = page.getByRole("button", { name: "Check order result" });
  await expect(check).toBeEnabled();
  await page.unroute(discardResult);
  const replay = page.waitForResponse((r) => new URL(r.url()).pathname === endpoint + "/receipt");
  await check.click();
  const result = await replay;
  expect(result.status()).toBe(200);
  expect(result.request().postDataJSON()).toEqual(firstBody);
  expect(await result.json()).toEqual(committed);
  expect(writes.filter((path) => path === endpoint + "/confirm")).toHaveLength(2);
  const receipt = page.getByRole("heading", { name: "Order filled" });
  await expect(receipt).toBeFocused();
  await expect(page.getByText("Bought 2 shares", { exact: true })).toBeVisible();
  await expect(page.getByText("Cash after this trade", { exact: true })).toBeVisible();
  const bought = await (await page.request.get(scope)).json();
  expect(Number(bought.cash)).toBe(9791.75);
  expect(bought.holdings).toEqual([
    expect.objectContaining({ catalog_id: item.catalog_id, symbol: "FQZT", asset_class: "stock" }),
  ]);
  expect(Number(bought.holdings[0].quantity)).toBe(2);
  expect(Number(bought.holdings[0].cost_basis)).toBe(208.25);

  catalogFixture("catalog-halt");
  await page.reload();
  await expect(page.getByText("Trading halted.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Confirm|Preview/ })).toHaveCount(0);
  catalogFixture("catalog-resume");
  await page.reload();
  const sell = page.getByRole("radio", { name: "Sell", exact: true });
  await sell.click();
  await expect(sell).toBeChecked();
  await page.getByRole("button", { name: "Sell all" }).click();
  await expect(quantity).toHaveValue("2");
  await page.getByRole("button", { name: "Preview trade" }).click();
  const sale = page.waitForResponse((r) => new URL(r.url()).pathname === endpoint + "/confirm");
  await page.getByRole("button", { name: "Confirm sell" }).click();
  expect((await sale).status()).toBe(201);
  await expect(page.getByText("Sold 2 shares", { exact: true })).toBeVisible();
  const sold = await (await page.request.get(scope)).json();
  expect(Number(sold.cash)).toBe(9993.75);
  expect(sold.holdings).toEqual([]);
  expect(observedQuotes()).toEqual([["FQZT"]]);

  catalogFixture("catalog-stale");
  catalogFixture("catalog-outage");
  const stale = await page.request.get(endpoint + "/trade-context");
  expect(stale.status()).toBe(200);
  expect(await stale.json()).toMatchObject({
    read_only: true,
    execution_reason: "quote_stale",
  });
  await page.reload();
  await expect(page.getByText("This quote is out of date.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Confirm|Preview/ })).toHaveCount(0);
  expect(writes.filter((path) => path === endpoint + "/confirm")).toHaveLength(3);

  const stranger = await browser.newContext();
  try {
    const otherPage = await stranger.newPage();
    await signInNewUser(otherPage);
    expect((await otherPage.request.get(scope + "/history")).status()).toBe(404);
    expect((await otherPage.request.get(endpoint + "/trade-context")).status()).toBe(404);
  } finally {
    await stranger.close();
  }
  catalogFixture("catalog-traded-reuse");
  await page.goto("/portfolios/" + portfolio + "/history");
  const summary = page.locator("summary").filter({ hasText: /FQZT/ });
  await expect(summary).toHaveCount(2);
  await summary.first().click();
  const previous = page.getByRole("link", { name: "View stock ticket for FQZT" });
  await expect(previous).toHaveAttribute("href", ticket);
  await previous.click();
  await expect(page.getByRole("heading", { name: item.company_name, exact: true })).toBeVisible();
  await expect(page.getByText("This listing is no longer active.")).toBeVisible();
});

test("catalog preserves the SQL closed mark with an empty cache and suppresses expired marks", async ({
  page,
}) => {
  test.setTimeout(90000);
  const writes = financialWrites(page);
  catalogFixture("catalog-finance");
  await openStocks(page);
  const owned = await portfolioId(page);
  const item = await selectPromotedStock(page);
  catalogFixture("catalog-cold-close");
  await page.goto("/");
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await searchFor(page, "FQZT");
  const selected = selectedQuote(page);
  await stock(page, /FQZT/).click();
  expect(await (await selected).json()).toMatchObject({
    reason: "market_closed",
    execution_reason: "market_closed",
    quote: { feed: "iex" },
  });
  await expect(page.getByText(/^\$102\.00/)).toBeVisible();
  await expect(page.locator("time").filter({ hasText: /^Opens in / })).toBeVisible();
  const endpoint = "/api/v2/portfolios/" + owned + "/stock-catalog/" + item.catalog_id;
  const ownedContext = page.waitForResponse(
    (r) => new URL(r.url()).pathname === endpoint + "/trade-context",
  );
  await page.getByRole("link", { name: "View details FQZT" }).click();
  expect(await (await ownedContext).json()).toMatchObject({
    portfolio_id: owned,
    reason: "market_closed",
    execution_reason: "market_closed",
    quote: { feed: "iex" },
  });
  await expect(page.getByText("$102.00", { exact: true })).toBeVisible();
  await expect(page.getByText(/^Market closed\./)).toBeVisible();
  const draft = page.getByLabel("Whole-share quantity");
  await draft.fill("3");
  await expect(draft).toHaveValue("3");
  await expect(page.getByRole("button", { name: /Confirm|Preview/ })).toHaveCount(0);
  for (const width of [390, 640]) {
    await page.setViewportSize({ width, height: 680 });
    await noOverflow(page);
  }
  catalogFixture("catalog-expire-mark");
  await page.reload();
  await expect(page.getByText(/^Market closed\./)).toBeVisible();
  await expect(page.locator("time").filter({ hasText: /^Opens in / })).toBeVisible();
  await expect(page.getByText("$102.00", { exact: true })).toHaveCount(0);
  await page.goto("/");
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  await searchFor(page, "FQZT");
  const expired = selectedQuote(page);
  await stock(page, /FQZT/).click();
  expect(await (await expired).json()).toMatchObject({
    reason: "market_closed",
    execution_reason: "market_closed",
    quote: null,
  });
  await expect(page.locator("time").filter({ hasText: /^Opens in / })).toBeVisible();
  await expect(page.getByText(/^\$102\.00/)).toHaveCount(0);
  expect(observedQuotes()).toEqual([["FQZT"]]);
  expect(writes).toEqual([]);
});

test("catalog posts an ordinary dividend and split into the owned mixed portfolio", async ({
  page,
}) => {
  test.setTimeout(120000);
  const email = await signInNewUser(page);
  catalogFixture("catalog-finance-mixed", email);
  const owned = await portfolioId(page);
  const prefix = "/portfolios/" + owned;
  const scope = "/api/v2" + prefix;
  await page.getByRole("button", { name: "Crypto", exact: true }).click();
  await page.getByRole("list", { name: "Crypto" }).getByRole("button", { name: /BTC/ }).click();
  await page.getByRole("link", { name: "Trade BTC" }).click();
  await page.getByLabel("Amount").fill("100");
  const cryptoFilled = page.getByRole("heading", { name: "Order filled" });
  const cryptoUpdated = page.getByText("Price updated. Please review again.");
  for (let attempt = 0; attempt < 3 && !(await cryptoFilled.isVisible()); attempt++) {
    await page.getByRole("button", { name: "Confirm buy" }).click();
    await expect(cryptoFilled.or(cryptoUpdated)).toBeVisible();
  }
  await expect(cryptoFilled).toBeVisible();

  await page.goto("/");
  await page.getByRole("button", { name: "US stocks", exact: true }).click();
  const item = await selectPromotedStock(page, "FQZM");
  await page.getByRole("link", { name: "Trade FQZM", exact: true }).click();
  await page.getByLabel("Whole-share quantity").fill("2");
  await page.getByRole("button", { name: "Preview trade" }).click();
  await page.getByRole("button", { name: "Confirm buy" }).click();
  await expect(page.getByText("Bought 2 shares", { exact: true })).toBeVisible();
  catalogFixture("catalog-dividend");
  const paid = await (await page.request.get(scope)).json();
  expect(Number(paid.cash)).toBe(9695);
  catalogFixture("catalog-split");
  const split = await (await page.request.get(scope)).json();
  const holding = split.holdings.find(
    (row: { catalog_id?: string }) => row.catalog_id === item.catalog_id,
  );
  expect(holding).toMatchObject({ symbol: "FQZM", asset_class: "stock", current_value: null });
  expect(Number(holding.quantity)).toBe(8);
  expect(Number(holding.cost_basis)).toBe(206);
  expect(Number(split.cash)).toBe(9695);
  expect(split.holdings).toContainEqual(
    expect.objectContaining({
      symbol: "BTC",
      asset_class: "crypto",
      current_value: expect.any(String),
    }),
  );

  catalogFixture("catalog-hold");
  await page.goto(prefix);
  await expect(page.getByText(/Known value/).first()).toBeVisible();
  const incomplete = await (await page.request.get(scope)).json();
  expect(incomplete).toMatchObject({
    valuation_complete: false,
    unvalued_holding_count: 1,
    total_value: null,
    total_pl: null,
    cash_allocation_percent: null,
  });
  const btc = incomplete.holdings.find((row: { symbol: string }) => row.symbol === "BTC");
  expect(Number(incomplete.known_value)).toBeCloseTo(9695 + Number(btc.current_value), 8);
  await page.goto(prefix + "/history");
  const dividend = page.locator("summary").filter({ hasText: /Dividend.*FQZM|FQZM.*Dividend/ });
  const forwardSplit = page.locator("summary").filter({
    hasText: /Forward split.*FQZM|FQZM.*Forward split/,
  });
  await expect(dividend).toHaveCount(1);
  await expect(forwardSplit).toHaveCount(1);
  await dividend.click();
  await expect(page.getByRole("link", { name: "View stock ticket for FQZM" })).toHaveAttribute(
    "href",
    prefix + "/trade/catalog/" + item.catalog_id,
  );
  await expect(page.locator("summary").filter({ hasText: /BTC/ })).toHaveCount(1);
  const history = await (await page.request.get(scope + "/event-history")).json();
  const recorded = history.items.filter((row: { symbol: string }) => row.symbol === "FQZM");
  expect(recorded).toEqual(
    expect.arrayContaining(
      ["dividend", "split", "trade"].map((kind) =>
        expect.objectContaining({ kind, symbol: "FQZM", catalog_id: item.catalog_id }),
      ),
    ),
  );
  expect(Number(recorded.find((row: { kind: string }) => row.kind === "dividend").cash_delta)).toBe(
    1,
  );
  const splitEvent = recorded.find((row: { kind: string }) => row.kind === "split");
  expect(Number(splitEvent.quantity_before)).toBe(4);
  expect(Number(splitEvent.quantity_after)).toBe(8);
  expect(observedQuotes()).toEqual([["FQZM"]]);
});
