import { apiFetch } from "./client";

export type PortfolioSummary = Readonly<{ id: string; name: string }>;

// Unicode White_Space matches the server, excluding JS trim's extra BOM.
const boundarySpace = new Set([
  9, 10, 11, 12, 13, 32, 133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8200, 8201,
  8202, 8232, 8233, 8239, 8287, 12288,
]);

/** Display assistance only. SQL alone determines casefold uniqueness/replay. */
export function portfolioNameDisplay(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const points = [...value];
  if (
    points.some((c) => {
      const point = c.codePointAt(0)!;
      return point < 32 || (point >= 127 && point <= 159) || (point >= 0xd800 && point <= 0xdfff);
    })
  )
    return null;
  let start = 0,
    end = points.length;
  while (start < end && boundarySpace.has(points[start].codePointAt(0)!)) start++;
  while (end > start && boundarySpace.has(points[end - 1].codePointAt(0)!)) end--;
  const display = points.slice(start, end).join("").normalize("NFC");
  const count = [...display].length;
  return count >= 1 && count <= 60 ? display : null;
}

export function isCanonicalPortfolioName(value: unknown): value is string {
  return typeof value === "string" && portfolioNameDisplay(value) === value;
}

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
        !isCanonicalPortfolioName(item.name)
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
