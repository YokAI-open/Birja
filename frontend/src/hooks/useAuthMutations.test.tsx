import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { apiFetch } from "@/api/client";
import { useMe } from "./useMe";
import { useLogout, useVerifyCode } from "./useAuthMutations";

const a = { email: "a@example.test", cash_usd: "8123.45" };
const b = { email: "b@example.test", cash_usd: "10000.00" };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; max-age=0; path=/";
});

it.each([
  { action: "logout", initialMe: a, lateMe: a },
  { action: "verify", initialMe: a, lateMe: a },
  { action: "verify", initialMe: null, lateMe: null },
] as const)(
  "cancels pending me ($lateMe) before $action publishes identity",
  async ({ action, initialMe, lateMe }) => {
    document.cookie = "bj_csrf=test; path=/";
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(["me"], initialMe);
    client.setQueryData(["portfolio"], "A portfolio");
    client.setQueryData(["history"], "A history");
    client.setQueryData(["holding", "BTC"], "A holding");
    const signals: AbortSignal[] = [];
    const releases: ((response: Response) => void)[] = [];
    let meSignal!: AbortSignal;
    let releaseMe!: (response: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn((path: string, init: RequestInit) => {
        if (path === "/api/v1/me") {
          meSignal = init.signal as AbortSignal;
          return new Promise<Response>((resolve) => {
            releaseMe = resolve;
          });
        }
        if (path === "/api/v1/auth/verify-code") return Promise.resolve(json(b));
        if (path === "/api/v1/auth/logout")
          return Promise.resolve(new Response(null, { status: 204 }));
        signals.push(init.signal as AbortSignal);
        return new Promise<Response>((resolve) => releases.push(resolve));
      }),
    );
    const late = ["portfolio", "history"].map((key) =>
      client
        .fetchQuery({
          queryKey: [key],
          queryFn: ({ signal }) => apiFetch(`/api/v1/${key}`, { signal }),
        })
        .catch((error: unknown) => error),
    );
    const { result, unmount } = renderHook(
      () => ({ me: useMe(), verify: useVerifyCode(), logout: useLogout() }),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <QueryClientProvider client={client}>{children}</QueryClientProvider>
        ),
      },
    );
    const meQuery = client.getQueryCache().find({ queryKey: ["me"] });
    let pendingMe!: ReturnType<typeof result.current.me.refetch>;
    act(() => {
      pendingMe = result.current.me.refetch();
    });
    await waitFor(() => expect(releaseMe).toBeTypeOf("function"));
    expect(meSignal.aborted).toBe(false);
    const cancel = client.cancelQueries.bind(client);
    let finishCancel!: () => void;
    vi.spyOn(client, "cancelQueries").mockImplementation(async (filters) => {
      await cancel(filters);
      await new Promise<void>((resolve) => {
        finishCancel = resolve;
      });
    });
    const publications: unknown[] = [];
    const unsubscribe = client.getQueryCache().subscribe((event) => {
      if (event.type === "updated" && event.query === meQuery && event.action.type === "success") {
        publications.push(
          client
            .getQueryCache()
            .getAll()
            .map((query) => query.queryKey),
        );
      }
    });
    let pending!: Promise<unknown>;
    act(() => {
      pending =
        action === "verify"
          ? result.current.verify.mutateAsync({ email: b.email, code: "123456" })
          : result.current.logout.mutateAsync();
    });
    await waitFor(() => expect(signals.every((signal) => signal.aborted)).toBe(true));
    expect(signals).toHaveLength(2);
    expect(meSignal.aborted).toBe(true);
    expect(client.getQueryData(["me"])).toEqual(initialMe);
    expect(client.getQueryData(["history"])).toBe("A history");
    expect(publications).toEqual([]);
    await act(async () => {
      finishCancel();
      await pending;
    });
    expect(publications).toEqual([[["me"]]]);
    expect(client.getQueryCache().find({ queryKey: ["me"] })).toBe(meQuery);
    expect(meQuery!.getObserversCount()).toBe(1);
    await waitFor(() => expect(result.current.me.data).toEqual(action === "verify" ? b : null));
    await act(async () => {
      releaseMe(lateMe === null ? json({}, 401) : json(lateMe));
      releases.forEach((release) => release(json("late private A")));
      await Promise.all([...late, pendingMe]);
    });
    expect(client.getQueryData(["me"])).toEqual(action === "verify" ? b : null);
    expect(result.current.me.data).toEqual(action === "verify" ? b : null);
    expect(client.getQueryCache().getAll()).toEqual([meQuery]);
    unsubscribe();
    unmount();
    client.clear();
  },
);

it.each(["verify", "logout"] as const)(
  "retains the current identity and cache on failed %s",
  async (action) => {
    document.cookie = "bj_csrf=test; path=/";
    const client = new QueryClient();
    client.setQueryData(["me"], a);
    client.setQueryData(["portfolio"], "A portfolio");
    const cancel = vi.spyOn(client, "cancelQueries");
    vi.stubGlobal("fetch", () => Promise.resolve(json({}, 500)));
    const { result, unmount } = renderHook(
      () => ({ verify: useVerifyCode(), logout: useLogout() }),
      {
        wrapper: ({ children }: { children: ReactNode }) => (
          <QueryClientProvider client={client}>{children}</QueryClientProvider>
        ),
      },
    );
    await act(async () => {
      await expect(
        action === "verify"
          ? result.current.verify.mutateAsync({ email: b.email, code: "123456" })
          : result.current.logout.mutateAsync(),
      ).rejects.toMatchObject({ status: 500 });
    });
    expect(cancel).not.toHaveBeenCalled();
    expect(client.getQueryData(["me"])).toEqual(a);
    expect(client.getQueryData(["portfolio"])).toBe("A portfolio");
    unmount();
    client.clear();
  },
);
