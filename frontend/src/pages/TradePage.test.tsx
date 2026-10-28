import { act, screen, waitFor, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithClient } from "@/test/render";
import TradePage from "./TradePage";

type Ctx = {
  mid: string;
  holding: string;
  priceAge: number;
  coins: string[];
  quote: (body: Record<string, unknown>) => Response | Promise<Response>;
  trade: (body: Record<string, unknown>) => Response | Promise<Response>;
  me: () => Response;
};

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const refusal = (status: number, code: string, message: string, extra: object = {}) =>
  json({ detail: { code, message, ...extra } }, status);

const quoteBody = (body: Record<string, unknown>, mid: string) => {
  const sell = body.side === "sell";
  return {
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

const fillBody = (mid: string) => ({
  trade_id: 1,
  created_at: "2026-10-28T10:00:00Z",
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100",
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
    mid: "100000.00000000",
    holding: "0",
    priceAge: 10,
    coins: ["BTC", "ETH"],
    quote: (body) => json(quoteBody(body, ctx.mid)),
    trade: () => json(fillBody(ctx.mid)),
    me: () => json({ email: "a@example.com", cash_usd: "10000.00000000" }),
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
      if (url === "/api/v1/me") return Promise.resolve(ctx.me());
      if (url.startsWith("/api/v1/holdings/")) {
        return Promise.resolve(json({ symbol: "BTC", quantity: ctx.holding }));
      }
      if (url === "/api/v1/trades/quote" || url === "/api/v1/trades") {
        const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
        posts.push({ url, body });
        return Promise.resolve(url === "/api/v1/trades" ? ctx.trade(body) : ctx.quote(body));
      }
      return Promise.resolve(new Response(null, { status: 204 }));
    }),
  );
}

const tradePosts = () => posts.filter((p) => p.url === "/api/v1/trades");
const quotePosts = () => posts.filter((p) => p.url === "/api/v1/trades/quote");
const countUrl = (url: string) => urls.filter((u) => u === url).length;

function show(route = "/trade/BTC") {
  return renderWithClient(
    <Routes>
      <Route path="/trade/:symbol" element={<TradePage />} />
      <Route path="/" element={<p>Markets home</p>} />
    </Routes>,
    { route },
  );
}

type User = ReturnType<typeof show>["user"];

async function enter(user: User, value: string, label = "Amount") {
  const field = await screen.findByLabelText(label);
  await user.clear(field);
  await user.type(field, value);
}

const previewCard = () => within(screen.getByRole("heading", { name: "Preview" }).parentElement!);
const confirmButton = (side = "buy") => screen.getByRole("button", { name: `Confirm ${side}` });

async function previewReady(user: User, value = "100") {
  await enter(user, value);
  await screen.findByText("0.00099501 BTC");
  await waitFor(() => {
    expect(confirmButton()).toBeEnabled();
  });
}

let uuid = 0;

beforeEach(() => {
  document.cookie = "bj_csrf=tok; path=/";
  uuid = 0;
  vi.spyOn(crypto, "randomUUID").mockImplementation(
    () => `key-${++uuid}` as unknown as ReturnType<typeof crypto.randomUUID>,
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
    expect(screen.getByRole("heading", { level: 1, name: "Trade BTC" })).toBeVisible();
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
      me: countUrl("/api/v1/me"),
      holding: countUrl("/api/v1/holdings/BTC"),
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
      idempotency_key: "key-1",
    });
    const card = within(screen.getByRole("heading", { name: "Order filled" }).parentElement!);
    expect(card.getByText("0.00099501 BTC")).toBeVisible();
    expect(card.getByText("$100,250.00")).toBeVisible();
    expect(card.getByText("$0.25")).toBeVisible();
    expect(card.getByText("-$100.00")).toBeVisible();
    expect(card.getByText("$9,900.00")).toBeVisible();
    await waitFor(() => {
      expect(countUrl("/api/v1/me")).toBeGreaterThan(before.me);
      expect(countUrl("/api/v1/holdings/BTC")).toBeGreaterThan(before.holding);
      expect(countUrl("/api/v1/prices")).toBeGreaterThan(before.prices);
    });

    await user.click(screen.getByRole("button", { name: "New order" }));
    expect(screen.getByRole("heading", { name: "Preview" })).toBeVisible();
    expect(screen.getByLabelText("Amount")).toHaveValue("");
    // A fill ends the attempt: the next order gets a new key.
    await previewReady(user);
    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()[1]!.body.idempotency_key).toBe("key-2");
  });

  it("sends exactly one request on a double click", async () => {
    ctx.trade = () =>
      new Promise((resolve) => setTimeout(() => resolve(json(fillBody(ctx.mid))), 80));
    const { user } = show();
    await previewReady(user);
    await user.dblClick(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()).toHaveLength(1);
  });

  it("keeps the key across a network-error retry and replaces it after an edit", async () => {
    let fail = true;
    ctx.trade = () => {
      if (fail) return Promise.reject(new TypeError("network"));
      return json(fillBody(ctx.mid));
    };
    const { user } = show();
    await previewReady(user);
    await user.click(confirmButton());
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't confirm. Check your connection and try again.",
    );
    await user.click(confirmButton());
    await waitFor(() => {
      expect(tradePosts()).toHaveLength(2);
    });
    expect(tradePosts()[0]!.body.idempotency_key).toBe("key-1");
    expect(tradePosts()[1]!.body.idempotency_key).toBe("key-1");

    await enter(user, "50");
    await waitFor(() => {
      expect(confirmButton()).toBeEnabled();
    });
    await screen.findByText("0.00099501 BTC");
    expect(screen.queryByRole("alert")).toBeNull();
    fail = false;
    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()[2]!.body.idempotency_key).toBe("key-2");
  });

  it("reuses the key when a quote refetch moves the mid between a failed attempt and the retry", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let fail = true;
    ctx.trade = () => {
      if (fail) return Promise.reject(new TypeError("network"));
      return json(fillBody(ctx.mid));
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
    await user.click(confirmButton());
    await screen.findByRole("heading", { name: "Order filled" });
    expect(tradePosts()).toHaveLength(2);
    expect(tradePosts()[1]!.body.idempotency_key).toBe("key-1");
    expect(tradePosts()[1]!.body.expected_mid).toBe("100050.00000000");
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
    expect(tradePosts()[0]!.body.idempotency_key).toBe("key-1");
    expect(tradePosts()[1]!.body.idempotency_key).toBe("key-2");
  });

  it("re-quotes when price_changed carries no usable quote", async () => {
    ctx.trade = () => refusal(409, "price_changed", "The price moved.", { quote: { mid: 1 } });
    const { user } = show();
    await previewReady(user);
    const before = quotePosts().length;
    await user.click(confirmButton());
    expect(await screen.findByText("Price updated. Please review again.")).toBeVisible();
    await waitFor(() => {
      expect(quotePosts().length).toBeGreaterThan(before);
    });
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
      ctx.trade = () => json(fillBody(ctx.mid));
      await user.click(confirmButton());
      await screen.findByRole("heading", { name: "Order filled" });
      expect(tradePosts()[0]!.body.idempotency_key).toBe("key-1");
      expect(tradePosts()[1]!.body.idempotency_key).toBe("key-2");
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

  it("refreshes the session state when the quote returns 401", async () => {
    ctx.quote = () => refusal(401, "not_authenticated", "Sign in.");
    const { user } = show();
    await screen.findByText("Bitcoin");
    const before = countUrl("/api/v1/me");
    await enter(user, "100");
    await waitFor(() => {
      expect(countUrl("/api/v1/me")).toBeGreaterThan(before);
    });
  });
});
