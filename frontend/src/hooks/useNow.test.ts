import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useNow } from "./useNow";

afterEach(() => vi.useRealTimers());

describe("useNow", () => {
  it("ticks every interval and clears on unmount", () => {
    vi.useFakeTimers();
    const { result, unmount } = renderHook(() => useNow(1000));
    const start = result.current;
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current).toBe(start + 1000);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});
