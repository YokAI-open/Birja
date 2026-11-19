import { act, screen, waitFor, within } from "@testing-library/react";
import { Link, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import TradePage from "./TradePage";
import { PortfolioTargetBoundary } from "@/components/PortfolioTargetBoundary";
import { cashPortfolio } from "@/test/portfolioFixtures";
import { openDeletionRecovery } from "@/lib/portfolioDeletionAttempt";

type Ctx = {
  mid: string;
  holding: string;
  priceAge: number;
  coins: string[];
  quote: (body: Record<string, unknown>) => Response | Promise<Response>;
  trade: (body: Record<string, unknown>) => Response | Promise<Response>;
  me: () => Response;
  name: string;
};

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const refusal = (status: number, code: string, message: string, extra: object = {}) =>
  json({ detail: { code, message, ...extra } }, status);

const quoteBody = (body: Record<string, unknown>, mid: string) => {
  const sell = body.side === "sell";
  return {
    portfolio_id: "1",
    symbol: "BTC",
    side: body.side,
    input_kind: body.amount_usd !== undefined ? "usd" : "quantity",
    input_value: String(body.amount_usd ?? body.quantity),
    mid,
    as_of: "2026-10-28T09:59:50Z",
    age_seconds: 10,
    exec_price: sell ? "99750.00000000" : "100250.00000000",
    quantity: sell ? String(body.quantity) : "0.00099501",
    notional: "99.75000000",
    fee: "0.25000000",
    cash_delta: sell ? "99.50000000" : "-100.00000000",
    cash_before: "10000.00000000",
    cash_after: "9900.00000000",
    held_before: "0",
    held_after: "0.00099501",
    whole_position: false,
  };
};

const fillBody = (
  mid: string,
  body: Record<string, unknown> = { side: "buy", amount_usd: "100" },
) => ({
  portfolio_id: "1",
  trade_id: 1,
  created_at: "2026-10-28T10:00:00Z",
  symbol: "BTC",
  side: body.side,
  input_kind: body.amount_usd !== undefined ? "usd" : "quantity",
  input_value: String(body.amount_usd ?? body.quantity),
  mid,
  as_of: "2026-10-28T09:59:50Z",
  exec_price: "100250.00000000",
  quantity: "0.00099501",
  notional: "99.75000000",
  fee: "0.25000000",
  cash_delta: "-100.00000000",
  cash_after: "9900.00000000",
});

let ctx: Ctx;
let posts: { url: string; body: Record<string, unknown> }[];
let urls: string[];

function install() {
  ctx = {
    name: "Strategy one",
    mid: "100000.00000000",
    holding: "0",
    priceAge: 10,
    coins: ["BTC", "ETH"],
    quote: (body) => json(quoteBody(body, ctx.mid)),
    trade: (body) => json(fillBody(ctx.mid, body)),
    me: () => json({ email: "a@example.com" }),
  };
  posts = [];
  urls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      urls.push(url);
      if (url === "/api/v1/prices") {
        return Promise.resolve(
          json({
            server_time: "2026-10-28T10:00:00Z",
            fresh_seconds: 90,
            stale_seconds: 300,
            items: ctx.coins.map((symbol) => ({
              symbol,
              name: symbol === "BTC" ? "Bitcoin" : symbol,
              price: ctx.mid,
              as_of: "2026-10-28T09:59:50Z",
              age_seconds: ctx.priceAge,
              status: "fresh",
            })),
          }),
        );
      }
      if (url === "/api/v2/me") return Promise.resolve(ctx.me());
      if (url === "/api/v2/portfolios")
        return Promise.resolve(
          json([
            { id: "1", name: ctx.name },
            { id: "2", name: "Strategy two" },
          ]),
        );
      if (/^\/api\/v2\/portfolios\/[12]$/.test(url))
        return Promise.resolve(
          json({
            ...cashPortfolio(),
            portfolio_id: url.endsWith("2") ? "2" : "1",
            name: "Strategy one",
          }),
        );
      if (url.startsWith("/api/v2/portfolios/1/holdings/")) {
        return Promise.resolve(json({ portfolio_id: "1", symbol: "BTC", quantity: ctx.holding }));
      }
      if (url === "/api/v2/portfolios/1/trades/quote" || url === "/api/v2/portfolios/1/trades") {
        const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
        posts.push({ url, body });
        return Promise.resolve(
          url === "/api/v2/portfolios/1/trades" ? ctx.trade(body) : ctx.quote(body),
        );
      }
      return Promise.resolve(new Response(null, { status: 204 }));
    }),
  );
}

