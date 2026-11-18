import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "@/api/client";
import { fetchPortfolios, isPortfolioId, parsePortfolios } from "@/api/portfolios";
import { usePortfolioTarget } from "./usePortfolioTarget";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";

const alice = "alice@example.test";
const bob = "bob@example.test";
const first = { id: "1", name: "My portfolio" };
const second = { id: "2", name: "Second strategy" };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const clients: QueryClient[] = [];
it("renews metadata authority from an identity-only event without reviving old handles", async () => {
  let release!: (value: Response) => void;
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json([first]))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    )
    .mockResolvedValueOnce(json([first]));
  vi.stubGlobal("fetch", fetch);
  const h = setup("1");
  await waitFor(() => expect(h.result.current.status).toBe("ready"));
  const original = h.result.current.target!;
  act(() => broadcastMetadataChange("1"));
  expect(original.isCurrent()).toBe(false);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  await act(async () => release(json([{ ...first, name: "Renamed" }])));
  await waitFor(() => expect(h.result.current.target?.name).toBe("Renamed"));
  expect(original.isOriginalCurrent?.()).toBe(true);
  expect(original.isCurrent()).toBe(false);
  const renamed = h.result.current.target!;
  await act(async () => {
    await h.result.current.refetch();
  });
  await waitFor(() => expect(h.result.current.target?.name).toBe(first.name));
  expect(original.isCurrent()).toBe(false);
  expect(renamed.isCurrent()).toBe(false);
  act(() => h.client.setQueryData(["me"], null));
  expect(original.isOriginalCurrent?.()).toBe(false);
});
function setup(id: string | undefined, legacyEntry = false, email: string | null = alice) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], email === null ? null : { email });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return {
    client,
    ...renderHook(({ routeId, legacy }) => usePortfolioTarget(routeId, { legacyEntry: legacy }), {
      initialProps: { routeId: id, legacy: legacyEntry },
      wrapper,
    }),
  };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it.each(["1", "9223372036854775807"])("keeps canonical bigint ID %s as a string", (id) => {
  expect(isPortfolioId(id)).toBe(true);
});
it.each([undefined, null, 1, "", "0", "01", "-1", "1.0", " 1", "1/2", "9223372036854775808"])(
  "rejects malformed ID %j",
  (id) => expect(isPortfolioId(id)).toBe(false),
);
it("parses only the bounded ordered metadata contract without financial fields", () => {
  const parsed = parsePortfolios([first, second]);
  expect(parsed).toEqual([first, second]);
  expect(Object.isFrozen(parsed)).toBe(true);
  expect(Object.isFrozen(parsed[0])).toBe(true);
  expect(parsePortfolios([])).toEqual([]);
  expect(parsePortfolios([{ id: "1", name: "🙂".repeat(60) }])).toHaveLength(1);
});
it.each([
  null,
  {},
  { items: [first] },
  [null],
  [{ ...first, cash: "10000" }],
  [{ id: 1, name: "My portfolio" }],
  [{ id: "01", name: "My portfolio" }],
  [{ id: "9223372036854775808", name: "My portfolio" }],
  [second, first],
  [first, first],
  [{ id: "1", name: "" }],
  [{ id: "1", name: " Name" }],
  [{ id: "1", name: "Name\n" }],
  [{ id: "1", name: "a".repeat(61) }],
  Array.from({ length: 11 }, (_, index) => ({ id: String(index + 1), name: "Strategy" })),
])("rejects unexpected metadata %j", (body) => {
  expect(() => parsePortfolios(body)).toThrow("Unexpected portfolio metadata");
});

