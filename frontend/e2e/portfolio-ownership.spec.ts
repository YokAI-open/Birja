import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { signInNewUser, readCodeFromLogs } from "./helpers.js";
import { stockFixture } from "./stock-trade-fixtures.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
type Book = { id: string; name: string; cash: string; starting_cash: string; closed: boolean };
function fixture(mode: "inspect" | "sibling" | "name" | "price-tick", email: string): Book[] {
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
      { cwd: root, encoding: "utf8", timeout: 30000 },
    ),
  );
}
function income(mode: "seed" | "up" | "uncertain" | "reconcile", email: string) {
  expect(process.env.COMPOSE_PROJECT_NAME).toBe("birja-phase09-e2e-test");
  execFileSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "backend",
      "python",
      "/browser-fixtures/dividend-execution-fixture.py",
      mode,
      email,
      "AMD",
    ],
    { cwd: root, timeout: 60000 },
  );
}
async function books(page: Page): Promise<Array<{ id: string; name: string }>> {
  const response = await page.request.get("/api/v2/portfolios");
  expect(response.status()).toBe(200);
  return response.json();
}
async function only(page: Page) {
  const result = await books(page);
  expect(result).toHaveLength(1);
  return result[0].id;
}
async function statement(page: Page, id: string) {
  const response = await page.request.get(`/api/v2/portfolios/${id}`);
  expect(response.status()).toBe(200);
  return response.json();
}
async function signIn(page: Page, email: string) {
  await page.goto("/");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByRole("button", { name: "Send code", exact: true }).click();
  await page.getByLabel("6-digit code").fill(await readCodeFromLogs(email));
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
}
async function crypto(page: Page, id: string, amount = "100") {
  await page.goto(`/portfolios/${id}/trade/BTC`);
  await page.getByLabel("Amount", { exact: true }).fill(amount);
  for (let n = 0; n < 3; n++) {
    const done = page.waitForResponse(
      (r) => r.url().endsWith(`/portfolios/${id}/trades`) && r.request().method() === "POST",
    );
    const confirm = page.getByRole("button", { name: "Confirm buy", exact: true });
    await expect(confirm).toBeEnabled();
    await confirm.click();
    const response = await done;
    if (response.status() === 201) {
      const value = await response.json();
      expect(value.portfolio_id).toBe(id);
      await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeFocused();
      return value;
    }
    expect((await response.json()).detail.code).toBe("price_changed");
  }
  throw new Error("No crypto fill after three explicit confirmations");
}
async function stockPreview(page: Page, id: string) {
  await page.goto(`/portfolios/${id}/trade/stocks/AAPL`);
  await page.getByLabel("Whole-share quantity").fill("2");
  await page.getByRole("button", { name: "Preview trade", exact: true }).click();
  await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeEnabled();
}
async function stockFill(page: Page, id: string) {
  const done = page.waitForResponse(
    (r) => r.url().endsWith(`/portfolios/${id}/stock-trades`) && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Confirm buy", exact: true }).click();
  const response = await done;
  expect(response.status()).toBe(201);
  const value = await response.json();
  expect(value.portfolio_id).toBe(id);
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeFocused();
  return value;
}
async function noOverflow(page: Page) {
  const overflow = await page.evaluate(`
    Array.from(document.querySelectorAll("body *"))
      .filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && (r.right > innerWidth + 0.5 || r.left < -0.5);
      })
      .slice(0, 15)
      .map((el) => ({
        tag: el.tagName,
        classes: el.className,
        width: el.getBoundingClientRect().width,
        x: el.getBoundingClientRect().x,
        minWidth: getComputedStyle(el).minWidth,
      }))
  `);
  expect(
    await page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
    JSON.stringify(overflow),
  ).toBe(true);
}

async function inApp(page: Page, path: string) {
  await page.evaluate(`(next => {
    const state = {
      usr: null,
      key: crypto.randomUUID(),
      idx: (window.history.state?.idx ?? 0) + 1,
    };
    window.history.pushState(state, "", next);
    window.dispatchEvent(new PopStateEvent("popstate", { state }));
  })(${JSON.stringify(path)})`);
  await expect(page).toHaveURL(new RegExp(path + "$"));
}

/** Actual DOM/CSS/fonts made inert for private offline owner review. */
async function snapshot(page: Page, info: TestInfo, name: string) {
  await noOverflow(page);
  const destination = process.env.BIRJA_PHASE12_REVIEW_DIR;
  const png = destination ? `${destination}/${name}.png` : info.outputPath(`${name}.png`);
  await page.screenshot({ path: png, fullPage: true });
  let css = await page.evaluate<string>(
    "Array.from(document.styleSheets).flatMap(s=>Array.from(s.cssRules,r=>r.cssText)).join('\\n')",
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
  const brandImages = await Promise.all(
    [
      ["/brand/icon-96.png", "image/png"],
      ["/brand/logo-240.webp", "image/webp"],
    ].map(async ([url, type]) => {
      const image = await page.request.get(url);
      expect(image.ok()).toBe(true);
      return [url, `data:${type};base64,${(await image.body()).toString("base64")}`];
    }),
  );
  const html = await page.evaluate<string>(`(([styles,brandImages])=>{
    const d=document.cloneNode(true);
    const values=document.querySelectorAll('input');
    d.querySelectorAll('input').forEach((n,i)=>{n.setAttribute('value',values[i].value);if(values[i].checked)n.setAttribute('checked','');n.setAttribute('readonly','');});
    d.querySelectorAll('script,link,style,iframe').forEach(n=>n.remove());
    const assets=new Map(brandImages);
    d.querySelectorAll('picture img, picture source').forEach(n=>{
      const attribute=n.tagName==='SOURCE'?'srcset':'src';
      const data=assets.get(n.getAttribute(attribute));
      if(data)n.setAttribute(attribute,data);
    });
    d.querySelectorAll('form').forEach(n=>{const v=d.createElement('div');v.className=n.className;v.replaceChildren(...n.childNodes);n.replaceWith(v);});
    d.querySelectorAll('a').forEach(n=>n.setAttribute('href','#'));
    d.querySelectorAll('button').forEach(n=>n.setAttribute('type','button'));
    const s=d.createElement('style');s.textContent=styles;d.head.append(s);
    const c=d.createElement('meta');c.httpEquiv='Content-Security-Policy';c.content="default-src 'none';style-src 'unsafe-inline';font-src data:;img-src data:;base-uri 'none';form-action 'none'";d.head.prepend(c);
    const note=d.createElement('p');note.textContent='Read-only synthetic review source ${process.env.BIRJA_PHASE12_SOURCE ?? "unbound"}. Actions do not execute. Check your browser menu at native 200% zoom.';note.style.padding='16px';d.body.prepend(note);
    return '<!doctype html>\\n'+d.documentElement.outerHTML;
  })(${JSON.stringify([css, brandImages])})`);
  expect(html).not.toMatch(/<script|<form|\s(?:src|href|action)=["']https?:/);
  await writeFile(
    destination ? `${destination}/${name}.html` : info.outputPath(`${name}.html`),
    html,
    { flag: "wx" },
  );
  const viewport = page.viewportSize();
  if (viewport?.width === 1280) {
    // The 1280px desktop canvas at 200%-equivalent reflow is 640x480 CSS
    // pixels. Capture every state at that size; native zoom stays a human gate.
    await page.setViewportSize({ width: 640, height: 480 });
    try {
      await snapshot(page, info, `automated-reflow-${name}`);
    } finally {
      await page.setViewportSize(viewport);
    }
  }
}

test.beforeEach(() => stockFixture("fresh"));

test("actual migrated original survives sign-in and reused-browser owner switch", async ({
  page,
}) => {
  await signIn(page, "e2e-migrated@example.com");
  const id = await only(page);
  const before = await statement(page, id);
  expect(before.cash).toBe("123.45");
  expect(before.starting_cash).toBe("9999.00");
  await page.goto(`/portfolios/${id}`);
  await expect(page.getByText("My portfolio", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByLabel("Email", { exact: true })).toBeVisible();
  await expect(page.getByText("Cash", { exact: true })).toHaveCount(0);
  await signInNewUser(page);
  await page.goto(`/portfolios/${id}`);
  await expect(
    page.getByRole("heading", { name: "Portfolio unavailable", exact: true }),
  ).toBeVisible();
  expect((await page.request.get(`/api/v2/portfolios/${id}`)).status()).toBe(404);
  expect(await only(page)).not.toBe(id);
});

test("actual scoped crypto and stock fills preserve exact independent cash and receipts", async ({
  page,
}) => {
  await signInNewUser(page);
  const id = await only(page);
  const fill = await crypto(page, id);
  expect(fill.cash_after).toBe("9900.00000000");
  await stockPreview(page, id);
  const stock = await stockFill(page, id);
  expect(stock.cash_after).toBe("9696.00000000");
  expect(stock.fee).toBe("0.00000000");
  await expect(page.getByRole("link", { name: "Portfolio", exact: true }).last()).toHaveAttribute(
    "href",
    `/portfolios/${id}`,
  );
  const value = await statement(page, id);
  expect(value.holdings.map((h: { symbol: string }) => h.symbol)).toEqual(["AAPL", "BTC"]);
  expect((await page.request.get("/api/v1/portfolio")).status()).toBe(409);
});

test("lost actual response recovers only original portfolio key without duplicate cash", async ({
  page,
}) => {
  const email = await signInNewUser(page);
  const id = await only(page);
  // These strategies exist before the first financial metadata observation.
  // Public creation/invalidation is Phase13; this fixture must not silently
  // create a new root behind a valid owner-scoped metadata cache.
  fixture("sibling", email);
  const sibling = fixture("inspect", email).find(
    (book: { name: string }) => book.name === "Sibling strategy",
  )!.id;
  const attempts: string[] = [];
  const refusedKeys: string[] = [];
  const outcomes: number[] = [];
  await page.route(`**/api/v2/portfolios/${id}/trades`, async (route) => {
    const payload = route.request().postData()!;
    if (attempts.length === 0 && refusedKeys.length === 0) fixture("price-tick", email);
    const response = await route.fetch();
    if (response.status() === 409 && attempts.length === 0) {
      const refusal = await response.json();
      expect(refusal.detail.code).toBe("price_changed");
      expect(refusal.detail.quote.portfolio_id).toBe(id);
      expect(refusal.detail.quote.mid).not.toBe(JSON.parse(payload).expected_mid);
      const unchanged = await statement(page, id);
      expect(unchanged.cash).toBe("10000.00");
      expect(unchanged.holdings).toEqual([]);
      expect((await statement(page, sibling)).cash).toBe("2000.00");
      refusedKeys.push(JSON.parse(payload).idempotency_key);
      await route.fulfill({ response });
      outcomes.push(409);
      return;
    }
    expect(response.status()).toBe(attempts.length === 0 ? 201 : 200);
    attempts.push(payload);
    if (attempts.length === 1) {
      expect(refusedKeys).not.toContain(JSON.parse(payload).idempotency_key);
      await route.abort("failed");
    } else await route.fulfill({ response });
    outcomes.push(response.status());
  });
  await page.goto(`/portfolios/${id}/trade/BTC`);
  await page.getByLabel("Amount", { exact: true }).fill("100");
  // A real provider tick must refuse without cash effects. Each subsequent
  // confirmation is an explicit user action; only the actual fill is lost.
  for (let n = 0; n < 3; n++) {
    const confirm = page.getByRole("button", { name: "Confirm buy", exact: true });
    await expect(confirm).toBeEnabled();
    await confirm.click();
    await expect.poll(() => outcomes.length).toBe(n + 1);
    if (outcomes[n] === 201) break;
    await expect(
      page.getByText("Price updated. Please review again.", { exact: true }),
    ).toBeVisible();
  }
  expect(outcomes[0]).toBe(409);
  expect(outcomes.at(-1)).toBe(201);
  await expect(page.getByRole("button", { name: "Check order result", exact: true })).toBeVisible();
  await page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name: "Markets", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  await inApp(page, `/portfolios/${sibling}/trade/BTC`);
  const switcher = page.getByRole("combobox", { name: "Open portfolio" });
  await expect(switcher).toHaveValue(sibling);
  await expect(switcher.locator("option:checked")).toHaveText("Sibling strategy");
  await expect(page.getByRole("button", { name: "Check order result", exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toHaveCount(0);
  expect(attempts).toHaveLength(1);
  // Returning uses retained state within the same app, not a new attempt key.
  await page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name: "Markets", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  await inApp(page, `/portfolios/${id}/trade/BTC`);
  await expect(page.getByRole("button", { name: "Check order result", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Check order result", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Order filled", exact: true })).toBeVisible();
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toBe(attempts[0]);
  expect((await statement(page, id)).cash).toBe("9900.00");
  expect((await statement(page, sibling)).cash).toBe("2000.00");
});

for (const mode of ["zero", "sibling"] as const)
  test(`actual identity with ${mode} roots never guesses at legacy entry`, async ({ page }) => {
    const email = await signInNewUser(page);
    if (mode === "zero") {
      const id = await only(page);
      const detail = await statement(page, id);
      expect((await page.request.get("/api/v1/auth/csrf")).status()).toBe(204);
      const csrf = (await page.context().cookies()).find((value) => value.name === "bj_csrf");
      expect(csrf).toBeDefined();
      const closed = await page.request.delete(`/api/v2/portfolios/${id}`, {
        headers: { "X-CSRF-Token": csrf!.value },
        data: {
          intent_key: randomUUID(),
          confirmation_name: detail.name,
          policy_version: "freeze_at_closure_v1",
        },
      });
      expect(closed.status()).toBe(200);
      expect(await closed.json()).toEqual({ portfolio_id: id, state: "closed" });
    } else {
      fixture(mode, email);
    }
    const finance: string[] = [];
    page.on("request", (request) => {
      if (/\/api\/v2\/portfolios\/\d+/.test(request.url())) finance.push(request.url());
    });
    await page.goto("/portfolio");
    await expect(
      page.getByRole("heading", {
        name: mode === "zero" ? "No portfolio available" : "Portfolio required",
        exact: true,
      }),
    ).toBeVisible();
    expect(finance).toEqual([]);
    const identity = await page.request.get("/api/v2/me");
    expect(await identity.json()).toEqual({ email });
  });

test("late actual sibling projection cannot replace current root", async ({ page }) => {
  const email = await signInNewUser(page);
  const id = await only(page);
  fixture("sibling", email);
  const sibling = fixture("inspect", email).find(
    (book: { name: string }) => book.name === "Sibling strategy",
  )!.id;
  let release!: () => void;
  const pause = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started!: () => void;
  const fetched = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route(`**/api/v2/portfolios/${id}`, async (route) => {
    const response = await route.fetch();
    started();
    await pause;
    await route.fulfill({ response }).catch(() => {});
  });
  await page.goto(`/portfolios/${id}`);
  await fetched;
  await page.getByRole("link", { name: "Markets", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Markets", exact: true })).toBeVisible();
  await inApp(page, `/portfolios/${sibling}`);
  await expect(page.getByText("Sibling strategy", { exact: true }).first()).toBeVisible();
  release();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText("$2,000.00", { exact: true }).first()).toBeVisible();
});

test("actual mixed dividend corrections retain same-root original details", async ({ page }) => {
  const email = await signInNewUser(page);
  const id = await only(page);
  await crypto(page, id);
  income("seed", email);
  income("up", email);
  income("uncertain", email);
  await page.goto(`/portfolios/${id}/history`);
  await expect(page.getByRole("heading", { name: "History", exact: true, level: 1 })).toBeVisible();
  const response = await page.request.get(`/api/v2/portfolios/${id}/event-history?limit=100`);
  const value = await response.json();
  const original = value.items.find(
    (item: { kind: string }) => item.kind === "dividend_correction",
  ).payment_reference;
  await page.locator("summary").filter({ hasText: "Dividend correction" }).first().click();
  await page.getByRole("button", { name: "View original dividend", exact: true }).first().click();
  await expect
    .poll(() => page.evaluate("document.activeElement?.id ?? ''"))
    .toMatch(new RegExp(original + "$"));
  expect(new Set(value.items.map((item: { kind: string }) => item.kind))).toEqual(
    new Set(["trade", "dividend", "dividend_correction"]),
  );
  // An uncertainty hold is instrument-global and must outlive healthy polls.
  // Finish this synthetic scenario through its existing reviewed reconciliation
  // evidence before another case creates a new dividend for the same stock.
  income("reconcile", email);
});

for (const width of [320, 768, 1280])
  test(`read-only actual UI review at ${width}px and 200%-equivalent reflow`, async ({
    page,
  }, info) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width, height: 960 });
    await page.goto("/");
    await page.getByRole("button", { name: "Go to sign-in form" }).press("Enter");
    await expect(page.getByLabel("Email", { exact: true })).toBeFocused();
    await snapshot(page, info, `sign-in-${width}`);
    const email = await signInNewUser(page);
    await page.getByRole("button", { name: "Crypto", exact: true }).click();
    await expect(page.getByRole("list", { name: "Crypto", exact: true })).toBeVisible();
    await snapshot(page, info, `markets-${width}`);
    const id = await only(page);
    fixture("name", email);
    await page.goto(`/portfolios/${id}/trade/BTC`);
    const switcher = page.getByRole("combobox", { name: "Open portfolio" });
    await expect(switcher).toHaveValue(id);
    await expect(switcher.locator("option:checked")).toContainText(
      "<Strategy>& UnbrokenPortfolioNameUnbrokenPortfolioName",
    );
    await snapshot(page, info, `crypto-draft-${width}`);
    await page.getByLabel("Amount", { exact: true }).fill("100");
    await expect(page.getByRole("button", { name: "Confirm buy", exact: true })).toBeEnabled();
    await snapshot(page, info, `crypto-preview-${width}`);
    await crypto(page, id);
    await snapshot(page, info, `crypto-receipt-${width}`);
    await stockPreview(page, id);
    await snapshot(page, info, `stock-preview-${width}`);
    await stockFill(page, id);
    await snapshot(page, info, `stock-receipt-${width}`);
    await page.goto(`/portfolios/${id}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: "Trade AAPL", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Trade BTC", exact: true })).toBeVisible();
    await snapshot(page, info, `holdings-${width}`);
    stockFixture("hold");
    await page.reload();
    await expect(page.getByText(/Known value/).first()).toBeVisible();
    await snapshot(page, info, `incomplete-${width}`);
    await page.goto(`/portfolios/${id}/history`);
    await expect(
      page.getByRole("heading", { name: "History", exact: true, level: 1 }),
    ).toBeVisible();
    await snapshot(page, info, `history-${width}`);
    income("seed", email);
    income("up", email);
    await page.reload();
    await page.locator("summary").filter({ hasText: "Dividend correction" }).first().click();
    await page.getByRole("button", { name: "View original dividend", exact: true }).first().click();
    await snapshot(page, info, `mixed-original-${width}`);
    income("uncertain", email);
    await page.reload();
    await expect(
      page
        .getByText("Dividend correction held", { exact: true })
        .and(page.locator(":visible"))
        .first(),
    ).toBeVisible();
    await snapshot(page, info, `held-correction-${width}`);
    income("reconcile", email);
    await page.goto("/portfolios/9223372036854775807");
    await expect(
      page.getByRole("heading", { name: "Portfolio unavailable", exact: true }),
    ).toBeVisible();
    await snapshot(page, info, `unavailable-${width}`);
    await page.setViewportSize({ width: 640, height: 480 });
    await noOverflow(page);
    await snapshot(page, info, `automated-reflow-${width}`);
  });