const tradePosts = () => posts.filter((p) => p.url === "/api/v2/portfolios/1/trades");
const quotePosts = () => posts.filter((p) => p.url === "/api/v2/portfolios/1/trades/quote");
const countUrl = (url: string) => urls.filter((u) => u === url).length;

function show(route = "/trade/BTC") {
  return renderWithClient(
    <Routes>
      <Route path="/portfolios/:portfolioId" element={<PortfolioTargetBoundary />}>
        <Route
          path="trade/:symbol"
          element={
            <>
              <Link to="/portfolios/2/trade/BTC">Other strategy</Link>
              <TradePage />
            </>
          }
        />
      </Route>
      <Route path="/" element={<p>Markets home</p>} />
    </Routes>,
    { route: route.startsWith("/trade/") ? "/portfolios/1" + route : route },
  );
}

type User = ReturnType<typeof show>["user"];

async function enter(user: User, value: string, label = "Amount") {
  const field = await screen.findByLabelText(label);
  await user.clear(field);
  await user.type(field, value);
}

const previewCard = () => within(screen.getByRole("region", { name: "Preview" }));
const confirmButton = (side = "buy") => screen.getByRole("button", { name: `Confirm ${side}` });

async function previewReady(user: User, value = "100") {
  await enter(user, value);
  await screen.findByText("0.00099501 BTC");
  await waitFor(() => {
    expect(confirmButton()).toBeEnabled();
  });
}

let uuid = 0;
const tradeKey = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;

