/// <reference types="node" />
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { webcrypto } from "node:crypto";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { isPortfolioDeletionQuarantined, usePortfolioDeletion } from "./usePortfolioDeletion";
import { DELETION_STORAGE_KEY } from "@/lib/portfolioDeletionAttempt";

const owner = "alice@example.test";
const metadata = Object.freeze({ id: "2", name: "Original", description: "raw" });
const clients: QueryClient[] = [];
const json = (body: unknown, status = 200, extra?: Record<string, string>) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...extra },
  });
function setup(
  root: string | undefined = "2",
  client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  }),
) {
  clients.push(client);
  client.setQueryData(["me"], { email: owner });
  client.setQueryData(["portfolioMetadata", owner, "2", 0], metadata);
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return {
    client,
    ...renderHook(({ id }) => usePortfolioDeletion(id), {
      wrapper,
      initialProps: { id: root },
    }),
  };
}
beforeEach(() => {
  vi.stubGlobal("crypto", webcrypto);
  document.cookie = "bj_csrf=test; path=/";
});
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

it("persists the exact original before DELETE and restores unknown without automatic mutation", async () => {
  let source!: QueryClient;
  const fetch = vi.fn((_url: string, init: RequestInit): Promise<Response> => {
    expect(init.method).toBe("DELETE");
    expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toContain("Original");
    expect(isPortfolioDeletionQuarantined(source, owner, "2")).toBe(true);
    return Promise.reject(new TypeError("lost response"));
  });
  vi.stubGlobal("fetch", fetch);
  const first = setup();
  source = first.client;
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  act(() => first.result.current.reviewDeletion(metadata));
  await act(async () => first.result.current.confirmDeletion());
  expect(first.result.current.deletion.phase).toBe("unknown");
  const original = first.result.current.deletion.attempt;
  expect(fetch).toHaveBeenCalledTimes(1);
  act(() => first.result.current.reviewDeletion({ ...metadata, id: "3", name: "Other" }));
  expect(first.result.current.deletion.attempt).toEqual(original);
  first.unmount();
  const next = setup(undefined);
  source = next.client;
  await waitFor(() => expect(next.result.current.ready).toBe(true));
  expect(next.result.current.deletion.phase).toBe("unknown");
  expect(next.result.current.deletion.attempt).toEqual(original);
  window.dispatchEvent(new Event("focus"));
  expect(fetch).toHaveBeenCalledTimes(1);
  fetch.mockImplementationOnce(() => Promise.resolve(json({ portfolio_id: "2", state: "closed" })));
  await act(async () => next.result.current.checkDeletionResult());
  expect(fetch.mock.calls[1][1].body).toBe(fetch.mock.calls[0][1].body);
  expect(next.result.current.deletion.phase).toBe("closed");
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt).toBeNull();
});
it("preserves the durable unknown marker when identity metadata is garbage-collected", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject(new TypeError("lost"))),
  );
  const first = setup();
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  act(() => first.result.current.reviewDeletion(metadata));
  await act(async () => first.result.current.confirmDeletion());
  const original = first.result.current.deletion.attempt;
  const stored = sessionStorage.getItem(DELETION_STORAGE_KEY);
  first.unmount();
  act(() => first.client.removeQueries({ queryKey: ["me"], exact: true }));
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(stored);
  const next = setup(undefined);
  await waitFor(() => expect(next.result.current.ready).toBe(true));
  expect(next.result.current.deletion.attempt).toEqual(original);
  expect(next.result.current.deletion.phase).toBe("unknown");
});
it("lets only the current client logout clear the newer durable original", async () => {
  const fetch = vi.fn(() => Promise.reject(new TypeError("lost")));
  vi.stubGlobal("fetch", fetch);
  const old = setup();
  await waitFor(() => expect(old.result.current.ready).toBe(true));
  act(() => old.result.current.reviewDeletion(metadata));
  const obsoleteConfirm = old.result.current.confirmDeletion;
  const current = setup();
  await waitFor(() => expect(current.result.current.ready).toBe(true));
  expect(old.result.current.ready).toBe(false);
  act(() => current.result.current.reviewDeletion(metadata));
  await act(async () => current.result.current.confirmDeletion());
  const stored = sessionStorage.getItem(DELETION_STORAGE_KEY);
  expect(JSON.parse(stored!).attempt.portfolioId).toBe("2");
  act(() => old.client.setQueryData(["me"], null));
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(stored);
  await act(async () => {
    old.client.setQueryData(["me"], { email: "bob@example.test" });
  });
  expect(old.result.current.ready).toBe(false);
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(stored);
  await act(async () => obsoleteConfirm());
  expect(fetch).toHaveBeenCalledTimes(1);
  act(() => current.client.setQueryData(["me"], null));
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBeNull();
  expect(current.result.current.deletion.attempt).toBeNull();
});

