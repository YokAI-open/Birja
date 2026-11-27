import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioValuePoint } from "@/api/portfolioValueHistory";
import { PortfolioValueSparkline } from "./PortfolioValueSparkline";

const first = "9007199254740993.01";
const day = (n: number) => `2026-10-${String(n).padStart(2, "0")}`;
const point = (n: number, total_value: string | null): PortfolioValuePoint => ({
  utc_day: day(n),
  captured_at: `${day(n)}T22:00:00Z`,
  total_value,
  valuation_complete: total_value !== null,
});
const series = (points: PortfolioValuePoint[]) => ({ start_day: day(1), end_day: day(30), points });
function draw(points: PortfolioValuePoint[], state?: "loading" | "failed") {
  return render(
    <a href="/portfolios/2" aria-describedby="test-trend">
      Strategy
      <PortfolioValueSparkline
        id="test-trend"
        series={series(points)}
        loading={state === "loading"}
        failed={state === "failed"}
      />
    </a>,
  );
}
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("keeps loading, error and collecting accessibly distinct without showing a fabricated line", () => {
  const unfinished = draw([], "loading");
  expect(screen.getByRole("link")).toHaveAccessibleDescription("Loading value history…");
  unfinished.unmount();
  const failed = draw([point(2, first)], "failed");
  expect(screen.getByRole("link")).toHaveAccessibleDescription("Value history unavailable");
  expect(failed.container.querySelector("canvas")).toBeNull();
  failed.unmount();
  const single = draw([point(2, first), point(3, null)]);
  expect(screen.getByRole("link")).toHaveAccessibleDescription(
    "Collecting daily values. One recorded value (UTC) on Oct 2, 2026, $9,007,199,254,740,993.01.",
  );
  expect(single.container.querySelector("canvas")).toBeNull();
});

it("plots only real adjacent days, preserves gaps, and describes the exact signed movement", () => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  );
  const ctx = {
    scale: vi.fn(),
    beginPath: vi.fn(),
    arc: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    fill: vi.fn(),
  };
  vi.spyOn(HTMLCanvasElement.prototype, "getBoundingClientRect").mockReturnValue(
    new DOMRect(0, 0, 298, 44),
  );
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
    ctx as unknown as CanvasRenderingContext2D,
  );
  const chart = draw([
    point(2, first),
    point(3, "9007199254740993.10"),
    point(4, null),
    point(5, "9007199254740993.08"),
    point(9, "9007199254740993.00"),
    point(10, "9007199254740993.06"),
  ]);
  expect(screen.getByRole("link")).toHaveAccessibleDescription(
    "30-day value history (UTC). First recorded value on Oct 2, 2026, $9,007,199,254,740,993.01. Last recorded value on Oct 10, 2026, $9,007,199,254,740,993.06. Change +$0.05. Some days have no recorded value.",
  );
  expect(chart.container.querySelector("canvas")).toHaveAttribute("aria-hidden", "true");
  expect(ctx.stroke).toHaveBeenCalledTimes(2);
  expect(ctx.moveTo.mock.calls.map(([x]) => x)).toEqual([14, 84]);
  expect(ctx.lineTo.mock.calls.map(([x]) => x)).toEqual([24, 94]);
  expect(ctx.arc).toHaveBeenCalledOnce();
  expect(ctx.arc.mock.calls[0][0]).toBe(44);
});
