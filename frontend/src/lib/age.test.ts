import { describe, expect, it } from "vitest";
import { formatAge, freshnessStatus, statusLabel } from "./age";

describe("formatAge", () => {
  it.each([
    [0, "0s ago"],
    [42, "42s ago"],
    [59, "59s ago"],
    [60, "1m ago"],
    [119, "1m ago"],
    [420, "7m ago"],
    [3599, "59m ago"],
    [3600, "1h ago"],
    [7300, "2h ago"],
    [-5, "0s ago"],
    [42.9, "42s ago"],
  ])("formats %s as %s", (input, expected) => {
    expect(formatAge(input)).toBe(expected);
  });
});

describe("freshnessStatus", () => {
  it.each([
    [119, "fresh"],
    [120, "aging"],
    [300, "aging"],
    [301, "stale"],
  ])("age %s is %s", (age, expected) => {
    expect(freshnessStatus(age, 120, 300)).toBe(expected);
  });
});

describe("statusLabel", () => {
  it("maps statuses to MASTER labels", () => {
    expect(statusLabel("fresh")).toBe("Live");
    expect(statusLabel("aging")).toBe("Delayed");
    expect(statusLabel("stale")).toBe("Stale");
  });
});
