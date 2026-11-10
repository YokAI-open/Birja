import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { StockAttribution } from "./StockAttribution";

afterEach(cleanup);

it.each(["listing", "preview", "valuation"] as const)(
  "visibly discloses IEX and simulation in %s",
  (context) => {
    render(<StockAttribution context={context} />);
    expect(screen.getByText("IEX prices")).toBeVisible();
    expect(
      screen.getByText(
        "Quotes come from IEX, one US exchange, and may differ from other exchanges. Birja uses virtual money and simulated execution.",
      ),
    ).toBeVisible();
  },
);

it("adds verified supplemental attribution as escaped visible text", () => {
  const supplemental = '<img src=x onerror="alert(1)"> required provider disclosure';
  const { container } = render(<StockAttribution context="listing" required_text={supplemental} />);
  expect(screen.getByText(supplemental)).toBeVisible();
  expect(screen.getByText("IEX prices")).toBeVisible();
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelector("script")).toBeNull();
});
