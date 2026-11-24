import { it, expect, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithClient } from "@/test/render";
import { fillFixture } from "@/test/stockTradeFixtures";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { StockTradeReceipt } from "./StockTradeReceipt";
it("displays original recorded balances, identity, source times and disclosure", async () => {
  const again = vi.fn(),
    fill = { ...fillFixture(), portfolio_id: "1" };
  const target: PortfolioTarget = Object.freeze({
    owner: "alice@example.test",
    portfolioId: "1",
    name: "Original strategy",
    epoch: Object.freeze({ owner: "alice@example.test", portfolioId: "1", session: 0 }),
    isCurrent: () => true,
  });
  const { user } = renderWithClient(
    <StockTradeReceipt fill={fill} target={target} onTradeAgain={again} />,
  );
  const receipt = screen.getByRole("region", { name: "Order filled" });
  expect(screen.getByRole("heading", { name: "Order filled" })).toHaveFocus();
  expect(receipt).toHaveTextContent("Apple Inc.");
  expect(receipt).not.toHaveTextContent("Original strategy");
  expect(within(receipt).getByRole("link", { name: "Portfolio" })).toHaveAttribute(
    "href",
    "/portfolios/1",
  );
  expect(receipt).toHaveTextContent("Cash after this trade$9,796.00");
  expect(receipt).toHaveTextContent("Shares after this trade2");
  expect(receipt).toHaveTextContent("9007199254740993");
  expect(receipt.querySelector('time[datetime="2026-11-10T15:00:09Z"]')).not.toBeNull();
  expect(
    within(receipt).getByRole("note", { name: "Stock preview price source" }),
  ).toHaveTextContent("IEX prices");
  expect(receipt).toHaveTextContent("Regulatory fees are omitted");
  await user.click(screen.getByRole("button", { name: "Trade again" }));
  expect(again).toHaveBeenCalledOnce();
});

it("does not reveal a wrong-root or unavailable receipt", () => {
  const target: PortfolioTarget = {
    owner: "alice@example.test",
    portfolioId: "2",
    name: "Sibling",
    epoch: { owner: "alice@example.test", portfolioId: "2", session: 0 },
    isCurrent: () => true,
  };
  const { rerender } = renderWithClient(
    <StockTradeReceipt
      fill={{ ...fillFixture(), portfolio_id: "1" }}
      target={target}
      onTradeAgain={() => {}}
    />,
  );
  expect(screen.queryByRole("region", { name: "Order filled" })).toBeNull();
  rerender(
    <StockTradeReceipt
      fill={{ ...fillFixture(), portfolio_id: "2" }}
      target={{ ...target, isCurrent: () => false }}
      onTradeAgain={() => {}}
    />,
  );
  expect(screen.queryByText(/Apple Inc/)).toBeNull();
});
