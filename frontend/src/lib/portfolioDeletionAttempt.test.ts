/// <reference types="node" />
import { webcrypto } from "node:crypto";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  DELETION_STORAGE_KEY,
  openDeletionRecovery,
  clearDeletionRecovery,
} from "./portfolioDeletionAttempt";
import { CREATION_STORAGE_KEY } from "./portfolioCreationAttempt";

const original = {
  portfolioId: "9007199254740993",
  intentKey: "12345678-1234-4234-8234-123456789abc",
  confirmationName: "Café",
  policyVersion: "freeze_at_closure_v1" as const,
};
beforeEach(() => {
  vi.stubGlobal("crypto", webcrypto);
});
afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("persists only a frozen owner-bound original and restores without performing a request", async () => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
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
  const store = await openDeletionRecovery("owner");
  store.persist(original);
  for (const replacement of [
    { ...original, portfolioId: "2" },
    { ...original, confirmationName: "Changed" },
    { ...original, intentKey: "ffffffff-ffff-4fff-afff-ffffffffffff" },
  ])
    expect(() => store.persist(replacement)).toThrow();
  expect(store.persist(original)).toEqual(original);
  expect((await openDeletionRecovery("owner")).attempt).toEqual(original);
});
it("clears crossed-owner private context and revokes old handles", async () => {
  let current = true;
  const old = await openDeletionRecovery("alice", () => current);
  old.persist(original);
  current = false;
  const next = await openDeletionRecovery("bob");
  expect(next.attempt).toBeNull();
  next.persist({ ...original, portfolioId: "2" });
  expect(() => old.persist(original)).toThrow();
  expect(() => old.resolve()).toThrow();
  clearDeletionRecovery(() => current);
  expect(next.attempt?.portfolioId).toBe("2");
});

it.each([
  "{",
  "x".repeat(16001),
  '"not an envelope"',
  JSON.stringify({ version: 9 }),
  "😀".repeat(5000),
])("blocks corrupt or byte-oversized storage without erasing evidence", async (raw) => {
  sessionStorage.setItem(DELETION_STORAGE_KEY, raw);
  await expect(openDeletionRecovery("owner")).rejects.toThrow("storage unavailable");
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(raw);
});

it("validates every stored intent field and rejects extra financial or credential fields", async () => {
  const store = await openDeletionRecovery("owner");
  store.persist(original);
  const envelope = JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!);
  for (const attempt of [
    { ...original, portfolioId: "01" },
    { ...original, intentKey: "bad" },
    { ...original, policyVersion: "other" },
    { ...original, confirmationName: " Café" },
    { ...original, confirmationName: "Cafe\u0301" },
    { ...original, cash: "1" },
    null,
  ]) {
    const value = attempt === null ? { ...envelope, extra: "token" } : { ...envelope, attempt };
    const raw = JSON.stringify(value);
    sessionStorage.setItem(DELETION_STORAGE_KEY, raw);
    await expect(openDeletionRecovery("owner")).rejects.toThrow();
    expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(raw);
  }
});

it("refuses quota, read and readback failures before a caller can send", async () => {
  const store = await openDeletionRecovery("owner");
  const setter = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota private");
  });
  expect(() => store.persist(original)).toThrow("storage unavailable");
  expect(store.attempt).toBeNull();
  setter.mockRestore();
  const get = Storage.prototype.getItem;
  let reads = 0;
  const getter = vi.spyOn(Storage.prototype, "getItem").mockImplementation(function (
    this: Storage,
    key: string,
  ) {
    reads++;
    return reads === 1 ? get.call(this, key) : null;
  });
  expect(() => store.persist(original)).toThrow("storage unavailable");
  getter.mockRestore();
  // The failed readback is still unresolved metadata, never permission to replace it.
  expect((await openDeletionRecovery("owner")).attempt).toEqual(original);
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new Error("private access");
  });
  await expect(openDeletionRecovery("owner")).rejects.toThrow("storage unavailable");
});

it("serializes concurrent openers and refuses a stale observer clearing a later original", async () => {
  const first = openDeletionRecovery("owner");
  const second = openDeletionRecovery("owner");
  const one = await first;
  one.persist(original);
  const two = await second;
  expect(two.attempt).toEqual(original);
  expect(() => two.persist({ ...original, portfolioId: "2" })).toThrow();
  one.resolve();
  one.persist({ ...original, portfolioId: "2" });
  expect(() => two.resolve()).toThrow();
  expect((await openDeletionRecovery("owner")).attempt?.portfolioId).toBe("2");
});

it("checks session epoch on existing handles while same-owner reload can review its original", async () => {
  let epoch = 1;
  const old = await openDeletionRecovery("owner", () => epoch === 1);
  old.persist(original);
  epoch = 2;
  const current = await openDeletionRecovery("owner", () => epoch === 2);
  expect(current.attempt).toEqual(original);
  expect(() => old.attempt).toThrow();
  expect(() => old.persist(original)).toThrow();
  expect(() => old.resolve()).toThrow();
  current.resolve();
  expect(current.attempt).toBeNull();
  clearDeletionRecovery(() => epoch === 2);
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBeNull();
});

it("does not write after the owner changes during an awaited digest", async () => {
  let current = true;
  let release!: (value: ArrayBuffer) => void;
  vi.stubGlobal("crypto", {
    randomUUID: () => original.intentKey,
    subtle: {
      digest: () =>
        new Promise<ArrayBuffer>((resolve) => {
          release = resolve;
        }),
    },
  });
  const pending = openDeletionRecovery("owner", () => current).catch((error: unknown) => error);
  await vi.waitFor(() => expect(release).toBeTypeOf("function"));
  current = false;
  release(new ArrayBuffer(32));
  expect(await pending).toBeInstanceOf(Error);
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBeNull();
});

it("detects replacement of an envelope while matching its digest", async () => {
  (await openDeletionRecovery("owner")).persist(original);
  let release!: (value: ArrayBuffer) => void;
  vi.stubGlobal("crypto", {
    subtle: {
      digest: () =>
        new Promise<ArrayBuffer>((resolve) => {
          release = resolve;
        }),
    },
  });
  const pending = openDeletionRecovery("owner").catch((error: unknown) => error);
  await vi.waitFor(() => expect(release).toBeTypeOf("function"));
  const raw = JSON.stringify({
    ...JSON.parse(sessionStorage.getItem(DELETION_STORAGE_KEY)!),
    nonce: "ffffffff-ffff-4fff-afff-ffffffffffff",
  });
  sessionStorage.setItem(DELETION_STORAGE_KEY, raw);
  release(new ArrayBuffer(32));
  expect(await pending).toBeInstanceOf(Error);
  expect(sessionStorage.getItem(DELETION_STORAGE_KEY)).toBe(raw);
});

it("does not erase unresolved context when a guarded logout clear fails", async () => {
  const store = await openDeletionRecovery("owner");
  store.persist(original);
  vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
    throw new Error("readonly");
  });
  clearDeletionRecovery(() => true);
  expect(store.attempt).toEqual(original);
});
