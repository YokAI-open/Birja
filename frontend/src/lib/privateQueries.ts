import type { QueryClient } from "@tanstack/react-query";

/** Leave the active identity observer attached while discarding its private views. */
export async function clearPrivateQueries(queryClient: QueryClient): Promise<void> {
  const filters = {
    predicate: (query: { queryKey: readonly unknown[] }) => query.queryKey[0] !== "me",
  };
  await queryClient.cancelQueries(filters);
  queryClient.removeQueries(filters);
}
