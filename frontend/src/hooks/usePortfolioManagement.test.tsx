/// <reference types="node" />
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { webcrypto } from "node:crypto";
import { usePortfolioManagement } from "./usePortfolioManagement";
import { CREATION_STORAGE_KEY } from "@/lib/portfolioCreationAttempt";

const clients: QueryClient[] = [];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const receipt = { id: "2", name: "Original", description: "raw" };
function setup(
  id?: string,
  client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  }),
) {
  clients.push(client);
  if (!client.getQueryData(["me"])) client.setQueryData(["me"], { email: "alice@example.test" });
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
