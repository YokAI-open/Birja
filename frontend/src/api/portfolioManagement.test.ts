import { afterEach, expect, it, vi } from "vitest";
import {
  createPortfolio,
  fetchPortfolioMetadata,
  updatePortfolioMetadata,
  parsePortfolioMetadata,
  portfolioNameDisplay,
  normalizePortfolioDescription,
  PortfolioManagementError,
} from "./portfolioManagement";
import { parsePortfolios } from "./portfolios";

const key = "12345678-1234-4234-8234-123456789abc";
const id = "9007199254740993";
const metadata = { id, name: "Café", description: "<b>plain</b>\n\ttext" };
const reply = (body: unknown, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), { status, headers });
afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0";
});

it("validates Unicode scalars, explicit whitespace and raw controls before display normalization", () => {
  expect(portfolioNameDisplay("\u0085bad")).toBeNull();
  expect(portfolioNameDisplay("\nname")).toBeNull();
  expect(portfolioNameDisplay("\u00a0Cafe\u0301\u3000")).toBe("Café");
  expect(portfolioNameDisplay("\ufeffName\ufeff")).toBe("\ufeffName\ufeff");
  expect(portfolioNameDisplay("😀".repeat(60))).toBe("😀".repeat(60));
  for (const value of [null, "", " ", "a".repeat(61), "😀".repeat(61), "\ud800", "a\u007fb"])
    expect(portfolioNameDisplay(value)).toBeNull();
  expect(portfolioNameDisplay("Straße")).toBe("Straße");
  expect(portfolioNameDisplay("STRASSE")).toBe("STRASSE");
  expect(normalizePortfolioDescription("a\r\nb\rc\t")).toBe("a\nb\nc\t");
  expect(normalizePortfolioDescription("😀".repeat(1000))).toBe("😀".repeat(1000));
  for (const value of [null, "😀".repeat(1001), "\udfff", "\u0085", "\u000b"])
    expect(normalizePortfolioDescription(value)).toBeNull();
});
it.each([
  null,
  [],
  { ...metadata, id: 1 },
  { ...metadata, id: "01" },
  { ...metadata, id: "9223372036854775808" },
  { ...metadata, cash: "10000" },
  { ...metadata, name: "Cafe\u0301" },
  { ...metadata, name: " Café" },
  { ...metadata, name: "x\n" },
  { ...metadata, description: null },
  { ...metadata, description: "\r\n" },
  { ...metadata, description: "x".repeat(1001) },
])("rejects malformed authoritative metadata %j", (body) => {
  expect(() => parsePortfolioMetadata(body)).toThrow();
});
it("keeps discovery exactly two keys and returns immutable authoritative metadata", () => {
  expect(() => parsePortfolios([metadata])).toThrow();
  expect(Object.isFrozen(parsePortfolioMetadata(metadata))).toBe(true);
  expect(parsePortfolioMetadata(metadata)).toEqual(metadata);
});
it("uses scoped metadata/PATCH URLs and credentials, CSRF, no-store, signal and omission semantics", async () => {
  document.cookie = "bj_csrf=test-csrf";
  const fetcher = vi.fn(async () => reply(metadata));
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  expect(await fetchPortfolioMetadata(id, signal)).toEqual(metadata);
  expect(await updatePortfolioMetadata(id, { description: "" }, signal)).toEqual(metadata);
  const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
  expect(calls.map(([url]) => url)).toEqual([
    `/api/v2/portfolios/${id}/metadata`,
    `/api/v2/portfolios/${id}`,
  ]);
  expect(calls[1][1].body).toBe('{"description":""}');
  expect(calls[1][1].method).toBe("PATCH");
  expect(new Headers(calls[1][1].headers).get("X-CSRF-Token")).toBe("test-csrf");
  expect(
    calls.every(
      ([, init]) =>
        init.signal === signal && init.cache === "no-store" && init.credentials === "same-origin",
    ),
  ).toBe(true);
});
it("freezes the original raw key/payload across session recovery without a replacement intent", async () => {
  document.cookie = "bj_csrf=test-csrf";
  const input = { key, name: " Cafe\u0301 ", description: "a\r\nb" };
  const fetcher = vi
    .fn()
    .mockImplementationOnce(async () => {
      input.name = "Changed";
      input.key = "ffffffff-ffff-4fff-afff-ffffffffffff";
      return reply({}, 401);
    })
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
    .mockResolvedValueOnce(reply(metadata, 201));
  vi.stubGlobal("fetch", fetcher);
  expect(await createPortfolio(input)).toEqual(metadata);
  const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
  expect(calls.map(([url]) => url)).toEqual([
    "/api/v2/portfolios",
    "/api/v1/auth/refresh",
    "/api/v2/portfolios",
  ]);
  for (const index of [0, 2]) {
    expect(new Headers(calls[index][1].headers).get("Idempotency-Key")).toBe(key);
    expect(calls[index][1].body).toBe(
      JSON.stringify({ name: " Cafe\u0301 ", description: "a\r\nb" }),
    );
    expect(calls[index][1].method).toBe("POST");
  }
});
it.each(["", key.toUpperCase(), key.replace("-4234-", "-1234-"), "x"])(
  "rejects invalid UUIDv4 %s before transport",
  async (bad) => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    await expect(createPortfolio({ key: bad, name: "ok" })).rejects.toMatchObject({
      outcome: "refused",
    });
    expect(fetcher).not.toHaveBeenCalled();
  },
);
it("rejects invalid targets, empty/null/extra patches and invalid creation fields before transport", async () => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  for (const bad of ["0", "01", "1/../2", "9223372036854775808"])
    await expect(fetchPortfolioMetadata(bad)).rejects.toThrow();
  for (const patch of [
    {},
    { name: null },
    { description: null },
    { cash: "1" },
    { name: "\nname" },
  ])
    await expect(updatePortfolioMetadata(id, patch as never)).rejects.toThrow();
  for (const input of [
    { key, name: null },
    { key, name: "ok", description: null },
    { key, name: "ok", cash: "1" },
  ])
    await expect(createPortfolio(input as never)).rejects.toThrow();
  expect(fetcher).not.toHaveBeenCalled();
});
it("rejects another root's metadata for both read and edit", async () => {
  document.cookie = "bj_csrf=test";
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => reply({ ...metadata, id: "2" })),
  );
  await expect(fetchPortfolioMetadata(id)).rejects.toThrow();
  await expect(updatePortfolioMetadata(id, { name: "new" })).rejects.toMatchObject({
    outcome: "unknown",
  });
});
it.each([
  [409, "name_taken"],
  [409, "creation_key_conflict"],
  [409, "portfolio_limit"],
  [404, "portfolio_unavailable"],
  [429, "creation_quota"],
  [429, "rate_limited"],
  [422, "invalid_input"],
])("preserves definitive %s/%s and Retry-After without server detail", async (status, code) => {
  document.cookie = "bj_csrf=test";
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply(
        { detail: { code, message: "secret", cash: "10000", owner: "private" } },
        status as number,
        { "Retry-After": "12" },
      ),
    ),
  );
  await expect(createPortfolio({ key, name: "ok" })).rejects.toMatchObject({
    outcome: "refused",
    status,
    code,
    retryAfter: 12,
  });
  try {
    await createPortfolio({ key, name: "ok" });
  } catch (error) {
    expect(error).toBeInstanceOf(PortfolioManagementError);
    expect(JSON.stringify(error)).not.toContain("private");
    expect((error as Error).message).not.toContain("secret");
  }
});
it.each([500, 503, 502, 409])(
  "keeps ambiguous %s results unknown without promising no grant",
  async (status) => {
    document.cookie = "bj_csrf=test";
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => reply({ detail: { code: "unrecognized", message: "secret" } }, status)),
    );
    await expect(createPortfolio({ key, name: "ok" })).rejects.toMatchObject({
      outcome: "unknown",
      status,
      code: null,
    });
  },
);
it("retains the known service code and wait while leaving the creation outcome unknown", async () => {
  document.cookie = "bj_csrf=test";
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply({ detail: { code: "service_unavailable", message: "private" } }, 503, {
        "Retry-After": "5",
      }),
    ),
  );
  await expect(createPortfolio({ key, name: "ok" })).rejects.toMatchObject({
    outcome: "unknown",
    status: 503,
    code: "service_unavailable",
    retryAfter: 5,
  });
});
it("keeps response loss/malformed success unknown and cancelled transports aborted", async () => {
  document.cookie = "bj_csrf=test";
  for (const response of [
    () => Promise.reject(new TypeError("network secret")),
    async () => reply({ ...metadata, cash: "1" }),
    async () => new Response("oops"),
  ]) {
    vi.stubGlobal("fetch", vi.fn(response));
    await expect(createPortfolio({ key, name: "ok" })).rejects.toMatchObject({
      outcome: "unknown",
    });
  }
  const controller = new AbortController();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      controller.abort();
      return reply(metadata);
    }),
  );
  await expect(createPortfolio({ key, name: "ok" }, controller.signal)).rejects.toMatchObject({
    name: "AbortError",
  });
});
