import { useEffect, useRef } from "react";
import {
  PORTFOLIO_VALUE_DAYS,
  UTC_DAY_MS,
  type PortfolioValuePoint,
} from "@/api/portfolioValueHistory";
import { signedUsd } from "@/lib/financialDisplay";
import { formatUsd } from "@/lib/money";

type Observation = PortfolioValuePoint & { total_value: string };
type Series = {
  start_day: string;
  end_day: string;
  points: readonly PortfolioValuePoint[];
};
const dates = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeZone: "UTC" });

function toCents(amount: string) {
  return BigInt(amount.replace(".", ""));
}

function signedChange(first: string, last: string) {
  const difference = toCents(last) - toCents(first);
  const magnitude = difference < 0n ? -difference : difference;
  const decimal = `${magnitude / 100n}.${String(magnitude % 100n).padStart(2, "0")}`;
  return signedUsd(difference < 0n ? `-${decimal}` : decimal);
}

function describe(point: Observation) {
  return `${dates.format(Date.parse(point.utc_day))}, ${formatUsd(point.total_value)}`;
}

function draw(canvas: HTMLCanvasElement, startDay: string, values: readonly Observation[]) {
  const { width, height } = canvas.getBoundingClientRect();
  if (width < 8 || height < 8) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const density = Math.min(window.devicePixelRatio || 1, 3);
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  ctx.scale(density, density);
  const amounts = values.map(({ total_value }) => toCents(total_value));
  const min = amounts.reduce((a, b) => (a < b ? a : b));
  const max = amounts.reduce((a, b) => (a > b ? a : b));
  const start = Date.parse(startDay);
  const padding = 4;
  const segments: { day: number; x: number; y: number }[][] = [];
  for (const [index, value] of values.entries()) {
    const day = (Date.parse(value.utc_day) - start) / UTC_DAY_MS;
    const x = padding + (day / (PORTFOLIO_VALUE_DAYS - 1)) * (width - 2 * padding);
    // Convert only the bounded normalized ordinate to a display number.
    const fraction =
      min === max ? 0.5 : Number(((max - amounts[index]) * 1_000_000n) / (max - min)) / 1_000_000;
    const y = padding + fraction * (height - 2 * padding);
    if (segments.at(-1)?.at(-1)?.day !== day - 1) segments.push([]);
    segments[segments.length - 1].push({ day, x, y });
  }
  const color = getComputedStyle(canvas).getPropertyValue("--data-fill").trim();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const [first, ...remaining] of segments) {
    ctx.beginPath();
    if (remaining.length === 0) {
      ctx.arc(first.x, first.y, 2, 0, 2 * Math.PI);
      ctx.fill();
    } else {
      ctx.moveTo(first.x, first.y);
      for (const { x, y } of remaining) ctx.lineTo(x, y);
      ctx.stroke();
    }
  }
}

export function PortfolioValueSparkline({
  id,
  series,
  loading,
  failed,
}: {
  id: string;
  series?: Series;
  loading: boolean;
  failed: boolean;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const startDay = series?.start_day;
  const points = series?.points;
  const values = points?.filter((point): point is Observation => point.total_value !== null) ?? [];
  const hasChart = !loading && !failed && values.length >= 2;
  useEffect(() => {
    const element = canvas.current;
    if (!element || !startDay || !points) return;
    const observations = points.filter((point): point is Observation => point.total_value !== null);
    if (observations.length < 2) return;
    const redraw = () => draw(element, startDay, observations);
    redraw();
    const observer = new ResizeObserver(redraw);
    observer.observe(element);
    return () => observer.disconnect();
  }, [hasChart, points, startDay]);

  if (loading || failed || !hasChart) {
    return (
      <div id={id} className="portfolio-value-trend portfolio-value-trend-status">
        {loading ? (
          "Loading value history…"
        ) : failed ? (
          <span className="sr-only">Value history unavailable</span>
        ) : (
          "Collecting daily values"
        )}
        {!loading && !failed && values[0] && (
          <span className="sr-only">. One recorded value (UTC) on {describe(values[0])}.</span>
        )}
      </div>
    );
  }

  const first = values[0];
  const last = values[values.length - 1];
  return (
    <div className="portfolio-value-trend">
      <canvas ref={canvas} className="block size-full" aria-hidden="true" />
      <span id={id} className="sr-only">
        30-day value history (UTC). First recorded value on {describe(first)}. Last recorded value
        on {describe(last)}. Change {signedChange(first.total_value, last.total_value)}.
        {values.length < PORTFOLIO_VALUE_DAYS && " Some days have no recorded value."}
      </span>
    </div>
  );
}
