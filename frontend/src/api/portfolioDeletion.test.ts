import { afterEach, expect, it, vi } from "vitest";
import { deletePortfolio, PortfolioDeletionError } from "./portfolioDeletion";

const intent = {
  portfolioId: "9007199254740993",
  intentKey: "12345678-1234-4234-8234-123456789abc",
  confirmationName: "Café",
  policyVersion: "freeze_at_closure_v1" as const,
};
const receipt = { portfolio_id: intent.portfolioId, state: "closed" };
const json = (body: unknown, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

it("sends only the exact original and returns a frozen minimal receipt", async () => {
  document.cookie = "bj_csrf=test; path=/";
  const fetcher = vi.fn(async () => json(receipt));
  vi.stubGlobal("fetch", fetcher);
  expect(await deletePortfolio(intent)).toEqual({ portfolioId: intent.portfolioId, state: "closed" });
  const [path, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
  expect(path).toBe(`/api/v2/portfolios/${intent.portfolioId}`);
  expect(init).toMatchObject({ method: "DELETE", cache: "no-store", credentials: "same-origin" });
  expect(JSON.parse(init.body as string)).toEqual({
    intent_key: intent.intentKey,
    confirmation_name: intent.confirmationName,
    policy_version: intent.policyVersion,
  });
  expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("test");
  expect(Object.isFrozen(await deletePortfolio(intent))).toBe(true);
});

it.each([
  { ...intent, portfolioId: "01" },
  { ...intent, portfolioId: "9223372036854775808" },
  { ...intent, intentKey: intent.intentKey.toUpperCase() },
  { ...intent, confirmationName: " Café" },
  { ...intent, confirmationName: "Cafe\u0301" },
  { ...intent, policyVersion: "other" },
  { ...intent, cash: "1" },
])("rejects noncanonical original before any fetch", async (bad) => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  await expect(deletePortfolio(bad as never)).rejects.toMatchObject({ outcome: "refused", code: "invalid_input" });
  expect(fetcher).not.toHaveBeenCalled();
});

it.each([
  () => json({ ...receipt, portfolio_id: "2" }),
  () => json({ ...receipt, cash: "10000" }),
  () => json({ ...receipt, state: "active" }),
  () => new Response(JSON.stringify(receipt), { headers: { "Content-Type": "text/html" } }),
  () => new Response("oops", { headers: { "Content-Type": "application/json" } }),
  () => new Response(null, { status: 204 }),
])("keeps poisoned or malformed acknowledgements unknown", async (reply) => {
  document.cookie = "bj_csrf=test; path=/";
  const fetcher = vi.fn(async () => reply());
  vi.stubGlobal("fetch", fetcher);
  await expect(deletePortfolio(intent)).rejects.toMatchObject({ outcome: "unknown" });
  expect(fetcher).toHaveBeenCalledTimes(1);
});

it("trusts only exact durable name-refusal shape, redacting arbitrary detail", async () => {
  document.cookie = "bj_csrf=test; path=/";
  vi.stubGlobal("fetch", vi.fn(async () => json({ detail: { code: "portfolio_confirmation_changed" } }, 409)));
  await expect(deletePortfolio(intent)).rejects.toMatchObject({ outcome: "refused", terminal: true, code: "portfolio_confirmation_changed" });
  vi.stubGlobal("fetch", vi.fn(async () => json({ detail: { code: "portfolio_confirmation_changed", cash: "secret" } }, 409)));
  const error = await deletePortfolio(intent).catch((error: unknown) => error);
  expect(error).toBeInstanceOf(PortfolioDeletionError);
  expect(error).toMatchObject({ outcome: "unknown", terminal: false });
  expect(JSON.stringify(error)).not.toContain("secret");
});