it("refuses before sending if original recovery persistence fails", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota with private implementation detail");
  });
  await act(async () => hook.result.current.confirmDeletion());
  expect(fetch).not.toHaveBeenCalled();
  expect(hook.result.current.deletion.error?.message).toMatch(/storage/i);
  expect(hook.result.current.deletion.error?.message).not.toContain("private");
  expect(isPortfolioDeletionQuarantined(hook.client, owner, "2")).toBe(false);
});

it("only durable terminal refusal resolves an unknown original and requires fresh metadata review", async () => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(new TypeError("lost"))
    .mockResolvedValueOnce(json({ detail: { code: "closure_intent_conflict" } }, 409))
    .mockResolvedValueOnce(json({ detail: { code: "portfolio_confirmation_changed" } }, 409));
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  await act(async () => hook.result.current.confirmDeletion());
  const original = hook.result.current.deletion.attempt;
  await act(async () => hook.result.current.checkDeletionResult());
  expect(hook.result.current.deletion.phase).toBe("unknown");
  expect(hook.result.current.deletion.attempt).toEqual(original);
  await act(async () => hook.result.current.checkDeletionResult());
  expect(hook.result.current.deletion.phase).toBe("terminal_refusal");
  expect(hook.result.current.deletion.attempt).toBeNull();
  expect(isPortfolioDeletionQuarantined(hook.client, owner, "2")).toBe(true);
  act(() => hook.result.current.reviewDeletion(metadata));
  expect(hook.result.current.deletion.phase).toBe("terminal_refusal");
  const latest = { ...metadata, name: "Latest" };
  act(() => {
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], latest);
    hook.result.current.reviewDeletion(latest);
  });
  expect(hook.result.current.deletion.phase).toBe("review");
  expect(isPortfolioDeletionQuarantined(hook.client, owner, "2")).toBe(false);
  expect(hook.result.current.deletion.review?.intentKey).not.toBe(original?.intentKey);
  expect(fetch).toHaveBeenCalledTimes(3);
});

it("submits once for duplicate rendered confirmations and does not resolve from active GET data", async () => {
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
  act(() => hook.result.current.reviewDeletion(metadata));
  const confirm = hook.result.current.confirmDeletion;
  let first!: Promise<unknown>;
  await act(async () => {
    first = confirm();
    await confirm();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  act(() => hook.client.setQueryData(["portfolios", owner], [{ id: "2", name: "Original" }]));
  expect(hook.result.current.deletion.phase).toBe("submitting");
  await act(async () => {
    release(json({ portfolio_id: "different", state: "closed" }));
    await first;
  });
  expect(hook.result.current.deletion.phase).toBe("unknown");
  const original = hook.result.current.deletion.attempt;
  act(() => {
    hook.client.setQueryData(["portfolios", owner], [{ id: "2", name: "Original" }]);
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], metadata);
  });
  expect(hook.result.current.deletion.attempt).toEqual(original);
  expect(hook.result.current.deletion.phase).toBe("unknown");
});

