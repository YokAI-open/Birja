import { it, expect, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithClient } from "@/test/render";
import { fillFixture } from "@/test/stockTradeFixtures";
import { StockTradeReceipt } from "./StockTradeReceipt";
it("displays original recorded balances, identity, source times and disclosure", async () => {
  const again = vi.fn(), fill = fillFixture();
  const { user } = renderWithClient(<StockTradeReceipt fill={fill} onTradeAgain={again} />);
  const receipt = screen.getByRole("region", { name: "Order filled" });
  expect(screen.getByRole("heading", { name: "Order filled" })).toHaveFocus();
  expect(receipt).toHaveTextContent("Apple Inc."); expect(receipt).toHaveTextContent("Cash after this trade$9,796.00");
  expect(receipt).toHaveTextContent("Shares after this trade2"); expect(receipt).toHaveTextContent("9007199254740993");
  expect(receipt.querySelector('time[datetime="2026-11-10T15:00:09Z"]')).not.toBeNull();
  expect(within(receipt).getByRole("note", { name: "Stock preview price source" })).toHaveTextContent("IEX prices");
  expect(receipt).toHaveTextContent("Regulatory fees are omitted");
  await user.click(screen.getByRole("button", { name: "Trade again" })); expect(again).toHaveBeenCalledOnce();
});
