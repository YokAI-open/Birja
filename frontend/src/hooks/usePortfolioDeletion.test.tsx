/// <reference types="node" />
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { webcrypto } from "node:crypto";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  isPortfolioDeletionQuarantined,
  usePortfolioDeletion,
} from "./usePortfolioDeletion";
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
});

it("persists the exact original before DELETE and restores unknown without automatic mutation", async () => {
  let source!: QueryClient;
  const fetch = vi.fn((_url: string, init: RequestInit) => {
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
  act(() => hook.result.current.reviewDeletion(metadata));
  expect(hook.result.current.deletion.phase).toBe("terminal_refusal");
  const latest = { ...metadata, name: "Latest" };
  act(() => {
    hook.client.setQueryData(["portfolioMetadata", owner, "2", 0], latest);
    hook.result.current.reviewDeletion(latest);
  });
  expect(hook.result.current.deletion.phase).toBe("review");
  expect(hook.result.current.deletion.review?.intentKey).not.toBe(original?.intentKey);
  expect(fetch).toHaveBeenCalledTimes(3);
});
