import { describe, expect, it } from "vitest";
import { formatUsd } from "./money";

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
