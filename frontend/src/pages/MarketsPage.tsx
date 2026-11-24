import { useRef, useState } from "react";
import { Link } from "react-router";
import { MarketOpening } from "@/components/MarketOpening";
import type { StockItem } from "@/api/stocks";
import { stockActionSummary } from "@/lib/stockActionCopy";
import { useNow } from "@/hooks/useNow";
import { usePrices } from "@/hooks/usePrices";
import { useStocks } from "@/hooks/useStocks";
import { formatAge, freshnessStatus, statusLabel } from "@/lib/age";
import { formatUnitPrice } from "@/lib/money";
import "./markets.css";

type Market = "crypto" | "stock";

const stockRestrictions: Record<StockItem["execution_reason"], string> = {
  available: "Market open",
  phase_disabled: "Stock trading is unavailable.",
  permission_unavailable: "Stock data is paused.",
  action_unavailable: "Corporate-action checks unavailable.",
  units_changed: "Stock units changed. Waiting for a new quote.",
  halted: "Trading halted.",
  frozen: "Trading frozen.",
  status_unavailable: "Stock status is unverified.",
  session_unavailable: "Market hours haven’t been confirmed.",
  market_closed: "Market closed.",
  quote_unavailable: "Waiting for a verified IEX quote.",
  quote_stale: "This quote is out of date.",
  receipt_unavailable: "Check the previous order result before trading again.",
};

