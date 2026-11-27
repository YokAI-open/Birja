import { writeFile } from "node:fs/promises";
import { expect, type Locator, type Page, type TestInfo } from "@playwright/test";

const anchors = {
  trade: {
    chooser: ".trade-chooser-shell select",
    heading: ".trade-workspace-heading",
    ticket: ".trade-workspace-ticket",
    preview: ".trade-workspace-preview",
  },
  history: {
    chooser: ".history-portfolio-picker select",
    update: 'button[aria-label="Update history"]',
    filters: ".history-filters",
    firstEvent: ".history-event-summary",
  },
  "sign-in": {
    panel: ".sign-in-workspace",
    heading: ".sign-in-title",
    email: "#email",
  },
} as const;

export async function capturePhase25(page: Page, info: TestInfo, surface: keyof typeof anchors) {
  for (const width of [1440, 390]) {
    const viewport = { width, height: 1000 };
    await page.setViewportSize(viewport);
    await page.evaluate("document.fonts.ready");
    const layout = Object.fromEntries(
      await Promise.all(
        Object.entries(anchors[surface]).map(async ([anchor, selector]) => {
          const element = page.locator(selector).first();
          await expect(element).toBeVisible();
          return [anchor, await element.boundingBox()];
        }),
      ),
    );
    if (surface === "history") {
      const { chooser, update } = layout;
      if (!chooser || !update) throw new Error("Expected measured History toolbar controls");
      expect(update.y).toBeCloseTo(chooser.y, 1);
      expect(update.x - (chooser.x + chooser.width)).toBeCloseTo(8, 1);
      expect(update.height).toBeCloseTo(44, 1);
    }
    await page.screenshot({
      path: info.outputPath(`${surface}-${width}.png`),
      animations: "disabled",
    });
    await writeFile(
      info.outputPath(`${surface}-${width}.json`),
      JSON.stringify({ viewport, layout }),
    );
  }
}

export async function testPhase25Reflow(page: Page, first: Locator, next: Locator, text: Locator) {
  await page.setViewportSize({ width: 320, height: 1000 });
  const fitsViewport = () =>
    page.evaluate<boolean>("document.documentElement.scrollWidth <= innerWidth");
  expect(await fitsViewport()).toBe(true);
  const styledSizes = await page.evaluate<number[]>(`Array.from(document.querySelectorAll('body *'))
    .filter(element => element instanceof HTMLElement && element.getClientRects().length && (
      element.matches('input, select, textarea, button') ||
      Array.from(element.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim())
    )).map((element, index) => {
      element.setAttribute('data-phase25-font', String(index));
      return parseFloat(getComputedStyle(element).fontSize);
    })`);
  const representatives = [first, next, text];
  const sizes = await Promise.all(
    representatives.map(async (locator) => {
      const index = await locator.getAttribute("data-phase25-font");
      if (index === null) throw new Error("Expected a visible text enlargement target");
      return styledSizes[Number(index)];
    }),
  );
  const style = await page.addStyleTag({
    content: styledSizes
      .map(
        (size, index) => `[data-phase25-font="${index}"] { font-size: ${size * 2}px !important; }`,
      )
      .join("\n"),
  });
  try {
    expect(await fitsViewport()).toBe(true);
    for (let index = 0; index < sizes.length; index++) {
      await expect(representatives[index]).toHaveCSS("font-size", `${sizes[index] * 2}px`);
    }
    await first.focus();
    await expect(first).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(next).toBeFocused();
    await expect(next).toBeInViewport();
  } finally {
    await style.evaluate((element) => element.remove());
    await page.evaluate(`document.querySelectorAll('[data-phase25-font]').forEach(
      element => element.removeAttribute('data-phase25-font')
    )`);
  }
}

export type TradeReceipt = {
  portfolio_id: string;
  symbol: string;
  side: "buy" | "sell";
  quantity: string;
  exec_price: string;
  fee: string;
  cash_delta: string;
  cash_after: string;
  trade_id: string | number;
  catalog_id?: string;
};

// Compare wire decimals exactly even when one endpoint pads its scale.
const decimal = (value: string) => value.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");

export async function verifyOwnedReceipt(
  page: Page,
  receipt: TradeReceipt,
  asset: "stock" | "crypto",
) {
  const scope = `/api/v2/portfolios/${receipt.portfolio_id}`;
  const [statement, history] = await Promise.all([
    page.request.get(scope),
    page.request.get(`${scope}/event-history`),
  ]);
  expect(statement.ok()).toBe(true);
  expect(history.ok()).toBe(true);
  expect(decimal((await statement.json()).cash)).toBe(decimal(receipt.cash_after));
  const event = (await history.json()).items[0];
  expect(event).toMatchObject({
    id: `trade:${receipt.trade_id}`,
    kind: "trade",
    asset_type: asset,
    side: receipt.side,
    symbol: receipt.symbol,
    ...(receipt.catalog_id ? { catalog_id: receipt.catalog_id } : {}),
  });
  for (const field of ["cash_delta", "quantity", "exec_price", "fee"] as const) {
    expect(decimal(event[field])).toBe(decimal(receipt[field]));
  }
}
