const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** Formats a server decimal string as USD without ever converting it to a JS float. */
export function formatUsd(value: string): string {
  if (!/^-?\d+(\.\d+)?$/.test(value)) {
    throw new Error(`Not a decimal string: ${value}`);
  }
  return USD.format(value as `${number}`);
}
