/// <reference types="node" />
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { webcrypto } from "node:crypto";
import { usePortfolioManagement } from "./usePortfolioManagement";
import { CREATION_STORAGE_KEY, openCreationRecovery } from "@/lib/portfolioCreationAttempt";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";
import { usePortfolioTarget } from "./usePortfolioTarget";

const clients: QueryClient[] = [];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const receipt = { id: "2", name: "Original", description: "raw" };
it.each(["owner","logout-return"])("does not refresh financial data after %s during metadata discovery",async(change)=>{
  let reads=0;
  let release!:(response:Response)=>void;
  const deferred=new Promise<Response>(resolve=>{release=resolve;});
  vi.stubGlobal("fetch",vi.fn((input:RequestInfo|URL,init?:RequestInit)=>{
    if(String(input)==="/api/v2/portfolios") {reads++;return reads===1?Promise.resolve(json([{id:"2",name:"Original"}])):deferred;}
    return Promise.resolve(json(init?.method==="PATCH"?{...receipt,name:"Renamed"}:receipt));
  }));
  const hook=setup("2");
  const wrapper=({children}:{children:ReactNode})=><QueryClientProvider client={hook.client}>{children}</QueryClientProvider>;
  const target=renderHook(()=>usePortfolioTarget("2"),{wrapper});
  await waitFor(()=>expect(target.result.current.status).toBe("ready"));
  await waitFor(()=>expect(hook.result.current.metadata).toEqual(receipt));
  act(()=>hook.result.current.editMetadata({name:"Renamed"}));
  const invalidate=vi.spyOn(hook.client,"invalidateQueries");
  let pending!:Promise<void>;
  act(()=>{pending=hook.result.current.saveMetadata();});
  await waitFor(()=>expect(reads).toBeGreaterThanOrEqual(2));
  expect(invalidate.mock.calls.some(([filter])=>["portfolio","history","eventHistory","portfolioOverview"].includes(String(filter?.queryKey?.[0])))).toBe(false);
  await act(async()=>{
    hook.client.setQueryData(["me"],null);
    hook.client.setQueryData(["me"],{email:change==="owner"?"bob@example.test":"alice@example.test"});
    release(json([{id:"2",name:"Renamed"}]));
    await pending;
  });
  expect(invalidate.mock.calls.some(([filter])=>["portfolio","history","eventHistory","portfolioOverview"].includes(String(filter?.queryKey?.[0])))).toBe(false);
});
function setup(
  id?: string,
  client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  }),
  seedIdentity = true,
) {
  clients.push(client);
  if (seedIdentity && !client.getQueryData(["me"]))
    client.setQueryData(["me"], { email: "alice@example.test" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return {
    client,
    ...renderHook(({ root }) => usePortfolioManagement(root), {
      wrapper,
      initialProps: { root: id },
    }),
  };
}
beforeEach(() => {
  vi.stubGlobal("crypto", webcrypto);
  document.cookie = "bj_csrf=test; path=/";
});
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((c) => c.clear());
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it.each(["owner", "logout-return"])(
  "does not invalidate overview after %s during awaited creation discovery refresh",
  async (change) => {
    let reads = 0;
    let release!: (value: Response) => void;
    const discovery = new Promise<Response>((resolve) => {
      release = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method === "POST") return Promise.resolve(json(receipt));
        reads++;
        return reads === 1 ? Promise.resolve(json([{ id: "1", name: "Original" }])) : discovery;
      }),
    );
    const hook = setup();
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={hook.client}>{children}</QueryClientProvider>
    );
    const target = renderHook(() => usePortfolioTarget("1"), { wrapper });
    await waitFor(() => expect(target.result.current.status).toBe("ready"));
    await waitFor(() => expect(hook.result.current.ready).toBe(true));
    let pending!: Promise<void>;
    act(() => {
      pending = hook.result.current.submitCreation({ name: "Original" });
    });
    await waitFor(() => expect(reads).toBe(2));
    const invalidate = vi.spyOn(hook.client, "invalidateQueries");
    await act(async () => {
      hook.client.setQueryData(["me"], null);
      hook.client.setQueryData(["me"], {
        email: change === "owner" ? "bob@example.test" : "alice@example.test",
      });
      release(
        json([
          { id: "1", name: "Original" },
          { id: "2", name: "Created" },
        ]),
      );
      await pending;
    });
    expect(invalidate).not.toHaveBeenCalledWith({
      queryKey: ["portfolioOverview", "alice@example.test"],
    });
    expect(hook.result.current.creation.receipt).toBeUndefined();
  },
);
it("persists before POST, freezes unknown raw intent and reloads only for explicit same-key retry", async () => {
  const fetch = vi.fn((_url: string, init: RequestInit): Promise<Response> => {
    expect(sessionStorage.getItem(CREATION_STORAGE_KEY)).toContain("Original");
    expect(init.method).toBe("POST");
    return Promise.reject(new TypeError("lost response"));
  });
  vi.stubGlobal("fetch", fetch);
  const first = setup();
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  await act(async () => {
    await first.result.current.submitCreation({ name: " Original ", description: "raw\r\n" });
  });
  expect(first.result.current.creation.phase).toBe("unknown");
  const original = first.result.current.creation.attempt!;
  await act(async () => {
    await first.result.current.submitCreation({ name: "Different" });
  });
  expect(fetch).toHaveBeenCalledTimes(1);
  first.unmount();
  const next = setup();
  await waitFor(() => expect(next.result.current.ready).toBe(true));
  expect(next.result.current.creation.attempt).toEqual(original);
  expect(fetch).toHaveBeenCalledTimes(1);
  fetch.mockImplementationOnce(() => Promise.resolve(json(receipt)));
  await act(async () => {
    await next.result.current.retryCreation();
  });
  expect(fetch.mock.calls[1][1].body).toBe(fetch.mock.calls[0][1].body);
  expect(new Headers(fetch.mock.calls[1][1].headers).get("Idempotency-Key")).toBe(original.key);
  expect(next.result.current.creation.phase).toBe("resolved");
  expect(next.result.current.creation.receipt?.metadata).toEqual(receipt);
});
it("blocks initial POST when recovery storage fails", async () => {
  vi.stubGlobal("fetch", vi.fn());
  const { result } = setup();
  await waitFor(() => expect(result.current.ready).toBe(true));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota");
  });
  await act(async () => {
    await result.current.submitCreation({ name: "Original" });
  });
  expect(result.current.creation.error?.message).toMatch(/storage/i);
  expect(fetch).not.toHaveBeenCalled();
});
it.each(["logout", "owner", "unmount"])(
  "suppresses late receipts and stale actions on %s",
  async (change) => {
    let release!: (response: Response) => void;
    const fetch = vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetch);
    const hook = setup();
    await waitFor(() => expect(hook.result.current.ready).toBe(true));
    const stale = hook.result.current.submitCreation;
    let pending!: Promise<unknown>;
    act(() => {
      pending = hook.result.current.submitCreation({ name: "Original" });
    });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    if (change === "unmount") hook.unmount();
    else
      act(() => {
        hook.client.setQueryData(
          ["me"],
          change === "logout" ? null : { email: "bob@example.test" },
        );
      });
    await act(async () => {
      release(json(receipt));
      await pending;
    });
    await act(async () => {
      await stale({ name: "Stale" });
    });
    expect(fetch).toHaveBeenCalledTimes(1);
    if (change !== "unmount") {
      expect(hook.result.current.creation.receipt).toBeUndefined();
      expect(sessionStorage.getItem(CREATION_STORAGE_KEY) ?? "").not.toContain("Original");
    }
  },
);
it("keeps a conflict unknown but permits corrected new intent only after definitive refusal", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json({ detail: { code: "creation_key_conflict" } }, 409))
    .mockResolvedValueOnce(json({ detail: { code: "name_taken" } }, 409))
    .mockResolvedValueOnce(json(receipt));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.ready).toBe(true));
  await act(async () => {
    await result.current.submitCreation({ name: "Original" });
  });
  const key = result.current.creation.attempt!.key;
  expect(result.current.creation.phase).toBe("unknown");
  await act(async () => {
    await result.current.retryCreation();
  });
  expect(result.current.creation.phase).toBe("editing");
  await act(async () => {
    await result.current.submitCreation({ name: "Corrected" });
  });
  expect(new Headers(fetch.mock.calls[2][1].headers).get("Idempotency-Key")).not.toBe(key);
});
it("closed replay resolves unavailable with no replacement request", async () => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(new TypeError("lost"))
    .mockResolvedValueOnce(json({ detail: { code: "portfolio_unavailable" } }, 404));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.ready).toBe(true));
  await act(async () => {
    await result.current.submitCreation({ name: "Original" });
    await result.current.retryCreation();
  });
  expect(result.current.creation.phase).toBe("unavailable");
  expect(result.current.creation.receipt).toBeUndefined();
  expect(fetch).toHaveBeenCalledTimes(2);
});
it("captured receipt cannot navigate after logout and the same owner returns", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json(receipt)));
  const { result, client } = setup();
  await waitFor(() => expect(result.current.ready).toBe(true));
  await act(async () => {
    await result.current.submitCreation({ name: "Original" });
  });
  const captured = result.current.creation.receipt!;
  expect(captured.isCurrent()).toBe(true);
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: "alice@example.test" });
  });
  expect(captured.isCurrent()).toBe(false);
  expect(result.current.creation.receipt).toBeUndefined();
});
it("refetches authoritative metadata on cross-tab change, retains dirty drafts and requires review", async () => {
  let server = { id: "2", name: "Original", description: "Server" };
  const fetch = vi.fn((_url: string, init: RequestInit) => {
    if (init.method === "PATCH") server = { ...server, ...JSON.parse(init.body as string) };
    return Promise.resolve(json(server));
  });
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("2");
  await waitFor(() => expect(result.current.metadata?.name).toBe("Original"));
  act(() => {
    result.current.editMetadata({ name: "Draft", description: "" });
  });
  server = { ...server, name: "Other tab" };
  act(() => {
    broadcastMetadataChange("2");
  });
  await waitFor(() => expect(result.current.metadata?.name).toBe("Other tab"));
  expect(result.current.draft).toEqual({ name: "Draft", description: "" });
  expect(result.current.reviewRequired).toBe(true);
  await act(async () => {
    await result.current.saveMetadata();
  });
  expect(fetch.mock.calls.filter(([, init]) => init.method === "PATCH")).toHaveLength(0);
  act(() => {
    result.current.reviewMetadata();
  });
  await act(async () => {
    await result.current.saveMetadata();
  });
  expect(server).toEqual({ id: "2", name: "Draft", description: "" });
  expect(result.current.draft).toBeNull();
});
it("ambiguous PATCH preserves the draft and refetches current same-ID metadata for explicit review", async () => {
  const fetch = vi.fn((_url: string, init: RequestInit) =>
    init.method === "PATCH"
      ? Promise.reject(new TypeError("lost"))
      : Promise.resolve(json(receipt)),
  );
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("2");
  await waitFor(() => expect(result.current.metadata).toEqual(receipt));
  act(() => {
    result.current.editMetadata({ description: "Retained" });
  });
  await waitFor(() => expect(result.current.draft).toEqual({ description: "Retained" }));
  await act(async () => {
    await result.current.saveMetadata();
  });
  expect(result.current.draft).toEqual({ description: "Retained" });
  await waitFor(() => expect(result.current.reviewRequired).toBe(true));
  expect(fetch.mock.calls.filter(([, init]) => init.method === "PATCH")).toHaveLength(1);
  expect(fetch.mock.calls.filter(([, init]) => init.method === "GET")).toHaveLength(2);
});
it("revokes captured edits across root changes and preserves original creation recovery", async () => {
  vi.stubGlobal("fetch", (url: string) =>
    Promise.resolve(json({ ...receipt, id: url.includes("/3/") ? "3" : "2" })),
  );
  const hook = setup("2");
  await waitFor(() => expect(hook.result.current.metadata?.id).toBe("2"));
  const oldEdit = hook.result.current.editMetadata;
  const oldSave = hook.result.current.saveMetadata;
  act(() => {
    hook.result.current.editMetadata({ name: "Old" });
  });
  hook.rerender({ root: "3" });
  expect(hook.result.current.draft).toBeNull();
  oldEdit({ name: "Stale" });
  await act(async () => {
    await oldSave();
  });
  await waitFor(() => expect(hook.result.current.metadata?.id).toBe("3"));
  expect(hook.result.current.draft).toBeNull();
});
it("cold authenticated identity resolution restores recovery without automatic POST", async () => {
  const original = {
    key: "12345678-1234-4234-8234-123456789abc",
    name: "Original",
    description: "raw",
  };
  (await openCreationRecovery("alice@example.test")).persist(original);
  const fetch = vi.fn(() => Promise.resolve(json({ email: "alice@example.test" })));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup(undefined, undefined, false);
  await waitFor(() => expect(result.current.ready).toBe(true));
  expect(result.current.creation.attempt).toEqual(original);
  expect(result.current.creation.phase).toBe("unknown");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith("/api/v2/me", expect.objectContaining({ method: "GET" }));
});
it.each(["logout", "owner", "root", "unmount"])(
  "suppresses late metadata save after %s",
  async (change) => {
    let release!: (response: Response) => void;
    let signal!: AbortSignal;
    const fetch = vi.fn((_url: string, init: RequestInit) => {
      if (init.method === "PATCH") {
        signal = init.signal!;
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      }
      return Promise.resolve(json(receipt));
    });
    vi.stubGlobal("fetch", fetch);
    const hook = setup("2");
    await waitFor(() => expect(hook.result.current.metadata).toEqual(receipt));
    act(() => {
      hook.result.current.editMetadata({ name: "Draft" });
    });
    let pending!: Promise<void>;
    act(() => {
      pending = hook.result.current.saveMetadata();
    });
    await waitFor(() => expect(release).toBeTypeOf("function"));
    if (change === "unmount") hook.unmount();
    else if (change === "root") hook.rerender({ root: "3" });
    else
      act(() =>
        hook.client.setQueryData(
          ["me"],
          change === "logout" ? null : { email: "bob@example.test" },
        ),
      );
    expect(signal.aborted).toBe(true);
    await act(async () => {
      release(json({ ...receipt, name: "Old saved" }));
      await pending;
    });
    if (change !== "unmount") expect(hook.result.current.metadata?.name).not.toBe("Old saved");
  },
);
it("focus fallback retains a dirty draft and forbids review until authoritative refresh completes", async () => {
  let release!: (response: Response) => void;
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json(receipt))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    );
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("2");
  await waitFor(() => expect(result.current.metadata).toEqual(receipt));
  act(() => {
    result.current.editMetadata({ name: "Draft" });
    window.dispatchEvent(new Event("focus"));
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  act(() => result.current.reviewMetadata());
  await act(async () => {
    await result.current.saveMetadata();
  });
  expect(fetch).toHaveBeenCalledTimes(2);
  await act(async () => release(json({ ...receipt, name: "Latest" })));
  await waitFor(() => expect(result.current.reviewRequired).toBe(true));
  expect(result.current.draft).toEqual({ name: "Draft" });
});
it("an aborted unmount permits same-original retry while its obsolete response remains unresolved", async () => {
  let release!: (response: Response) => void;
  const fetch = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    )
    .mockResolvedValueOnce(json(receipt));
  vi.stubGlobal("fetch", fetch);
  const first = setup();
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  let pending!: Promise<void>;
  act(() => {
    pending = first.result.current.submitCreation({ name: "Original" });
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  const original = first.result.current.creation.attempt;
  first.unmount();
  const next = setup(undefined, first.client);
  await waitFor(() => expect(next.result.current.creation.phase).toBe("unknown"));
  expect(next.result.current.creation.attempt).toEqual(original);
  await act(async () => {
    await next.result.current.retryCreation();
  });
  expect(next.result.current.creation.receipt?.metadata).toEqual(receipt);
  await act(async () => {
    release(json({ ...receipt, name: "Obsolete" }));
    await pending;
  });
  expect(next.result.current.creation.receipt?.metadata).toEqual(receipt);
});
it("a cross-tab change while PATCH is pending retains the draft for review of latest metadata", async () => {
  let release!: (response: Response) => void;
  let server = receipt;
  const fetch = vi.fn((_url: string, init: RequestInit) =>
    init.method === "PATCH"
      ? new Promise<Response>((resolve) => {
          release = resolve;
        })
      : Promise.resolve(json(server)),
  );
  vi.stubGlobal("fetch", fetch);
  const { result } = setup("2");
  await waitFor(() => expect(result.current.metadata).toEqual(receipt));
  act(() => result.current.editMetadata({ name: "Draft" }));
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.saveMetadata();
  });
  await waitFor(() => expect(release).toBeTypeOf("function"));
  server = { ...receipt, name: "Newer" };
  act(() => broadcastMetadataChange("2"));
  await waitFor(() => expect(result.current.metadata?.name).toBe("Newer"));
  await act(async () => {
    release(json({ ...receipt, name: "Draft" }));
    await pending;
  });
  await waitFor(() => expect(result.current.reviewRequired).toBe(true));
  expect(result.current.draft).toEqual({ name: "Draft" });
  expect(result.current.metadata?.name).toBe("Newer");
});
it.each([
  { source: "cross-tab", status: 409, code: "name_taken" },
  { source: "focus", status: 409, code: "name_taken" },
  { source: "cross-tab", status: 422, code: "invalid_input" },
  { source: "focus", status: 422, code: "invalid_input" },
])(
  "late $status refusal preserves review after $source authoritative refresh",
  async ({ source, status, code }) => {
    let release!: (response: Response) => void;
    let server = receipt;
    let patches = 0;
    const fetch = vi.fn((_url: string, init: RequestInit) => {
      if (init.method !== "PATCH") return Promise.resolve(json(server));
      patches++;
      if (patches === 1)
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      server = { ...server, ...JSON.parse(init.body as string) };
      return Promise.resolve(json(server));
    });
    vi.stubGlobal("fetch", fetch);
    const { result } = setup("2");
    await waitFor(() => expect(result.current.metadata).toEqual(receipt));
    act(() => result.current.editMetadata({ name: "Draft", description: "" }));
    let pending!: Promise<void>;
    act(() => {
      pending = result.current.saveMetadata();
    });
    await waitFor(() => expect(release).toBeTypeOf("function"));
    server = { ...receipt, name: "Newer authoritative", description: "Other tab description" };
    act(() => {
      if (source === "focus") window.dispatchEvent(new Event("focus"));
      else broadcastMetadataChange("2");
    });
    await waitFor(() => expect(result.current.metadata).toEqual(server));
    expect(result.current.reviewRequired).toBe(true);
    await act(async () => {
      release(json({ detail: { code } }, status));
      await pending;
    });
    await waitFor(() => expect(result.current.metadataError).not.toBeNull());
    expect(result.current.reviewRequired).toBe(true);
    expect(result.current.metadata).toEqual(server);
    expect(result.current.draft).toEqual({ name: "Draft", description: "" });
    await act(async () => {
      await result.current.saveMetadata();
    });
    expect(patches).toBe(1);
    act(() => result.current.reviewMetadata());
    await act(async () => {
      await result.current.saveMetadata();
    });
    expect(patches).toBe(2);
    expect(server).toEqual({ id: "2", name: "Draft", description: "" });
  },
);
