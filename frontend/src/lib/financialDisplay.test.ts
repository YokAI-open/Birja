import { describe, expect, it } from "vitest";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "./financialDisplay";

describe("exact signed financial display", () => {
  it.each([
    ["12.34", "+$12.34", "+12.34%", "gain"],
    ["-12.34", "−$12.34", "−12.34%", "loss"],
    ["0.00", "$0.00", "0.00%", "zero"],
    ["-0.00", "$0.00", "0.00%", "zero"],
  ])("formats %s independently", (value, dollars, percent, result) => {
    expect(signedUsd(value)).toBe(dollars);
    expect(signedPercent(value)).toBe(percent);
    expect(outcome(value)).toBe(result);
  });

  it("preserves values beyond safe integer precision", () => {
    expect(signedUsd("9007199254740993.01")).toBe("+$9,007,199,254,740,993.01");
    expect(signedPercent("9007199254740993.01")).toBe("+9007199254740993.01%");
  });

  it.each(["1e2", "NaN", "Infinity", "", "+1.00", "1%;color:red"])(
    "rejects invalid decimal %s",
    (value) => {
      expect(() => signedUsd(value)).toThrow();
      expect(() => signedPercent(value)).toThrow();
      expect(() => outcome(value)).toThrow();
    },
  );

  it("formats a full local timestamp including seconds and timezone", () => {
    const utc = "2026-10-29T10:02:03Z";
    expect(fullLocalTimestamp(utc)).toBe(
      new Date(utc).toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "short",
      }),
    );
  });
});
