import type { QueryClient } from "@tanstack/react-query";

/** Leave the active identity observer attached while discarding its private views. */
export async function clearPrivateQueries(queryClient: QueryClient): Promise<void> {
  const filters = {
    predicate: (query: { queryKey: readonly unknown[] }) => query.queryKey[0] !== "me",
  };
  // Identity reads can also finish with the previous session's result. Cancel
  // them before publication, but retain the query object and its active observer.
  await queryClient.cancelQueries();
  queryClient.removeQueries(filters);
}