it("keeps an interrupted original outside the unmounted financial route and ignores obsolete results", async () => {
  let release!: (response: Response) => void;
  let signal!: AbortSignal;
  const fetch = vi.fn((_url: string, init: RequestInit) => {
    signal = init.signal!;
    return new Promise<Response>((resolve) => {
      release = resolve;
    });
  });
  vi.stubGlobal("fetch", fetch);
  const first = setup();
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  act(() => first.result.current.reviewDeletion(metadata));
  let pending!: Promise<unknown>;
  act(() => {
    pending = first.result.current.confirmDeletion();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  const original = first.result.current.deletion.attempt;
  first.unmount();
  expect(signal.aborted).toBe(true);
  const next = setup(undefined, first.client);
  await waitFor(() => expect(next.result.current.deletion.phase).toBe("unknown"));
  expect(next.result.current.deletion.attempt).toBe(original);
  await act(async () => {
    release(json({ portfolio_id: "2", state: "closed" }));
    await pending;
  });
  expect(next.result.current.deletion.phase).toBe("unknown");
  expect(next.result.current.deletion.receipt).toBeUndefined();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it.each(["owner", "logout-return", "route-return"])(
  "revokes stale %s callbacks and receipts",
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
    act(() => hook.result.current.reviewDeletion(metadata));
    const staleConfirm = hook.result.current.confirmDeletion;
    let pending!: Promise<unknown>;
    act(() => {
      pending = staleConfirm();
    });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    if (change === "route-return") {
      hook.rerender({ id: "3" });
      hook.rerender({ id: "2" });
    } else
      act(() => {
        hook.client.setQueryData(["me"], null);
        hook.client.setQueryData(["me"], {
          email: change === "owner" ? "bob@example.test" : owner,
        });
      });
    await act(async () => {
      release(json({ portfolio_id: "2", state: "closed" }));
      await pending;
      await staleConfirm();
    });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(hook.result.current.deletion.receipt).toBeUndefined();
    expect(hook.result.current.deletion.phase).not.toBe("closed");
    if (change !== "route-return")
      expect(sessionStorage.getItem(DELETION_STORAGE_KEY) ?? "").not.toContain("Original");
  },
);

it("invalidates a named review on rename even when the name changes back", async () => {
  const fetch = vi.fn(() => Promise.resolve(json({ portfolio_id: "2", state: "closed" })));
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  const oldReview = hook.result.current.deletion.review;
  const oldConfirm = hook.result.current.confirmDeletion;
  act(() => {
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], {
      ...metadata,
      name: "Changed",
    });
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], metadata);
  });
  expect(hook.result.current.canConfirm).toBe(false);
  expect(hook.result.current.deletion.review).toEqual(oldReview);
  await act(async () => {
    await oldConfirm();
    await hook.result.current.confirmDeletion();
  });
  expect(fetch).not.toHaveBeenCalled();
  act(() => hook.result.current.reviewDeletion(metadata));
  expect(hook.result.current.deletion.review?.intentKey).not.toBe(oldReview?.intentKey);
  await act(async () => hook.result.current.confirmDeletion());
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("preserves a named review through a description-only change and safe cancel sends nothing", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  const stale = hook.result.current.confirmDeletion;
  act(() =>
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], {
      ...metadata,
      description: "Updated",
    }),
  );
  expect(hook.result.current.canConfirm).toBe(true);
  act(() => hook.result.current.cancelReview());
  await act(async () => stale());
  expect(hook.result.current.deletion.phase).toBe("idle");
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
});

it("a captured confirmation refuses metadata work appearing after named review", async () => {
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  const confirm = hook.result.current.confirmDeletion;
  act(() =>
    hook.client.setQueryData(["portfolioMetadataDraft", owner, "2", 0], {
      draft: { description: "Unresolved" },
      reviewRequired: true,
    }),
  );
  expect(hook.result.current.canConfirm).toBe(false);
  await act(async () => confirm());
  expect(fetch).not.toHaveBeenCalled();
  expect(hook.result.current.deletion.phase).toBe("review");
});

it("honors server Retry-After without automatically retrying the original", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(
      json({ detail: { code: "service_unavailable" } }, 503, { "Retry-After": "5" }),
    )
    .mockResolvedValueOnce(json({ portfolio_id: "2", state: "closed" }));
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  vi.useFakeTimers();
  act(() => hook.result.current.reviewDeletion(metadata));
  await act(async () => hook.result.current.confirmDeletion());
  expect(hook.result.current.canCheck).toBe(false);
  await act(async () => hook.result.current.checkDeletionResult());
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async () => vi.advanceTimersByTimeAsync(5000));
  expect(hook.result.current.canCheck).toBe(true);
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async () => hook.result.current.checkDeletionResult());
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(hook.result.current.deletion.phase).toBe("closed");
});

it("retains unknown original when storage cannot resolve a matching closed receipt", async () => {
  const fetch = vi.fn(() => Promise.resolve(json({ portfolio_id: "2", state: "closed" })));
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  const originalWrite = Storage.prototype.setItem;
  const write = vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
    this: Storage,
    key,
    value,
  ) {
    if (key === DELETION_STORAGE_KEY && JSON.parse(value).attempt === null)
      throw new Error("unavailable");
    originalWrite.call(this, key, value);
  });
  await act(async () => hook.result.current.confirmDeletion());
  expect(hook.result.current.deletion.phase).toBe("unknown");
  expect(isPortfolioDeletionQuarantined(hook.client, owner, "2")).toBe(true);
  write.mockRestore();
  await act(async () => hook.result.current.checkDeletionResult());
  expect(hook.result.current.deletion.phase).toBe("closed");
});

