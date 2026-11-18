/// <reference types="node" />
import { afterEach, expect, it, vi } from "vitest";
import { webcrypto } from "node:crypto";
import { openCreationRecovery, CREATION_STORAGE_KEY } from "./portfolioCreationAttempt";

vi.stubGlobal("crypto", webcrypto);
const input = {
  key: "12345678-1234-4234-8234-123456789abc",
  name: "  e\u0301  ",
  description: "x\r\ny",
};
afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
});
it("stores one frozen raw original, restores same owner, and never persists email or money", async () => {
  const store = await openCreationRecovery("alice@example.test");
  store.persist(input);
  expect((await openCreationRecovery("alice@example.test")).attempt).toEqual(input);
  expect(Object.isFrozen((await openCreationRecovery("alice@example.test")).attempt)).toBe(true);
  const raw = sessionStorage.getItem(CREATION_STORAGE_KEY)!;
  expect(raw).not.toContain("alice@example.test");
  expect(raw).not.toMatch(/cash|receipt|token|balance/);
  expect(() => store.persist({ ...input, name: "é" })).toThrow();
});
it("clears crossed-owner intent without exposing its original", async () => {
  (await openCreationRecovery("alice@example.test")).persist(input);
  expect((await openCreationRecovery("bob@example.test")).attempt).toBeNull();
  expect(sessionStorage.getItem(CREATION_STORAGE_KEY)).not.toContain(input.key);
});
it.each([
  "{",
  "x".repeat(16001),
  JSON.stringify({ version: 1, key: input.key }),
  JSON.stringify({ version: 9 }),
])("blocks corrupted recovery instead of funding a replacement", async (raw) => {
  sessionStorage.setItem(CREATION_STORAGE_KEY, raw);
  await expect(openCreationRecovery("alice@example.test")).rejects.toThrow();
  expect(sessionStorage.getItem(CREATION_STORAGE_KEY)).toBe(raw);
});
it("refuses failed persistence and malformed originals before any transport", async () => {
  const store = await openCreationRecovery("alice@example.test");
  expect(() => store.persist({ ...input, key: "bad" })).toThrow();
  expect(() => store.persist({ ...input, description: "x".repeat(1001) })).toThrow();
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("quota");
  });
  expect(() => store.persist(input)).toThrow();
  expect(store.attempt).toBeNull();
});
it("concurrent recovery observers share a lifecycle rather than overwrite an outstanding original", async () => {
  const first = openCreationRecovery("alice@example.test");
  const second = openCreationRecovery("alice@example.test");
  const one = await first;
  one.persist(input);
  const two = await second;
  expect(two.attempt).toEqual(input);
  expect(two.persist(input)).toEqual(input);
});
