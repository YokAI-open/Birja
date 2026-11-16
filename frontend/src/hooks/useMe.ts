import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { fetchMe } from "@/api/auth";

type IdentityGuard = { email: string | null; epoch: number };
const guards = new WeakMap<QueryClient, IdentityGuard>();
const owner = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;

function identityGuard(client: QueryClient): IdentityGuard {
  const existing = guards.get(client);
  if (existing) return existing;
  const guard = { email: owner(client), epoch: 0 };
  guards.set(client, guard);
  client.getQueryCache().subscribe(() => {
    const email = owner(client);
    if (email === guard.email) return;
    guard.email = email;
    guard.epoch++;
    // Removal cancels old in-flight private observers as well as cached data.
    // Keep the identity query object attached during sign-out/account switches.
    client.removeQueries({ predicate: (query) => query.queryKey[0] !== "me" });
  });
  return guard;
}

export function useMe() {
  const client = useQueryClient();
  const guard = identityGuard(client);
  return useQuery({
    queryKey: ["me"],
    queryFn: async ({ signal }) => {
      const epoch = guard.epoch;
      const identity = await fetchMe(signal);
      signal.throwIfAborted();
      if (epoch !== guard.epoch) throw new Error("Identity session changed");
      return identity;
    },
    retry: false,
    staleTime: 60_000,
  });
}