beforeEach(async () => {
  document.cookie = "bj_csrf=tok; path=/";
  sessionStorage.clear();
  // Recovery has its own genuine nonce; deterministic valid UUIDs below
  // identify financial attempts, independently of recovery initialization.
  await openDeletionRecovery("a@example.com");
  uuid = 0;
  vi.spyOn(crypto, "randomUUID").mockImplementation(
    () => tradeKey(++uuid) as ReturnType<typeof crypto.randomUUID>,
  );
  install();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("TradePage", () => {
  it("renders the coin, live price and an idle form", async () => {
    show();
    expect(await screen.findByRole("heading", { level: 1, name: "Trade BTC" })).toBeVisible();
    expect(await screen.findByText("Bitcoin")).toBeVisible();
    expect(screen.getByText("$100,000.00")).toBeVisible();
    expect(screen.getByText("Live · 10s ago")).toBeVisible();
    expect(screen.getByRole("radio", { name: "Buy" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radiogroup", { name: "Side" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Amount (USD)" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(await screen.findByText("Cash available $10,000.00")).toBeVisible();
    expect(confirmButton()).toBeDisabled();
    expect(quotePosts()).toHaveLength(0);
  });

  it("requests one server quote after the debounce and shows the preview", async () => {
    const { user } = show();
    await enter(user, "100");
    expect(await screen.findByText("0.00099501 BTC")).toBeVisible();
    expect(quotePosts()).toHaveLength(1);
    expect(quotePosts()[0]!.body).toEqual({ symbol: "BTC", side: "buy", amount_usd: "100" });
    const preview = previewCard();
    expect(preview.getByText("$100,000.00")).toBeVisible();
    expect(preview.getByText("$100,250.00")).toBeVisible();
    expect(preview.getByText("$0.25")).toBeVisible();
    expect(preview.getByText("-$100.00")).toBeVisible();
    expect(confirmButton()).toBeEnabled();
  });

  it("shows inline errors for invalid input and sends no quote", async () => {
    const { user } = show();
    await enter(user, "1.005");
    expect(await screen.findByText("Enter an amount with up to 2 decimals.")).toBeVisible();
    await enter(user, "0");
    expect(await screen.findByText("Enter an amount greater than 0.")).toBeVisible();
    await enter(user, "abc");
    expect(await screen.findByText("Enter an amount with up to 2 decimals.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Quantity" }));
    await enter(user, "0.123456789", "Quantity");
    expect(await screen.findByText("Enter a quantity with up to 8 decimals.")).toBeVisible();
    await enter(user, "0.0", "Quantity");
    expect(await screen.findByText("Enter a quantity greater than 0.")).toBeVisible();
    await new Promise((resolve) => setTimeout(resolve, 400));
    expect(quotePosts()).toHaveLength(0);
    expect(confirmButton()).toBeDisabled();
  });

  it("buys by quantity", async () => {
    const { user } = show();
    await user.click(await screen.findByRole("button", { name: "Quantity" }));
    await enter(user, "0.001", "Quantity");
    await screen.findByText("0.00099501 BTC");
    expect(quotePosts()[0]!.body).toEqual({ symbol: "BTC", side: "buy", quantity: "0.001" });
  });

  it("fills the order, shows the result and refreshes cash, holding and prices", async () => {
    const { user } = show();
    await previewReady(user);
    const before = {
      portfolio: countUrl("/api/v2/portfolios/1"),
      holding: countUrl("/api/v2/portfolios/1/holdings/BTC"),
      prices: countUrl("/api/v1/prices"),
    };
    await user.click(confirmButton());
    expect(await screen.findByRole("heading", { name: "Order filled" })).toBeVisible();
    const sent = tradePosts()[0]!.body;
    expect(sent).toEqual({
      symbol: "BTC",
      side: "buy",
      amount_usd: "100",
      expected_mid: "100000.00000000",
      idempotency_key: tradeKey(1),
    });
    const card = within(screen.getByRole("region", { name: "Order filled" }));
    expect(card.getByText("0.00099501 BTC")).toBeVisible();
    expect(card.getByText("$100,250.00")).toBeVisible();
    expect(card.getByText("$0.25")).toBeVisible();
    expect(card.getByText("-$100.00")).toBeVisible();
    expect(card.getByText("$9,900.00")).toBeVisible();
    await waitFor(() => {
      expect(countUrl("/api/v2/portfolios/1")).toBeGreaterThan(before.portfolio);
      expect(countUrl("/api/v2/portfolios/1/holdings/BTC")).toBeGreaterThan(before.holding);
      expect(countUrl("/api/v1/prices")).toBeGreaterThan(before.prices);
    });

    await user.click(screen.getByRole("button", { name: "Trade again" }));
    expect(screen.getByRole("heading", { name: "Preview" })).toBeVisible();
    expect(screen.getByLabelText("Amount")).toHaveValue("");
    // A fill ends the attempt: the next order gets a new key.
    await previewReady(user);
    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()[1]!.body.idempotency_key).toBe(tradeKey(2));
  });

  it("sends exactly one request on a double click", async () => {
    ctx.trade = (body) =>
      new Promise((resolve) => setTimeout(() => resolve(json(fillBody(ctx.mid, body))), 80));
    const { user } = show();
    await previewReady(user);
    await user.dblClick(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()).toHaveLength(1);
  });

  it("locks edits for an unknown result and checks only its frozen original attempt", async () => {
    let fail = true;
    ctx.trade = (body) =>
      fail ? Promise.reject(new TypeError("network")) : json(fillBody(ctx.mid, body));
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    const check = await screen.findByRole("button", { name: "Check order result" });
    expect(screen.getByLabelText("Amount")).toBeDisabled();
    expect(screen.getByRole("radio", { name: "Sell" })).toBeDisabled();
    await user.click(check);
    await waitFor(() => expect(tradePosts()).toHaveLength(2));
    expect(tradePosts()[1]!.body).toEqual(tradePosts()[0]!.body);
    fail = false;
    await user.click(await screen.findByRole("button", { name: "Check order result" }));
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()[2]!.body).toEqual(tradePosts()[0]!.body);
    await user.click(screen.getByRole("button", { name: "Trade again" }));
    await previewReady(user, "50");
    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()[3]!.body.idempotency_key).toBe(tradeKey(2));
  });

  it("reuses the key when a quote refetch moves the mid between a failed attempt and the retry", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let fail = true;
    ctx.trade = (body) => {
      if (fail) return Promise.reject(new TypeError("network"));
      return json(fillBody(ctx.mid, body));
    };
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    await screen.findByRole("alert");

    ctx.mid = "100050.00000000";
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(quotePosts().length).toBeGreaterThanOrEqual(2);
    expect(await previewCard().findByText("$100,050.00")).toBeVisible();

    fail = false;
    await user.click(screen.getByRole("button", { name: "Check order result" }));
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()).toHaveLength(2);
    expect(tradePosts()[1]!.body.idempotency_key).toBe(tradeKey(1));
    expect(tradePosts()[1]!.body.expected_mid).toBe("100000.00000000");
    expect(uuid).toBe(1);
  });

  it("swaps in the server quote on price_changed and needs a new confirm with a new key", async () => {
    let first = true;
    ctx.trade = (body) => {
      if (first) {
        first = false;
        return refusal(409, "price_changed", "The price moved.", {
          quote: quoteBody(body, "100100.00000000"),
        });
      }
      return json(fillBody("100100.00000000"));
    };
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    expect(await screen.findByText("Price updated. Please review again.")).toBeVisible();
    expect(await previewCard().findByText("$100,100.00")).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Order filled" })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(confirmButton()).toBeEnabled();

    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()).toHaveLength(2);
    expect(tradePosts()[1]!.body.expected_mid).toBe("100100.00000000");
    expect(tradePosts()[0]!.body.idempotency_key).toBe(tradeKey(1));
    expect(tradePosts()[1]!.body.idempotency_key).toBe(tradeKey(2));
  });

  it("keeps an invalid reprice response unknown instead of inventing a new quote or attempt", async () => {
    ctx.trade = () => refusal(409, "price_changed", "The price moved.", { quote: { mid: 1 } });
    const { user } = show();
    await previewReady(user);
    const before = quotePosts().length;
    await user.click(confirmButton());
    expect(await screen.findByRole("button", { name: "Check order result" })).toBeEnabled();
    expect(screen.getByLabelText("Amount")).toBeDisabled();
    expect(quotePosts()).toHaveLength(before);
    expect(screen.queryByText("Price updated. Please review again.")).toBeNull();
  });

  it.each([
    ["insufficient_cash", 422, "You don't have enough cash."],
    ["below_minimum", 422, "The order is below the $1 minimum."],
    ["order_too_large", 422, "The order is too large."],
  ])(
    "shows the %s refusal and blocks Confirm until the input changes",
    async (code, status, message) => {
      ctx.trade = () => refusal(status, code, message);
      const { user } = show();
      await previewReady(user);
      await user.click(confirmButton());
      expect(await screen.findByRole("alert")).toHaveTextContent(message);
      expect(confirmButton()).toBeDisabled();

      await enter(user, "20");
      await waitFor(() => {
        expect(screen.queryByRole("alert")).toBeNull();
        expect(confirmButton()).toBeEnabled();
      });
      ctx.trade = (body) => json(fillBody(ctx.mid, body));
      await user.click(confirmButton());
      await screen.findByRole("heading", { name: "Order filled" });
      expect(tradePosts()[0]!.body.idempotency_key).toBe(tradeKey(1));
      expect(tradePosts()[1]!.body.idempotency_key).toBe(tradeKey(2));
    },
  );

  it("shows insufficient_quantity on a sell", async () => {
    ctx.holding = "0.00099501";
    ctx.trade = () => refusal(422, "insufficient_quantity", "You don't hold that much.");
    const { user } = show();
    await user.click(await screen.findByRole("radio", { name: "Sell" }));
    await enter(user, "5", "Quantity");
    await screen.findByText("5 BTC", { selector: "dd" });
    await waitFor(() => {
      expect(confirmButton("sell")).toBeEnabled();
    });
    await user.click(confirmButton("sell"));
    expect(await screen.findByRole("alert")).toHaveTextContent("You don't hold that much.");
    expect(confirmButton("sell")).toBeDisabled();
  });

  it("shows the stale message when the server refuses with stale_price", async () => {
    ctx.trade = () => refusal(409, "stale_price", "The price is too old.");
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Prices are out of date, so trading is paused.");
    expect(alert).toHaveTextContent("The price is too old.");
    expect(confirmButton()).toBeDisabled();
  });

  it("pauses trading while the price is not live", async () => {
    ctx.priceAge = 400;
    const { user } = show();
    expect(await screen.findByText("Stale · 6m ago")).toBeVisible();
    expect(
      screen.getByText("Prices are out of date, so trading is paused. We'll resume automatically."),
    ).toBeVisible();
    await enter(user, "100");
    await new Promise((resolve) => setTimeout(resolve, 400));
    expect(quotePosts()).toHaveLength(0);
    expect(confirmButton()).toBeDisabled();
  });

  it("sells by quantity and shows the holding", async () => {
    ctx.holding = "0.00099501";
    const { user } = show();
    await user.click(await screen.findByRole("radio", { name: "Sell" }));
    expect(screen.getByRole("radio", { name: "Sell" })).toHaveAttribute("aria-checked", "true");
    expect(screen.queryByRole("button", { name: "Amount (USD)" })).toBeNull();
    expect(await screen.findByText("You hold 0.00099501 BTC")).toBeVisible();
    await enter(user, "0.0005", "Quantity");
    await waitFor(() => {
      expect(quotePosts()).toHaveLength(1);
    });
    expect(quotePosts()[0]!.body).toEqual({ symbol: "BTC", side: "sell", quantity: "0.0005" });
    expect(await previewCard().findByText("+$99.50")).toBeVisible();
    expect(confirmButton("sell")).toBeInTheDocument();
  });

  it("redirects unknown symbols to the home page and upper-cases lowercase ones", async () => {
    show("/trade/NOPE");
    expect(await screen.findByText("Markets home")).toBeVisible();
  });

  it("accepts a lowercase symbol", async () => {
    show("/trade/btc");
    expect(await screen.findByRole("heading", { level: 1, name: "Trade BTC" })).toBeVisible();
    expect(await screen.findByText("Bitcoin")).toBeVisible();
  });

  it("redirects when the quote reports an unknown coin", async () => {
    ctx.quote = () => refusal(404, "unknown_coin", "Unknown coin.");
    const { user } = show();
    await enter(user, "100");
    expect(await screen.findByText("Markets home")).toBeVisible();
  });

  it("redirects when the trade reports an unknown coin", async () => {
    ctx.trade = () => refusal(404, "unknown_coin", "Unknown coin.");
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    expect(await screen.findByText("Markets home")).toBeVisible();
  });

  it("shows a quote failure and keeps Confirm disabled", async () => {
    ctx.quote = () => new Response("{}", { status: 500 });
    const { user } = show();
    await enter(user, "100");
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load a preview.");
    expect(confirmButton()).toBeDisabled();
  });

  it("shows the server message when the quote is refused", async () => {
    ctx.quote = () => refusal(422, "below_minimum", "The order is below the $1 minimum.");
    const { user } = show();
    await enter(user, "0.5");
    expect(await screen.findByRole("alert")).toHaveTextContent("below the $1 minimum");
  });

  it("refetches the quote every 30 seconds", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { user } = show();
    await previewReady(user);
    expect(quotePosts()).toHaveLength(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });
    expect(quotePosts().length).toBeGreaterThanOrEqual(2);
  });

  it("hides the target when the quote returns 401", async () => {
    ctx.quote = () => refusal(401, "not_authenticated", "Sign in.");
    const { user } = show();
    await screen.findByText("Bitcoin");
    await enter(user, "100");
    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Trade BTC" })).toBeNull();
    });
  });
});

