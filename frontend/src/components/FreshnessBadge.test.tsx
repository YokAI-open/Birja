import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FreshnessBadge } from "./FreshnessBadge";

describe("FreshnessBadge", () => {
  it.each([
    ["fresh", 42, "Live · 42s ago", "success"],
    ["aging", 150, "Delayed · 2m ago", "warning"],
    ["stale", 420, "Stale · 7m ago", "danger"],
  ] as const)("renders %s", (status, age, text, variant) => {
    const { container } = render(<FreshnessBadge status={status} ageSeconds={age} />);
    expect(screen.getByText(text)).toHaveAttribute("data-variant", variant);
    expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
    expect(container.querySelector("[aria-live]")).toBeNull();
  });
});
