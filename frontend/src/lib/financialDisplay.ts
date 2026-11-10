import { formatUsd } from "./money";

/** Inspect the server's rounded decimal, without a numeric conversion. */
export function outcome(value: string): "gain" | "loss" | "zero" {
  if (!/^-?\d+(\.\d+)?$/.test(value)) throw new Error("Not a decimal string");
  if (/^-?0+(\.0+)?$/.test(value)) return "zero";
  return value.startsWith("-") ? "loss" : "gain";
}

export function signedUsd(value: string): string {
  const state = outcome(value);
  return (
    (state === "zero" ? "" : state === "loss" ? "−" : "+") + formatUsd(value.replace(/^-/, ""))
  );
}

/** Server percentages are already percentage points. */
export function signedPercent(value: string): string {
  const state = outcome(value);
  return (state === "zero" ? "" : state === "loss" ? "−" : "+") + value.replace(/^-/, "") + "%";
}

export function fullLocalTimestamp(utc: string): string {
  return new Date(utc).toLocaleString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  });
}