it("names the ticket, confirmation and focused original receipt with scoped links", async () => {
  const { user } = show();
  await previewReady(user);
  expect(screen.getAllByText("Strategy one")).toHaveLength(2);
  expect(previewCard().getByText("Strategy one")).toBeVisible();
  await user.click(confirmButton());
  const heading = await screen.findByRole("heading", { name: "Order filled" });
  await waitFor(() => expect(heading).toHaveFocus());
  const receipt = within(screen.getByRole("region", { name: "Order filled" }));
  expect(receipt.getByText("Strategy one")).toBeVisible();
  expect(receipt.getByRole("link", { name: "Portfolio" })).toHaveAttribute("href", "/portfolios/1");
});
it("renders a long markup-like portfolio name as wrapping plain text", async () => {
  ctx.name = "<img src=x onerror=alert(1)> Strategy " + "a".repeat(22);
  show();
  const names = await screen.findAllByText(ctx.name);
  expect(names[0]).toHaveClass("min-w-0");
  expect(names[0]).toHaveClass("[overflow-wrap:anywhere]");
  expect(document.querySelector("img")).toBeNull();
});
it("does not mount prices, holdings, previews or receipts for an unavailable target", async () => {
  show("/portfolios/99/trade/BTC");
  expect(await screen.findByRole("heading", { name: "Portfolio unavailable" })).toBeVisible();
  expect(urls.some((p) => p.includes("/99/") || p === "/api/v1/prices")).toBe(false);
  expect(screen.queryByLabelText("Amount")).toBeNull();
});
it("does not label a late original fill as a sibling portfolio after navigation", async () => {
  let resolve!: (value: Response) => void;
  ctx.trade = () =>
    new Promise<Response>((done) => {
      resolve = done;
    });
  const { user } = show();
  await previewReady(user);
  await user.click(confirmButton());
  await waitFor(() => expect(tradePosts()).toHaveLength(1));
  await user.click(screen.getByRole("link", { name: "Other strategy" }));
  expect((await screen.findAllByText("Strategy two"))[0]).toBeVisible();
  await act(async () => {
    resolve(json(fillBody(ctx.mid)));
  });
  expect(screen.queryByRole("heading", { name: "Order filled" })).toBeNull();
  expect(screen.queryByText("Strategy one")).toBeNull();
  expect(urls.some((p) => p === "/api/v2/portfolios/2/trades")).toBe(false);
});