export default function MarketsPage({ portfolioId }: { portfolioId?: string }) {
  const [market, setMarket] = useState<Market>("crypto");
  const [search, setSearch] = useState("");
  const [selection, setSelection] = useState<string>();
  const [showAsset, setShowAsset] = useState(false);
  const assetHeading = useRef<HTMLHeadingElement>(null);
  const selectedRow = useRef<HTMLButtonElement>(null);
  const prices = usePrices();
  const stocks = useStocks();
  const stockMarket = market === "stock";
  const query = stockMarket ? stocks : prices;
  const now = useNow(1000);
  const permitted = stocks.data?.admission.state === "approved";
  const coins = prices.data?.items ?? [];
  const stockItems = stocks.data?.items ?? [];
  const assets = stockMarket
    ? stockItems.map((item) => ({
        symbol: item.symbol,
        name: item.company_name,
        age_seconds: undefined,
        price: permitted ? item.quote?.mid : undefined,
      }))
    : coins;
  const term = search.trim().toLowerCase();
  const results = assets.filter(
    ({ symbol, name }) => symbol.toLowerCase().includes(term) || name.toLowerCase().includes(term),
  );
  const asset = results.find(({ symbol }) => symbol === selection) ?? results[0];
  const coin = stockMarket ? undefined : coins.find(({ symbol }) => symbol === asset?.symbol);
  const stock = stockMarket ? stockItems.find(({ symbol }) => symbol === asset?.symbol) : undefined;
  const marketClosed = stock?.session.state === "closed";
  const elapsed = Math.max(0, Math.floor((now - prices.dataUpdatedAt) / 1000));
  const age = coin ? coin.age_seconds + elapsed : null;
  const fresh =
    age !== null &&
    prices.data &&
    freshnessStatus(age, prices.data.fresh_seconds, prices.data.stale_seconds) === "fresh";
  const stockQuote = permitted ? stock?.quote : null;
  const stockRestriction = stock
    ? !permitted
      ? stockRestrictions.permission_unavailable
      : stock.session.state === "unknown" && stock.action.state === "unknown"
        ? stockRestrictions.session_unavailable
        : stock.action.state !== "current"
          ? stockActionSummary(stock.action)
          : stock.session.state === "unknown"
            ? stockRestrictions.session_unavailable
            : stock.execution_reason === "phase_disabled" && stock.quote_reason === "stale"
              ? stockRestrictions.quote_stale
              : stock.execution_reason === "phase_disabled" && stock.quote_reason === "missing"
                ? stockRestrictions.quote_unavailable
                : stockRestrictions[stock.execution_reason]
    : null;
  const action = stock
    ? stock.execution_enabled && permitted && !marketClosed
      ? "Trade"
      : "View details"
    : fresh
      ? "Trade"
      : "Check price";
  const prefix = portfolioId ? `/portfolios/${encodeURIComponent(portfolioId)}` : "";
  const price = asset?.price
    ? formatUnitPrice(asset.price)
    : stockMarket
      ? null
      : "Price unavailable";

  function selectMarket(next: Market) {
    if (next === market) return;
    setMarket(next);
    setSearch("");
    setSelection(undefined);
    setShowAsset(false);
  }

  return (
    <div className="markets mx-auto my-7 max-w-[1280px] md:my-12 lg:my-16">
      <h1 className="sr-only">Markets</h1>
      <div className="grid min-w-0 grid-cols-1 gap-8 md:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] md:gap-10 lg:gap-16">
        <section
          aria-label="Find an asset"
          className={showAsset && asset ? "hidden md:block" : undefined}
        >
          <div
            role="group"
            aria-label="Asset class"
            className="mb-5 flex gap-7 border-b md:gap-9 border-[var(--market-line)]"
          >
            <button
              type="button"
              aria-pressed={!stockMarket}
              className="market-tab"
              onClick={() => selectMarket("crypto")}
            >
              Crypto
            </button>
            <button
              type="button"
              aria-pressed={stockMarket}
              className="market-tab"
              onClick={() => selectMarket("stock")}
            >
              US stocks
            </button>
          </div>
          <label htmlFor="market-search" className="sr-only">
            Search by name or symbol
          </label>
          <input
            id="market-search"
            type="search"
            value={search}
            placeholder="Search by name or symbol"
            className="mb-5 min-h-13 w-full rounded-sm border border-[var(--market-input)] px-4 placeholder:text-[var(--market-muted)] md:min-h-14"
            onChange={(event) => {
              setSearch(event.target.value);
              setShowAsset(false);
            }}
          />
          {query.isPending ? (
            <p role="status">Loading {stockMarket ? "stocks" : "prices"}…</p>
          ) : query.isError || (stockMarket && stocks.data && !permitted && !marketClosed) ? (
            <div role="status" className="mb-3 flex flex-wrap items-center gap-3 text-sm">
              <p>
                {query.isError
                  ? query.data
                    ? "Couldn’t refresh. Showing the last available update."
                    : "Couldn’t load this market."
                  : stockRestrictions.permission_unavailable}
              </p>
              <button
                type="button"
                className="min-h-11 underline"
                disabled={query.isFetching}
                onClick={() => void query.refetch()}
              >
                Try again
              </button>
            </div>
          ) : null}
          {stockMarket && permitted && stockItems.some((item) => item.quote) && (
            <p className="mb-2 text-xs text-[var(--market-muted)]">
              IEX prices · Midpoint
              {stocks.data?.attribution.required_text && (
                <span className="block">{stocks.data.attribution.required_text}</span>
              )}
            </p>
          )}
          {results.length > 0 ? (
            <ul
              aria-label={stockMarket ? "US stocks" : "Crypto"}
              className="border-t border-[var(--market-ink)]"
            >
              {results.map((item) => {
                const { symbol, name, price: value } = item;
                const status =
                  item.age_seconds !== undefined && prices.data
                    ? freshnessStatus(
                        item.age_seconds + elapsed,
                        prices.data.fresh_seconds,
                        prices.data.stale_seconds,
                      )
                    : undefined;
                return (
                  <li key={symbol} className="border-b border-[var(--market-line)]">
                    <button
                      type="button"
                      ref={asset?.symbol === symbol ? selectedRow : undefined}
                      aria-current={asset?.symbol === symbol ? true : undefined}
                      className="market-row grid min-h-17 w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-3 py-3 text-left md:min-h-20 md:px-5 md:text-lg"
                      onClick={() => {
                        setSelection(symbol);
                        setShowAsset(true);
                        if (window.matchMedia?.("(max-width: 767px)").matches) {
                          requestAnimationFrame(() => assetHeading.current?.focus());
                        }
                      }}
                    >
                      <span className="min-w-0 wrap-anywhere">
                        <span className="block font-semibold">{name}</span>{" "}
                        {symbol !== name && (
                          <span className="block text-sm text-[var(--market-muted)]">{symbol}</span>
                        )}
                      </span>
                      {value && (
                        <>
                          {" "}
                          <span className="text-right tabular-nums">
                            {formatUnitPrice(value)}
                            {status && status !== "fresh" && (
                              <span className="block text-sm text-[var(--market-muted)]">
                                {" "}
                                {statusLabel(status)}
                              </span>
                            )}
                          </span>
                        </>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : !query.isPending && !query.isError ? (
            <p role="status">
              {term
                ? "No assets match your search."
                : "Prices are loading. They appear within a minute."}
            </p>
          ) : null}
        </section>
        {asset && (
          <section
            aria-labelledby="market-asset"
            className={`${showAsset ? "" : "hidden md:block"} min-w-0 border-t border-[var(--market-line)] pt-5 md:sticky md:top-8 md:self-start md:border-t-0 md:border-l md:pt-6 md:pl-9 lg:pl-12`}
          >
            <button
              type="button"
              className="mb-3 min-h-11 underline md:hidden"
              onClick={() => {
                setShowAsset(false);
                requestAnimationFrame(() => selectedRow.current?.focus());
              }}
            >
              All assets
            </button>
            <h2
              id="market-asset"
              ref={assetHeading}
              tabIndex={-1}
              className="text-3xl font-semibold tracking-tight wrap-anywhere lg:text-4xl"
            >
              {asset.name}
            </h2>
            <p className="mt-2 text-[var(--market-muted)]">
              {asset.symbol} · {stock?.listing_exchange ?? "USD"}
            </p>
            <div className="my-7 border-y border-[var(--market-line)] py-5 md:py-7">
              {price && (
                <p className="text-[clamp(2rem,4vw,3.25rem)] leading-tight font-semibold tracking-tight wrap-anywhere tabular-nums">
                  {price}
                </p>
              )}
              {coin && age !== null && (
                <p className="mt-2 text-[var(--market-muted)]">
                  <time dateTime={coin.as_of} title={coin.as_of}>
                    Updated {formatAge(age)}
                  </time>
                  {!fresh && " · Trading needs a fresh price"}
                </p>
              )}
              {stockQuote && !marketClosed && (
                <p className="mt-2 text-[var(--market-muted)]">
                  IEX midpoint ·{" "}
                  <time dateTime={stockQuote.event_at} title={stockQuote.event_at}>
                    Updated {formatAge(stockQuote.age_seconds)}
                  </time>
                </p>
              )}
              {marketClosed && (
                <div className="mt-2 text-[var(--market-muted)]">
                  <p role="status" className="font-medium">
                    Market closed
                  </p>
                  <p className="empty:hidden">
                    <MarketOpening nextOpen={stock?.session.next_open_at} now={now} />
                  </p>
                </div>
              )}
              {stock && !marketClosed && (
                <div className="mt-2 space-y-2">
                  <p
                    role="status"
                    className={
                      permitted
                        ? "text-[var(--market-muted)]"
                        : "text-[var(--market-muted)] md:hidden"
                    }
                  >
                    {stockRestriction}
                  </p>
                </div>
              )}
            </div>
            <Link
              className="market-action inline-flex min-h-13 w-full items-center justify-center rounded-sm px-8 py-3 font-semibold md:w-auto"
              to={`${prefix}/trade/${stockMarket ? "stocks/" : ""}${encodeURIComponent(asset.symbol)}`}
              aria-label={`${action} ${asset.symbol}`}
            >
              {action}
            </Link>
            {stockQuote && stocks.data?.attribution.required_text && (
              <p className="mt-3 text-xs text-[var(--market-muted)] md:hidden">
                {stocks.data.attribution.required_text}
              </p>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
