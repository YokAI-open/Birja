const USD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** Formats a server decimal string as USD without ever converting it to a JS float. */
export function formatUsd(value: string): string {
  if (!/^-?\d+(\.\d+)?$/.test(value)) {
    throw new Error(`Not a decimal string: ${value}`);
  }
  return USD.format(value as `${number}`);
}

const UNIT_SMALL = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumSignificantDigits: 4,
  maximumSignificantDigits: 4,
});

/** Unit price: 2 decimals at $1 or more, 4 significant digits below $1 (D-06). */
export function formatUnitPrice(value: string): string {
  if (!/^\d+(\.\d+)?$/.test(value)) {
    throw new Error(`Not a non-negative decimal string: ${value}`);
  }
  const integerPart = value.split(".")[0] ?? "";
  if (/^0+$/.test(integerPart)) {
    return UNIT_SMALL.format(value as `${number}`);
  }
  return formatUsd(value);
}
