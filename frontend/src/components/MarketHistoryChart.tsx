import { useEffect, useRef } from "react";
import {
  historyRanges,
  type HistoryRange,
  type HistoryResponse,
  type HistorySeries,
} from "@/api/marketHistory";
import { fullLocalTimestamp, outcome, signedPercent } from "@/lib/financialDisplay";

const periods: Record<HistoryRange, string> = {
  "1D": "Past day",
  "1W": "Past week",
  "1M": "Past month",
};
const priceAxis = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumSignificantDigits: 5,
});
const precisePriceAxis = new Intl.NumberFormat("en-US", {
  ...priceAxis.resolvedOptions(),
  maximumSignificantDigits: 7,
});
const exactPrice = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 12,
});
const clock = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });
const dateLabel = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const historyAsOf = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function drawChart(canvas: HTMLCanvasElement, series: HistorySeries, range: HistoryRange) {
  const { width, height } = canvas.getBoundingClientRect();
  if (width < 80 || height < 40) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const density = Math.min(window.devicePixelRatio || 1, 3);
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  ctx.scale(density, density);

  // Number conversion is confined to the display canvas. The table keeps the exact decimals.
  const prices = series.points.map(({ close }) => Number(close));
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const padding = Math.max((max - min) * 0.12, max * 0.0001);
  const low = Math.max(0, min - padding);
  const high = max + padding;
  const styles = getComputedStyle(canvas);
  ctx.font = `11px ${styles.fontFamily}`;
  const tickValues = Array.from({ length: 5 }, (_, index) => high - ((high - low) * index) / 4);
  const roundedTicks = tickValues.map((value) => priceAxis.format(value));
  const ticks =
    new Set(roundedTicks).size === roundedTicks.length
      ? roundedTicks
      : tickValues.map((value) => precisePriceAxis.format(value));
  const axisWidth = Math.max(56, ...ticks.map((label) => ctx.measureText(label).width + 12));
  const right = width - axisWidth;
  const top = 10;
  const bottom = height - 28;
  const start = Date.parse(series.start_at);
  const end = Date.parse(series.end_at);
  const x = (stamp: number) => ((stamp - start) / Math.max(1, end - start)) * right;
  const y = (price: number) => top + ((high - price) / (high - low)) * (bottom - top);

  ctx.strokeStyle = styles.getPropertyValue("--border").trim();
  ctx.fillStyle = styles.getPropertyValue("--muted-foreground").trim();
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (const [index, label] of ticks.entries()) {
    const ordinate = top + ((bottom - top) * index) / 4;
    ctx.beginPath();
    ctx.moveTo(0, ordinate);
    ctx.lineTo(right, ordinate);
    ctx.stroke();
    ctx.fillText(label, width - 1, ordinate);
  }

  const divisions = right < 300 ? 2 : 4;
  const timeLabels = range === "1D" ? clock : dateLabel;
  for (let i = 0; i <= divisions; i++) {
    ctx.textAlign = i === 0 ? "left" : i === divisions ? "right" : "center";
    ctx.fillText(
      timeLabels.format(start + ((end - start) * i) / divisions),
      (right * i) / divisions,
      bottom + 16,
    );
  }

  const color = styles.getPropertyValue("--data-fill").trim();
  const points = series.points.map((point, index) => ({
    x: x(Date.parse(point.ends_at)),
    y: y(prices[index]),
    gap: point.gap_before,
  }));
  const segments: (typeof points)[] = [];
  for (const point of points) {
    if (!segments.length || point.gap) segments.push([]);
    segments[segments.length - 1].push(point);
  }
  const fill = ctx.createLinearGradient(0, top, 0, bottom);
  fill.addColorStop(0, `color-mix(in srgb, ${color} 18%, transparent)`);
  fill.addColorStop(1, "transparent");
  ctx.lineWidth = 2;
  ctx.lineJoin = "round";
  ctx.strokeStyle = color;
  for (const segment of segments) {
    const first = segment[0];
    const last = segment[segment.length - 1];
    ctx.beginPath();
    ctx.moveTo(first.x, first.y);
    for (const point of segment.slice(1)) ctx.lineTo(point.x, point.y);
    if (segment.length > 1) {
      ctx.stroke();
      ctx.lineTo(last.x, bottom);
      ctx.lineTo(first.x, bottom);
      ctx.closePath();
      ctx.fillStyle = fill;
      ctx.fill();
    }
    if (segment.length === 1 || last === points.at(-1)) {
      ctx.beginPath();
      ctx.arc(last.x, last.y, 3.5, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    }
  }
}

function HistoryPlot({ series, range }: { series: HistorySeries; range: HistoryRange }) {
  const plot = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = plot.current;
    if (!canvas) return;
    const draw = () => drawChart(canvas, series, range);
    draw();
    const resize = new ResizeObserver(draw);
    resize.observe(canvas);
    return () => resize.disconnect();
  }, [series, range]);
  return <canvas className="market-history-plot" ref={plot} aria-hidden="true" />;
}