it("requests metadata only with no-store and a cancellable signal", async () => {
  const controller = new AbortController();
  const fetch = vi.fn(() => Promise.resolve(json([first])));
  vi.stubGlobal("fetch", fetch);
  expect(await fetchPortfolios(controller.signal)).toEqual([first]);
  expect(fetch).toHaveBeenCalledWith(
    "/api/v2/portfolios",
    expect.objectContaining({ cache: "no-store", signal: controller.signal, method: "GET" }),
  );
  controller.abort();
  await expect(fetchPortfolios(controller.signal)).rejects.toThrow();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("resolves only an explicit owned metadata target and captures a frozen epoch", async () => {
  const fetch = vi.fn(() => Promise.resolve(json([first, second])));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup("2");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  expect(result.current.target).toMatchObject({
    owner: alice,
    portfolioId: "2",
    name: second.name,
  });
  expect(result.current.target!.isCurrent()).toBe(true);
  expect(Object.isFrozen(result.current.target!.epoch)).toBe(true);
  expect(client.getQueryData(["portfolios", alice])).toEqual([first, second]);
  expect(result.current.redirectPortfolioId).toBeNull();
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith("/api/v2/portfolios", expect.anything());
});

it.each([undefined, "", "0", "01", "-1", "9223372036854775808", "foreign/name"])(
  "does not query or discover a substitute for required/malformed explicit target %j",
  async (id) => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const { result } = setup(id);
    await waitFor(() => expect(result.current.status).toBe("required"));
    expect(result.current.target).toBeNull();
    expect(result.current.redirectPortfolioId).toBeNull();
    await expect(result.current.refetch()).rejects.toThrow("Portfolio target changed");
    expect(fetch).not.toHaveBeenCalled();
  },
);

it.each([
  { items: [], state: "empty", redirect: null },
  { items: [first], state: "redirect", redirect: "1" },
  { items: [first, second], state: "ambiguous", redirect: null },
])(
  "legacy discovery with $state never returns financial authority",
  async ({ items, state, redirect }) => {
    vi.stubGlobal("fetch", () => Promise.resolve(json(items)));
    const { result } = setup(undefined, true);
    await waitFor(() => expect(result.current.status).toBe(state));
    expect(result.current.target).toBeNull();
    expect(result.current.redirectPortfolioId).toBe(redirect);
  },
);

it("does not redirect an unavailable explicit target even with one active alternative", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([first])));
  const { result } = setup("99", true);
  await waitFor(() => expect(result.current.status).toBe("unavailable"));
  expect(result.current.target).toBeNull();
  expect(result.current.redirectPortfolioId).toBeNull();
});

it("does not request metadata when signed out", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("1", false, null);
  expect(result.current.status).toBe("signed_out");
  expect(result.current.target).toBeNull();
  await expect(result.current.refetch()).rejects.toThrow("Portfolio target changed");
  expect(fetch).not.toHaveBeenCalled();
});

it("keeps a changed explicit route while its original metadata request finishes", async () => {
  let release!: (response: Response) => void;
  const fetch = vi.fn(
    () =>
      new Promise<Response>((resolve) => {
        release = resolve;
      }),
  );
  vi.stubGlobal("fetch", fetch);
  const { result, rerender } = setup("1");
  await waitFor(() => expect(release).toBeTypeOf("function"));
  const staleRecovery = result.current.refetch;
  rerender({ routeId: "2", legacy: false });
  expect(result.current.target).toBeNull();
  await expect(staleRecovery()).rejects.toThrow("Portfolio target changed");
  await act(async () => release(json([first, second])));
  await waitFor(() => expect(result.current.target?.portfolioId).toBe("2"));
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("invalidates captured target callbacks and epoch immediately when the route changes", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([first, second])));
  const { result, rerender } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  const original = result.current.target!;
  const staleRefetch = result.current.refetch;
  rerender({ routeId: "2", legacy: false });
  expect(result.current.target!.portfolioId).toBe("2");
  expect(result.current.target!.epoch).not.toBe(original.epoch);
  expect(original.isCurrent()).toBe(false);
  await expect(staleRefetch()).rejects.toThrow("Portfolio target changed");
  expect(original.isOriginalCurrent?.()).toBe(false);
  rerender({ routeId: "1", legacy: false });
  expect(result.current.target!.epoch).not.toBe(original.epoch);
  expect(original.isCurrent()).toBe(false);
});

