import { describe, expect, it } from "vitest";
import { formatUnitPrice, formatUsd } from "./money";

describe("formatUsd", () => {
  it("formats a server decimal string", () => {
    expect(formatUsd("10000.00000000")).toBe("$10,000.00");
    expect(formatUsd("0")).toBe("$0.00");
  });

  it("keeps precision beyond float range", () => {
    expect(formatUsd("123456789012345678.99")).toBe("$123,456,789,012,345,678.99");
  });

  it("rejects non-numeric strings", () => {
    expect(() => formatUsd("abc")).toThrow();
    expect(() => formatUsd("")).toThrow();
  });
});

describe("formatUnitPrice", () => {
  it.each([
    ["81042.35000000", "$81,042.35"],
    ["1.00800000", "$1.01"],
    ["1.00000000", "$1.00"],
    ["0.20663000", "$0.2066"],
    ["0.07998070", "$0.07998"],
    ["0.33080000", "$0.3308"],
    ["0.00001234", "$0.00001234"],
  ])("formats %s as %s", (input, expected) => {
    expect(formatUnitPrice(input)).toBe(expected);
  });

  it("rejects invalid and negative values", () => {
    expect(() => formatUnitPrice("abc")).toThrow();
    expect(() => formatUnitPrice("-1.5")).toThrow();
  });
});