export function MarketHistoryChange({ value }: { value: string }) {
  const tone = outcome(value);
  return (
    <span
      className={
        tone === "gain"
          ? "text-gain-text"
          : tone === "loss"
            ? "text-loss-text"
            : "text-muted-foreground"
      }
    >
      {signedPercent(value)}
    </span>
  );
}

export function MarketHistoryChart({
  symbol,
  range,
  onRange,
  response,
  loading,
  retry,
}: {
  symbol: string;
  range: HistoryRange;
  onRange: (range: HistoryRange) => void;
  response?: HistoryResponse;
  loading: boolean;
  retry?: () => void;
}) {
  const selectedRange = useRef<HTMLButtonElement>(null);
  const series = response?.series;
  const usable = series && series.points.length > 0;
  const referencePrices = series?.source === "coin_metrics" && series.interval_minutes !== 1440;
  const singleSession = range === "1D" && series?.time_basis === "regular_session";
  const period = singleSession ? "Regular session" : periods[range];
  const stateMessage = loading
    ? "Loading price history…"
    : response?.state === "empty"
      ? "No history for this range"
      : response?.state === "pending"
        ? "History is still loading"
        : "Couldn’t load price history";
  const source =
    series?.source === "kraken" ? (
      "Kraken · UTC intervals"
    ) : series?.source === "coin_metrics" ? (
      <>
        <a
          className="underline underline-offset-2"
          href="https://github.com/coinmetrics/product-docs/blob/master/docs/packages/coin-metrics-community-data.md"
          target="_blank"
          rel="noreferrer"
        >
          Coin Metrics
        </a>
        {series.interval_minutes === 1440
          ? " · Daily USD closes · UTC"
          : " · USD reference prices · UTC"}
        {" · "}
        <a
          className="underline underline-offset-2"
          href="https://creativecommons.org/licenses/by-nc/4.0/"
          target="_blank"
          rel="noreferrer"
        >
          CC BY-NC 4.0
        </a>
      </>
    ) : (
      "IEX · Regular sessions · Split-adjusted"
    );

  return (
    <section className="market-history" aria-label="Price history">
      <div className="market-history-toolbar">
        <p className="text-sm text-muted-foreground">
          {period}{" "}
          {series?.period_change_pct != null && (
            <strong>
              <MarketHistoryChange value={series.period_change_pct} />
            </strong>
          )}
        </p>
        <div className="market-history-ranges" role="group" aria-label="Price history range">
          {historyRanges.map((option) => (
            <button
              key={option}
              type="button"
              ref={option === range ? selectedRange : undefined}
              aria-pressed={option === range}
              onClick={() => onRange(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      {usable ? (
        <figure className="market-history-figure">
          <HistoryPlot series={series} range={range} />
          <figcaption className="market-history-caption">
            <span>
              {source}
              {series.timeliness === "on_time" && series.as_of && (
                <>
                  {" · As of "}
                  <time dateTime={series.as_of}>
                    {historyAsOf.format(Date.parse(series.as_of))}
                  </time>
                </>
              )}
            </span>
            <details key={range}>
              <summary>Price data</summary>
              <table>
                <caption className="sr-only">
                  {symbol} {referencePrices ? "reference prices" : "closing prices"} · {period}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Interval end (local)</th>
                    <th scope="col">{referencePrices ? "Reference price (USD)" : "Close (USD)"}</th>
                  </tr>
                </thead>
                <tbody>
                  {series.points.map((point) => (
                    <tr key={point.ends_at}>
                      <td>
                        <time dateTime={point.ends_at}>{fullLocalTimestamp(point.ends_at)}</time>
                        {point.gap_before && (
                          <span className="block text-muted-foreground">
                            {point.gap_before === "closed"
                              ? "After market close"
                              : "After missing intervals"}
                          </span>
                        )}
                      </td>
                      <td>{exactPrice.format(point.close as `${number}`)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </figcaption>
          {(series.coverage === "partial" || series.timeliness !== "on_time") && (
            <div role="status" className="market-history-status">
              {series.coverage === "partial" && <p>Some price intervals are missing</p>}
              {series.timeliness !== "on_time" && series.as_of && (
                <p>
                  {series.timeliness === "delayed" && "History behind · "}
                  As of <time dateTime={series.as_of}>{fullLocalTimestamp(series.as_of)}</time>
                </p>
              )}
            </div>
          )}
        </figure>
      ) : (
        <div className="market-history-empty">
          <p role="status">{stateMessage}</p>
          {series && <p className="text-xs">{source}</p>}
          {!loading && retry && (
            <button
              type="button"
              onClick={() => {
                selectedRange.current?.focus();
                retry();
              }}
            >
              Try history again
            </button>
          )}
        </div>
      )}
    </section>
  );
}
