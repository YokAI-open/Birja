import { useMutation, useQueryClient } from "@tanstack/react-query";
import { logout, requestCode, verifyCode, type Me } from "@/api/auth";
import { clearPrivateQueries } from "@/lib/privateQueries";

export function useRequestCode() {
  return useMutation({ mutationFn: (email: string) => requestCode(email) });
}

export function useVerifyCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ email, code }: { email: string; code: string }) => verifyCode(email, code),
    onSuccess: async (me: Me) => {
      await clearPrivateQueries(queryClient);
      queryClient.setQueryData(["me"], me);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: async () => {
      // queryClient.clear() would detach useMe's observer from the "me" query, so the
      // sign-in card would not show. Drop everything except "me", then set it to null.
      await clearPrivateQueries(queryClient);
      queryClient.setQueryData(["me"], null);
    },
  });
}