it.each([
  [401, "invalid_session"],
  [403, "csrf_failed"],
  [404, "portfolio_unavailable"],
  [422, "invalid_input"],
  [429, "closure_quota"],
])("keeps the unknown original after a later %s request refusal", async (status, code) => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(new TypeError("lost"))
    .mockResolvedValueOnce(json({ detail: { code } }, Number(status)));
  vi.stubGlobal("fetch", fetch);
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  await act(async () => hook.result.current.confirmDeletion());
  const original = hook.result.current.deletion.attempt;
  await act(async () => hook.result.current.checkDeletionResult());
  expect(hook.result.current.deletion.phase).toBe("unknown");
  expect(hook.result.current.deletion.attempt).toEqual(original);
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt).toEqual(original);
  expect(isPortfolioDeletionQuarantined(hook.client, owner, "2")).toBe(true);
});

it("a late durable refusal cannot clear a newer explicitly reviewed original", async () => {
  let release!: (response: Response) => void;
  const refused = () => json({ detail: { code: "portfolio_confirmation_changed" } }, 409);
  const fetch = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    )
    .mockImplementationOnce(() => Promise.resolve(refused()));
  vi.stubGlobal("fetch", fetch);
  const first = setup();
  await waitFor(() => expect(first.result.current.ready).toBe(true));
  act(() => first.result.current.reviewDeletion(metadata));
  let pending!: Promise<unknown>;
  act(() => {
    pending = first.result.current.confirmDeletion();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  first.unmount();
  const next = setup("2", first.client);
  await waitFor(() => expect(next.result.current.deletion.phase).toBe("unknown"));
  await act(async () => next.result.current.checkDeletionResult());
  const latest = { ...metadata, name: "Latest" };
  act(() => {
    next.client.setQueryData(["portfolioMetadata", owner, "2", 0], latest);
    next.result.current.reviewDeletion(latest);
  });
  const newReview = next.result.current.deletion.review;
  await act(async () => {
    release(refused());
    await pending;
  });
  expect(next.result.current.deletion.phase).toBe("review");
  expect(next.result.current.deletion.review).toBe(newReview);
  expect(next.result.current.canConfirm).toBe(true);
});

it("does not let a cached closed target become a new deletion review", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(json({ portfolio_id: "2", state: "closed" })));
  const hook = setup();
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  act(() => hook.result.current.reviewDeletion(metadata));
  await act(async () => hook.result.current.confirmDeletion());
  act(() => hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], metadata));
  act(() => {
    expect(hook.result.current.reviewDeletion(metadata)).toBe(false);
  });
  expect(hook.result.current.deletion.phase).toBe("closed");
});

it.each(["owner", "route"])(
  "does not navigate after %s changes during closed-list discovery",
  async (change) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(json({ portfolio_id: "2", state: "closed" })));
    const base = setup();
    base.unmount();
    const onClosed = vi.fn();
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={base.client}>{children}</QueryClientProvider>
    );
    const hook = renderHook(({ route }) => usePortfolioDeletion("2", { route, onClosed }), {
      wrapper,
      initialProps: { route: "first" },
    });
    await waitFor(() => expect(hook.result.current.ready).toBe(true));
    let release!: () => void;
    const pendingDiscovery = new Promise<void>((resolve) => {
      release = resolve;
    });
    vi.spyOn(base.client, "invalidateQueries").mockImplementationOnce(() => pendingDiscovery);
    act(() => hook.result.current.reviewDeletion(metadata));
    let pending!: ReturnType<typeof hook.result.current.confirmDeletion>;
    act(() => {
      pending = hook.result.current.confirmDeletion();
    });
    await waitFor(() => expect(hook.result.current.deletion.phase).toBe("closed"));
    act(() => {
      if (change === "owner") base.client.setQueryData(["me"], { email: "bob@example.test" });
      else hook.rerender({ route: "second" });
    });
    await act(async () => {
      release();
      await pending;
    });
    expect(onClosed).not.toHaveBeenCalled();
  },
);

it("retains known closure when list discovery fails and invokes only a current receipt callback", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(json({ portfolio_id: "2", state: "closed" })));
  const base = setup();
  base.unmount();
  const onClosed = vi.fn();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={base.client}>{children}</QueryClientProvider>
  );
  const hook = renderHook(() => usePortfolioDeletion("2", { onClosed }), { wrapper });
  await waitFor(() => expect(hook.result.current.ready).toBe(true));
  vi.spyOn(base.client, "invalidateQueries").mockRejectedValueOnce(new Error("discovery failed"));
  act(() => hook.result.current.reviewDeletion(metadata));
  await act(async () => hook.result.current.confirmDeletion());
  expect(hook.result.current.deletion.phase).toBe("closed");
  expect(hook.result.current.deletion.error?.message).toMatch(/list unavailable/i);
  expect(onClosed).toHaveBeenCalledTimes(1);
  expect(onClosed.mock.calls[0][0].isCurrent()).toBe(true);
  expect(JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!).attempt).toBeNull();
});