it("suppresses owner A metadata and late responses after an account switch", async () => {
  let release!: (body: Response) => void;
  let signal!: AbortSignal;
  const fetch = vi.fn((_path: string, init: RequestInit) => {
    signal = init.signal!;
    return new Promise<Response>((resolve) => {
      release = resolve;
    });
  });
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup("1");
  await waitFor(() => expect(release).toBeTypeOf("function"));
  const oldRelease = release;
  const oldSignal = signal;
  act(() => client.setQueryData(["me"], { email: bob }));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  expect(oldSignal.aborted).toBe(true);
  expect(result.current.target).toBeNull();
  await act(async () => oldRelease(json([first])));
  expect(result.current.target).toBeNull();
  expect(client.getQueryData(["portfolios", alice])).toBeUndefined();
  await act(async () => release(json([second])));
  await waitFor(() => expect(result.current.status).toBe("unavailable"));
  expect(result.current.redirectPortfolioId).toBeNull();
});

it("invalidates old target handles across logout and return to the same owner", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json([first])));
  const { result, client } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  const original = result.current.target!;
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: alice });
  });
  expect(original.isCurrent()).toBe(false);
  await waitFor(() => {
    expect(result.current.status).toBe("ready");
    expect(result.current.target).not.toBeNull();
    expect(result.current.target!.epoch).not.toBe(original.epoch);
  });
  expect(result.current.target!.isCurrent()).toBe(true);
});

it("invalidates the target when fresh metadata removes its root", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json([first]))
    .mockResolvedValueOnce(json([second]));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  const original = result.current.target!;
  await act(async () => {
    await result.current.refetch();
  });
  expect(original.isCurrent()).toBe(false);
  await waitFor(() => expect(result.current.status).toBe("unavailable"));
  expect(original.isOriginalCurrent?.()).toBe(false);
  expect(result.current.target).toBeNull();
  expect(result.current.redirectPortfolioId).toBeNull();
});

it("never publishes a cancelled earlier metadata response after a newer root-loss result", async () => {
  let release!: (body: Response) => void;
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json([first]))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    )
    .mockResolvedValueOnce(json([second]));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  const original = result.current.target!;
  let pending!: ReturnType<typeof result.current.refetch>;
  act(() => {
    pending = result.current.refetch();
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.status).toBe("unavailable"));
  await act(async () => {
    release(json([first]));
    await pending;
  });
  expect(result.current.target).toBeNull();
  expect(original.isCurrent()).toBe(false);
  expect(client.getQueryData(["portfolios", alice])).toEqual([second]);
});

it("hides target authority on metadata failure and only retries the same target", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json([first]))
    .mockResolvedValueOnce(json({}, 500))
    .mockResolvedValueOnce(json([first]));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("ready"));
  const original = result.current.target!;
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.status).toBe("error"));
  expect(result.current.target).toBeNull();
  expect(original.isCurrent()).toBe(false);
  expect(original.isOriginalCurrent?.()).toBe(false);
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.target?.portfolioId).toBe("1"));
});

it("leaves api-version refusal visible without signing out or selecting a portfolio", async () => {
  vi.stubGlobal("fetch", () =>
    Promise.resolve(json({ detail: { code: "api_version_required" } }, 409)),
  );
  const { result, client } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("error"));
  expect(result.current.error).toBeInstanceOf(ApiError);
  expect(result.current.target).toBeNull();
  expect(client.getQueryData(["me"])).toEqual({ email: alice });
});

it("expires identity after metadata401 and does not reinterpret it as an empty portfolio", async () => {
  document.cookie = "bj_csrf=t; path=/";
  vi.stubGlobal("fetch", () => Promise.resolve(json({}, 401)));
  const { result, client } = setup("1");
  await waitFor(() => expect(result.current.status).toBe("signed_out"));
  expect(client.getQueryData(["me"])).toBeNull();
  expect(result.current.target).toBeNull();
  expect(client.getQueryData(["portfolios", alice])).toBeUndefined();
});
