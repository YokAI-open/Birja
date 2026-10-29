import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDebouncedValue } from "./useDebouncedValue";

afterEach(() => vi.useRealTimers());

describe("useDebouncedValue", () => {
  it("keeps the old value until the delay passes without change", () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: "a" },
    });
    expect(result.current).toBe("a");
    rerender({ v: "b" });
    act(() => vi.advanceTimersByTime(299));
    expect(result.current).toBe("a");
    rerender({ v: "c" });
    act(() => vi.advanceTimersByTime(299));
    expect(result.current).toBe("a");
    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe("c");
  });

  it("clears the timer on unmount", () => {
    vi.useFakeTimers();
    const { rerender, unmount } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: 1 },
    });
    rerender({ v: 2 });
    expect(vi.getTimerCount()).toBe(1);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});
