import { afterEach, expect, it, vi } from "vitest";
import {
  metadataEvent,
  subscribeMetadataEvents,
  broadcastMetadataChange,
} from "./portfolioMetadataEvents";
const scope = "12345678-1234-4234-8234-123456789abc";
afterEach(() => vi.unstubAllGlobals());
it("accepts only bounded identity-only events", () => {
  expect(metadataEvent({ scope, portfolioId: "2" })).toEqual({ scope, portfolioId: "2" });
  for (const value of [
    null,
    {},
    { scope, portfolioId: 2 },
    { scope, portfolioId: "01" },
    { scope: "x".repeat(2000), portfolioId: "2" },
    { scope, portfolioId: "2", name: "private" },
    { scope, portfolioId: "2", key: scope },
  ])
    expect(metadataEvent(value)).toBeNull();
});
it("accepts the finite lifecycle hint while rejecting authority and private payloads", () => {
  expect(metadataEvent({ scope, portfolioId: "2", kind: "lifecycle" })).toEqual({
    scope,
    portfolioId: "2",
    kind: "lifecycle",
  });
  for (const extra of [
    { kind: "closed" },
    { kind: "lifecycle", closed: true },
    { kind: "lifecycle", name: "Private" },
    { kind: "lifecycle", key: scope },
    { kind: "lifecycle", cash: "10000" },
  ]) expect(metadataEvent({ scope, portfolioId: "2", ...extra })).toBeNull();
});
it("broadcasts only opaque source/root and cleans up listeners/channel", () => {
  const close = vi.fn();
  const postMessage = vi.fn();
  let deliver!: (event: MessageEvent) => void;
  class Channel {
    postMessage = postMessage;
    close = close;
    addEventListener(_name: string, callback: (event: MessageEvent) => void) {
      deliver = callback;
    }
    removeEventListener = vi.fn();
  }
  vi.stubGlobal("BroadcastChannel", Channel);
  const changed = vi.fn();
  const dispose = subscribeMetadataEvents(changed);
  deliver(new MessageEvent("message", { data: { scope, portfolioId: "2" } }));
  deliver(
    new MessageEvent("message", { data: { scope, portfolioId: "2", description: "private" } }),
  );
  expect(changed).toHaveBeenCalledExactlyOnceWith("2");
  broadcastMetadataChange("2");
  expect(postMessage).toHaveBeenCalledWith({
    scope: expect.stringMatching(/^[a-f0-9-]{36}$/),
    portfolioId: "2",
  });
  dispose();
  expect(close).toHaveBeenCalledTimes(2);
});
