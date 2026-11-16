import { apiFetch } from "./client";

export type PortfolioSummary = Readonly<{ id: string; name: string }>;

/** IDs remain canonical bigint strings throughout browser state and transport. */
export function isPortfolioId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[1-9]\d{0,18}$/.test(value) &&
    BigInt(value) <= 9223372036854775807n
  );
}

export function parsePortfolios(body: unknown): readonly PortfolioSummary[] {
  if (!Array.isArray(body) || body.length > 10) throw new Error("Unexpected portfolio metadata");
  let previous = 0n;
  return Object.freeze(
    body.map((entry: unknown) => {
      if (typeof entry !== "object" || entry === null || Array.isArray(entry))
        throw new Error("Unexpected portfolio metadata");
      const item = entry as Record<string, unknown>;
      if (
        Object.keys(item).length !== 2 ||
        !isPortfolioId(item.id) ||
        BigInt(item.id) <= previous ||
        typeof item.name !== "string" ||
        item.name.trim() !== item.name ||
        item.name.length === 0 ||
        [...item.name].length > 60 ||
        [...item.name].some((character) => {
          const point = character.codePointAt(0)!;
          return point < 32 || (point >= 127 && point <= 159);
        })
      )
        throw new Error("Unexpected portfolio metadata");
      previous = BigInt(item.id);
      return Object.freeze({ id: item.id, name: item.name });
    }),
  );
}

/** Discovery is metadata only; every financial request still needs a verified target. */
export async function fetchPortfolios(signal?: AbortSignal): Promise<readonly PortfolioSummary[]> {
  return parsePortfolios(await apiFetch("/api/v2/portfolios", { signal, cache: "no-store" }));
}
