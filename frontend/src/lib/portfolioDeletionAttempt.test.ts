/// <reference types="node" />
import { webcrypto } from "node:crypto";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { DELETION_STORAGE_KEY, openDeletionRecovery, clearDeletionRecovery } from "./portfolioDeletionAttempt";
import { CREATION_STORAGE_KEY } from "./portfolioCreationAttempt";

const original = { portfolioId: "9007199254740993", intentKey: "12345678-1234-4234-8234-123456789abc", confirmationName: "Café", policyVersion: "freeze_at_closure_v1" as const };
beforeEach(() => { vi.stubGlobal("crypto", webcrypto); });
afterEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("persists only a frozen owner-bound original and restores without performing a request", async () => {
  const fetcher = vi.fn(); vi.stubGlobal("fetch", fetcher);
  sessionStorage.setItem(CREATION_STORAGE_KEY, "unrelated creation");
  const first = await openDeletionRecovery("alice@example.test");
  expect(first.persist(original)).toEqual(original);
  const second = await openDeletionRecovery("alice@example.test");
  expect(second.attempt).toEqual(original);
  expect(Object.isFrozen(second.attempt)).toBe(true);
  const raw = sessionStorage.getItem(DELETION_STORAGE_KEY)!;
  expect(raw).not.toContain("alice@example.test");
  expect(raw).not.toMatch(/cash|balance|token|receipt/);
  expect(sessionStorage.getItem(CREATION_STORAGE_KEY)).toBe("unrelated creation");
  expect(fetcher).not.toHaveBeenCalled();
});
it("never overwrites an unknown original with a same-name replacement or different review", async () => {
  const store = await openDeletionRecovery("owner"); store.persist(original);
  for (const replacement of [{ ...original, portfolioId: "2" }, { ...original, confirmationName: "Changed" }, { ...original, intentKey: "ffffffff-ffff-4fff-afff-ffffffffffff" }])
    expect(() => store.persist(replacement)).toThrow();
  expect(store.persist(original)).toEqual(original);
  expect((await openDeletionRecovery("owner")).attempt).toEqual(original);
});
it("clears crossed-owner private context and revokes old handles", async () => {
  let current = true;
  const old = await openDeletionRecovery("alice", () => current); old.persist(original); current = false;
  const next = await openDeletionRecovery("bob");
  expect(next.attempt).toBeNull();
  next.persist({ ...original, portfolioId: "2" });
  expect(() => old.persist(original)).toThrow();
  expect(() => old.resolve()).toThrow();
  clearDeletionRecovery(() => current);
  expect(next.attempt?.portfolioId).toBe("2");
});
