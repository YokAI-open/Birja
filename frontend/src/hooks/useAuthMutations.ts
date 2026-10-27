import { useMutation, useQueryClient } from "@tanstack/react-query";
import { logout, requestCode, verifyCode, type Me } from "@/api/auth";

export function useRequestCode() {
  return useMutation({ mutationFn: (email: string) => requestCode(email) });
}

export function useVerifyCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ email, code }: { email: string; code: string }) => verifyCode(email, code),
    onSuccess: (me: Me) => {
      queryClient.setQueryData(["me"], me);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      // queryClient.clear() would detach useMe's observer from the "me" query, so the
      // sign-in card would not show. Drop everything except "me", then set it to null.
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== "me" });
      queryClient.setQueryData(["me"], null);
    },
  });
}
