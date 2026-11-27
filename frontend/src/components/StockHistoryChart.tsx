import { historyRanges, type HistoryRange } from "@/api/marketHistory";

const widgetOrigin = "https://www.tradingview-widget.com";
const ranges = {
  "1D": { symbolRange: "1D", widgetRange: "1d|5", label: "Past day" },
  "1W": { symbolRange: "5D", widgetRange: "5d|5", label: "Past 5 trading days" },
  "1M": { symbolRange: "1M", widgetRange: "1m|30", label: "Past month" },
} as const;

function widgetSymbol(exchange: string, ticker: string) {
  if (exchange !== "NYSE" && exchange !== "NASDAQ") return null;
  if (!/^[A-Z0-9][A-Z0-9.-]{0,13}$/.test(ticker)) return null;
  return `${exchange}:${ticker}`;
}

export function StockHistoryChart({
  exchange,
  ticker,
  range,
  onRange,
}: {
  exchange: string;
  ticker: string;
  range: HistoryRange;
  onRange: (range: HistoryRange) => void;
}) {
  const symbol = widgetSymbol(exchange, ticker);
  if (!symbol) return null;

  const selected = ranges[range];
  // Match the official iframe bootstrap's public URL without loading its
  // script into the signed-in application document.
  const url = new URL("/embed-widget/symbol-overview/", widgetOrigin);
  url.searchParams.set("locale", "en");
  url.hash = encodeURIComponent(
    JSON.stringify({
      symbols: [[`${symbol}|${selected.symbolRange}`]],
      dateRanges: [selected.widgetRange],
      chartOnly: true,
      hideDateRanges: true,
      colorTheme: "light",
      isTransparent: true,
      autosize: true,
    }),
  );
  const sourceUrl = new URL("https://www.tradingview.com/chart/");
  sourceUrl.searchParams.set("symbol", symbol);

  return (
    <section className="market-history" aria-label="Price history">
      <div className="market-history-toolbar">
        <p className="text-sm text-muted-foreground">{selected.label}</p>
        <div className="market-history-ranges" role="group" aria-label="Price history range">
          {historyRanges.map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={option === range}
              onClick={() => onRange(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      <iframe
        key={url.href}
        className="market-history-plot border-0"
        title={`${ticker} price history · ${selected.label}`}
        src={url.href}
        sandbox="allow-scripts allow-same-origin"
        referrerPolicy="no-referrer"
        loading="lazy"
      />
      <div className="market-history-caption">
        <span>Delayed stock prices</span>
        <a
          className="inline-flex min-h-11 items-center underline underline-offset-2"
          href={sourceUrl.href}
          target="_blank"
          rel="noreferrer"
        >
          Open chart on TradingView
        </a>
      </div>
    </section>
  );
}
