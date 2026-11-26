import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { MarketOpening } from "@/components/MarketOpening";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";
import { ApiError } from "@/api/client";
import type { StockCatalogItem } from "@/api/stockCatalog";
import type { StockItem } from "@/api/stocks";
import { stockActionSummary } from "@/lib/stockActionCopy";
import { useNow } from "@/hooks/useNow";
import { usePrices } from "@/hooks/usePrices";
import {
  catalogDisplay,
  useSelectedCatalogPrice,
  useStockCatalogSearch,
} from "@/hooks/useStockCatalog";
import { useStocks } from "@/hooks/useStocks";
import { formatAge, freshnessStatus, statusLabel } from "@/lib/age";
import { fullLocalTimestamp } from "@/lib/financialDisplay";
import { formatUnitPrice } from "@/lib/money";
import "./markets.css";

type Market = "crypto" | "stock";
type MarketRow = {
  key: string;
  symbol: string;
  name: string;
  age_seconds?: number;
  price?: string;
  listing?: StockCatalogItem;
};

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

export default function MarketsPage({
  portfolioId,
  onSelectPortfolio,
  portfolioBlock,
}: {
  portfolioId?: string;
  onSelectPortfolio?: (id: string) => void;
  portfolioBlock?: "pending" | "unavailable";
}) {
  const [market, setMarket] = useState<Market>("stock");
  const [search, setSearch] = useState("");
  const [composing, setComposing] = useState(false);
  const [submittedSearch, setSubmittedSearch] = useState("");
  const [catalogIntent, setCatalogIntent] = useState<StockCatalogItem | null>(null);
  const [selection, setSelection] = useState<string>();
  const assetHeading = useRef<HTMLHeadingElement>(null);
  const selectedRow = useRef<HTMLButtonElement>(null);
  const searchField = useRef<HTMLInputElement>(null);
  const restoreFocusFromRemovedDetail = useCallback((panel: HTMLElement | null) => {
    if (!panel) return;
    return () => {
      if (!panel.contains(document.activeElement)) return;
      requestAnimationFrame(() => {
        if (!panel.isConnected && document.activeElement === document.body) {
          searchField.current?.focus();
        }
      });
    };
  }, []);
  const prices = usePrices();
  const stocks = useStocks();
  const stockMarket = market === "stock";
  const query = stockMarket ? stocks : prices;
  const input = search.trim();
  const searchingStocks = stockMarket && !composing && input.length > 0;
  const searchReady = searchingStocks && submittedSearch === input;
  useEffect(() => {
    if (!searchingStocks) return;
    const timeout = window.setTimeout(() => setSubmittedSearch(input), 250);
    return () => window.clearTimeout(timeout);
  }, [input, searchingStocks]);
  const catalog = useStockCatalogSearch(searchReady ? input : null);
  const catalogData = searchReady && catalog.data?.state === "ready" ? catalog.data : null;
  const waitingForCatalog =
    searchingStocks && catalog.enabled && (!searchReady || (catalog.isPending && !catalogData));
  const catalogUnavailable =
    searchReady && catalog.enabled && (catalog.isError || catalog.data?.state === "unavailable");
  const now = useNow(1000);
  const permitted = stocks.data?.admission.state === "approved";
  const coins = prices.data?.items ?? [];
  const stockItems = stocks.data?.items ?? [];
  const assets: MarketRow[] = stockMarket
    ? stockItems.map((item) => ({
        key: item.symbol,
        symbol: item.symbol,
        name: item.company_name,
        price: permitted ? item.quote?.mid : undefined,
      }))
    : coins.map((item) => ({ ...item, key: item.symbol }));
  const term = input.toLowerCase();
  const results: MarketRow[] = catalogData
    ? catalogData.items.map((item) => ({
        key: item.catalog_id,
        symbol: item.ticker,
        name: item.company_name,
        listing: item,
      }))
    : waitingForCatalog
      ? []
      : assets.filter(
          ({ symbol, name }) =>
            symbol.toLowerCase().includes(term) || name.toLowerCase().includes(term),
        );
  const asset = catalogData
    ? results.find(({ key }) => key === catalogIntent?.catalog_id)
    : catalogIntent
      ? undefined
      : (results.find(({ key }) => key === selection) ?? results[0]);
  const catalogListing = asset?.listing;
  const versionChanged =
    catalogListing !== undefined &&
    catalogListing.listing_version !== catalogIntent?.listing_version;
  const selectedQuote = useSelectedCatalogPrice(
    versionChanged ? null : (catalogListing ?? null),
    now,
  );
  const quoteView = selectedQuote.data;
  const catalogMark = quoteView ? catalogDisplay(quoteView, now) : null;
  const catalogRestriction = quoteView?.execution_reason;
  const executionMessage =
    catalogRestriction && catalogRestriction !== "read_only" && catalogRestriction !== "available"
      ? stockRestrictions[catalogRestriction]
      : null;
  const priceError = selectedQuote.error instanceof ApiError ? selectedQuote.error.code : null;
  const listingChanged = versionChanged || priceError === "listing_changed";
  const missingListing = priceError === "stock_catalog_not_found";
  const quoteFailure = listingChanged
    ? versionChanged
      ? "This listing changed. Select it again to check its price."
      : "This listing changed. Refresh stock search."
    : missingListing
      ? "This listing is no longer available."
      : priceError === "queue_full"
        ? "Stock price requests are temporarily limited."
        : selectedQuote.isError
          ? "Couldn’t load this stock price."
          : (catalogMark?.message ?? executionMessage);
  const retryPrice =
    (!listingChanged && !missingListing && selectedQuote.isError) || catalogMark?.retryable;
  const coin = stockMarket ? undefined : coins.find(({ symbol }) => symbol === asset?.symbol);
  const stock =
    stockMarket && !catalogListing
      ? stockItems.find(({ symbol }) => symbol === asset?.symbol)
      : undefined;
  const marketClosed = catalogListing ? catalogMark?.closed : stock?.session.state === "closed";
  const nextOpen = catalogListing ? quoteView?.session.next_open_at : stock?.session.next_open_at;
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
  const action = catalogListing
    ? quoteView?.read_only === false &&
      catalogRestriction === "available" &&
      !selectedQuote.isError &&
      !marketClosed &&
      catalogMark?.quote
      ? "Trade"
      : "View details"
    : stock
      ? stock.execution_enabled && permitted && !marketClosed
        ? "Trade"
        : "View details"
      : fresh
        ? "Trade"
        : "Check price";
  const prefix = portfolioId ? `/portfolios/${encodeURIComponent(portfolioId)}` : "";
  const rawPrice = catalogMark?.quote?.mid ?? asset?.price;
  const price = rawPrice ? formatUnitPrice(rawPrice) : stockMarket ? null : "Price unavailable";
  const closingMarkTime = marketClosed
    ? (catalogMark?.quote?.event_at ?? stockQuote?.event_at)
    : undefined;

  function selectMarket(next: Market) {
    if (next === market) return;
    setMarket(next);
    setSearch("");
    setSubmittedSearch("");
    setComposing(false);
    setCatalogIntent(null);
    setSelection(undefined);
  }

  function pickAsset(item: MarketRow) {
    setCatalogIntent(item.listing ?? null);
    setSelection(item.key);
    if (window.matchMedia?.("(width < 48rem)").matches) {
      requestAnimationFrame(() => assetHeading.current?.focus());
    }
  }

  return (
    <div className="markets mx-auto my-7 max-w-[1280px] md:my-12 lg:my-16">
      <h1 className="sr-only">Markets</h1>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div role="group" aria-label="Asset class" className="flex gap-6 md:gap-8">
          <button
            type="button"
            aria-pressed={stockMarket}
            className="market-tab"
            onClick={() => selectMarket("stock")}
          >
            US stocks
          </button>
          <button
            type="button"
            aria-pressed={!stockMarket}
            className="market-tab"
            onClick={() => selectMarket("crypto")}
          >
            Crypto
          </button>
        </div>
        {onSelectPortfolio && (
          <PortfolioSwitcher portfolioId={portfolioId} onSelect={onSelectPortfolio} inline />
        )}
      </div>
      <div className="market-workspace grid min-w-0 grid-cols-1 items-start gap-6 md:gap-8">
        <section aria-label="Find an asset" className="min-w-0">
          <label
            htmlFor="market-search"
            className={stockMarket ? "mb-2 block font-medium" : "sr-only"}
          >
            {stockMarket ? "Search stocks" : "Search by name or symbol"}
          </label>
          <input
            id="market-search"
            ref={searchField}
            type="search"
            value={search}
            maxLength={stockMarket ? 80 : undefined}
            placeholder={stockMarket ? "Name or ticker" : "Search by name or symbol"}
            onCompositionStart={() => setComposing(true)}
            onCompositionEnd={(event) => {
              setSearch(event.currentTarget.value);
              setComposing(false);
            }}
            className="mb-5 min-h-13 w-full rounded-sm border border-[var(--market-input)] px-4 placeholder:text-[var(--market-muted)] md:min-h-14"
            onChange={(event) => {
              setSearch(event.target.value);
              setSubmittedSearch("");
              setCatalogIntent(null);
            }}
          />
          {waitingForCatalog && <p role="status">Searching stocks…</p>}
          {catalogUnavailable && (
            <div role="status" className="mb-3 flex flex-wrap items-center gap-3 text-sm">
              <p>
                {catalogData
                  ? "Couldn’t refresh stock search. Showing the last available results."
                  : "Catalog search is unavailable. The original stocks are still available."}
              </p>
              <button
                type="button"
                className="min-h-11 underline"
                disabled={catalog.isFetching}
                onClick={() => void catalog.refetch()}
              >
                Try stock search again
              </button>
            </div>
          )}
          {catalogData && results.length > 0 && (
            <p
              role="status"
              className={
                catalogData.has_more ? "mb-3 text-sm text-[var(--market-muted)]" : "sr-only"
              }
            >
              {catalogData.has_more
                ? "More than 20 stocks match. Refine your search."
                : `${results.length} ${results.length === 1 ? "stock matches" : "stocks match"} your search.`}
            </p>
          )}
          {!catalogData &&
            !waitingForCatalog &&
            !catalogUnavailable &&
            (query.isPending ? (
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
            ) : null)}
          {!catalogData &&
            !waitingForCatalog &&
            stockMarket &&
            permitted &&
            stockItems.some((item) => item.quote) && (
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
              className="market-list border-y border-border"
            >
              {results.map((item) => {
                const { key, symbol, name, price: value, listing } = item;
                const status =
                  item.age_seconds !== undefined && prices.data
                    ? freshnessStatus(
                        item.age_seconds + elapsed,
                        prices.data.fresh_seconds,
                        prices.data.stale_seconds,
                      )
                    : undefined;
                return (
                  <li key={key} className="border-b border-border last:border-b-0">
                    <button
                      type="button"
                      ref={asset?.key === key ? selectedRow : undefined}
                      aria-current={asset?.key === key ? true : undefined}
                      className="market-row grid min-h-16 w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-4 px-3 py-2 text-left"
                      onClick={() => pickAsset(item)}
                    >
                      <span className="flex min-w-0 flex-col wrap-anywhere">
                        {(listing || symbol !== name) && (
                          <span className="order-2 text-sm text-muted-foreground">{name}</span>
                        )}{" "}
                        <span className="font-semibold">
                          {symbol}
                          {listing && ` · ${listing.listing_exchange}`}
                          {listing?.share_class && ` · Class ${listing.share_class}`}
                        </span>
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
          ) : catalogData ? (
            <p role="status">No matching stocks. Try another name or ticker.</p>
          ) : !waitingForCatalog && !catalogUnavailable && !query.isPending && !query.isError ? (
            <p role="status">
              {term
                ? stockMarket
                  ? "No matching stocks. Try another name or ticker."
                  : "No assets match your search."
                : "Prices are loading. They appear within a minute."}
            </p>
          ) : null}
        </section>
        {asset && (
          <section
            ref={restoreFocusFromRemovedDetail}
            aria-labelledby="market-asset"
            className="min-w-0 rounded-card border border-border bg-card p-5 md:p-7"
          >
            <button
              type="button"
              className="mb-3 min-h-11 underline md:hidden"
              onClick={() => {
                requestAnimationFrame(() => (selectedRow.current ?? searchField.current)?.focus());
              }}
            >
              Back to results
            </button>
            <h2
              id="market-asset"
              ref={assetHeading}
              tabIndex={-1}
              className="scroll-mt-4 text-2xl font-semibold tracking-tight wrap-anywhere"
            >
              {asset.name}
            </h2>
            <p className="mt-2 wrap-anywhere text-[var(--market-muted)]">
              {asset.symbol} ·{" "}
              {catalogListing?.listing_exchange ?? stock?.listing_exchange ?? "USD"}
              {catalogListing?.share_class && ` · Class ${catalogListing.share_class}`}
            </p>
            <div className="my-5 border-y border-border py-5 md:my-6 md:py-6">
              {price && (
                <p
                  className="text-[clamp(2rem,4vw,3.25rem)] leading-tight font-semibold tracking-tight wrap-anywhere tabular-nums"
                  title={closingMarkTime ? fullLocalTimestamp(closingMarkTime) : undefined}
                >
                  {price}
                  {closingMarkTime && (
                    <time className="sr-only" dateTime={closingMarkTime}>
                      {" As of "}
                      {fullLocalTimestamp(closingMarkTime)}
                    </time>
                  )}
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
              {catalogListing && !marketClosed && catalogMark?.quote && (
                <p className="mt-2 text-[var(--market-muted)]">
                  IEX midpoint ·{" "}
                  <time dateTime={catalogMark.quote.event_at} title={catalogMark.quote.event_at}>
                    {new Date(catalogMark.quote.event_at).toLocaleString()}
                  </time>
                </p>
              )}
              {catalogListing && !marketClosed && (selectedQuote.isFetching || quoteFailure) && (
                <p role="status" className="mt-2 text-[var(--market-muted)]">
                  {selectedQuote.isFetching ? "Checking stock price…" : quoteFailure}
                </p>
              )}
              {catalogListing && (priceError === "listing_changed" || missingListing) && (
                <button
                  type="button"
                  className="min-h-11 underline"
                  onClick={() => {
                    setCatalogIntent(null);
                    void catalog.refetch();
                    requestAnimationFrame(() => searchField.current?.focus());
                  }}
                >
                  Refresh stock search
                </button>
              )}
              {catalogListing && !marketClosed && retryPrice && !selectedQuote.isFetching && (
                <button
                  type="button"
                  className="min-h-11 underline"
                  onClick={() => void selectedQuote.refetch()}
                >
                  Retry price
                </button>
              )}
              {marketClosed && (
                <div className="mt-2 text-[var(--market-muted)]">
                  <p role="status" className="font-medium">
                    Market closed
                  </p>
                  <p className="empty:hidden">
                    <MarketOpening nextOpen={nextOpen} now={now} />
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
            {portfolioBlock === "pending" && (
              <p className="text-muted-foreground" role="status">
                Checking your trading portfolio…
              </p>
            )}
            {portfolioBlock === "unavailable" && (
              <Link className="inline-flex min-h-11 items-center underline" to="/portfolios">
                Choose an available portfolio
              </Link>
            )}
            {!portfolioBlock &&
              !listingChanged &&
              !missingListing &&
              (!catalogListing || !selectedQuote.isFetching) && (
                <Link
                  className="market-action inline-flex min-h-11 items-center justify-center rounded-pill px-5 py-2 font-semibold"
                  to={
                    catalogListing
                      ? `${prefix}/trade/catalog/${catalogListing.catalog_id}`
                      : `${prefix}/trade/${stockMarket ? "stocks/" : ""}${encodeURIComponent(asset.symbol)}`
                  }
                  aria-label={`${action} ${asset.symbol}`}
                >
                  {action}
                </Link>
              )}
            {stockQuote && stocks.data?.attribution.required_text && (
              <p className="mt-3 text-xs text-[var(--market-muted)] md:hidden">
                {stocks.data.attribution.required_text}
              </p>
            )}
          </section>
        )}
        {!asset && catalogData && results.length > 0 && (
          <section
            aria-label="Asset details"
            className="hidden rounded-card border border-border bg-card p-7 text-muted-foreground md:block"
          >
            Select a stock to see its price.
          </section>
        )}
      </div>
    </div>
  );
}
