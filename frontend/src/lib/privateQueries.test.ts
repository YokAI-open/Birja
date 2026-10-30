import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { expect, it, vi } from "vitest";
import { clearPrivateQueries } from "./privateQueries";

it("awaits private cancellation before removal and preserves the observed me query", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const me = { email: "a@example.test", cash_usd: "10000" };
  client.setQueryData(["me"], me);
  const observer = new QueryObserver(client, { queryKey: ["me"], staleTime: Infinity });
  const unsubscribe = observer.subscribe(() => {});
  const meQuery = client.getQueryCache().find({ queryKey: ["me"] });
  let signal!: AbortSignal;
  let release!: (value: string) => void;
  client.setQueryData(["portfolio"], "cached A");
  client.setQueryData(["history"], "cached A history");
  const pending = client
    .fetchQuery({
      queryKey: ["portfolio"],
      queryFn: (context) => {
        signal = context.signal;
        return new Promise<string>((resolve) => {
          release = resolve;
        });
      },
    })
    .catch((error: unknown) => error);
  const cancel = client.cancelQueries.bind(client);
  let finishCancel!: () => void;
  vi.spyOn(client, "cancelQueries").mockImplementation(async (filters) => {
    await cancel(filters);
    await new Promise<void>((resolve) => {
      finishCancel = resolve;
    });
  });
  const cleanup = clearPrivateQueries(client);
  await vi.waitFor(() => expect(signal.aborted).toBe(true));
  await vi.waitFor(() => expect(finishCancel).toBeTypeOf("function"));
  expect(client.getQueryData(["portfolio"])).toBe("cached A");
  expect(client.getQueryData(["history"])).toBe("cached A history");
  finishCancel();
  await cleanup;
  expect(client.getQueryCache().getAll()).toEqual([meQuery]);
  expect(meQuery!.getObserversCount()).toBe(1);
  expect(observer.getCurrentResult().data).toEqual(me);
  release("late A");
  await pending;
  await Promise.resolve();
  expect(client.getQueryData(["portfolio"])).toBeUndefined();
  client.setQueryData(["me"], null);
  expect(observer.getCurrentResult().data).toBeNull();
  unsubscribe();
  client.clear();
});
