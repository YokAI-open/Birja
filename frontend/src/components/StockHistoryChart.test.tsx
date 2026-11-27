import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { StockHistoryChart } from "./StockHistoryChart";

it("preserves exchange and share class in the isolated frame and external link", async () => {
  const onRange = vi.fn();
  const props = { exchange: "NYSE", ticker: "BRK.B", onRange };
  const app = render(<StockHistoryChart {...props} range="1W" />);
  const frame = screen.getByTitle("BRK.B price history · Past 5 trading days");
  const url = new URL(frame.getAttribute("src")!);
  expect(url.origin).toBe("https://www.tradingview-widget.com");
  expect(frame).toHaveAttribute("sandbox", "allow-scripts allow-same-origin");
  expect(frame).toHaveAttribute("referrerpolicy", "no-referrer");
  expect(JSON.parse(decodeURIComponent(url.hash.slice(1)))).toMatchObject({
    symbols: [["NYSE:BRK.B|5D"]],
    dateRanges: ["5d|5"],
  });
  expect(screen.getByRole("link", { name: "Open chart on TradingView" })).toHaveAttribute(
    "href",
    "https://www.tradingview.com/chart/?symbol=NYSE%3ABRK.B",
  );
  await userEvent.click(screen.getByRole("button", { name: "1M" }));
  expect(onRange).toHaveBeenCalledExactlyOnceWith("1M");
  app.rerender(<StockHistoryChart {...props} range="1M" />);
  const month = screen.getByTitle("BRK.B price history · Past month");
  expect(month).not.toBe(frame);
  expect(screen.getByRole("button", { name: "1M" })).toHaveAttribute("aria-pressed", "true");
});

it("does not guess an exchange or accept a malformed ticker", () => {
  const onRange = vi.fn();
  const app = render(
    <StockHistoryChart exchange="OTC" ticker="AAPL" range="1W" onRange={onRange} />,
  );
  expect(screen.queryByRole("region", { name: "Price history" })).toBeNull();
  app.rerender(
    <StockHistoryChart exchange="NASDAQ" ticker="AAPL/DEMO" range="1W" onRange={onRange} />,
  );
  expect(screen.queryByRole("region", { name: "Price history" })).toBeNull();
});
