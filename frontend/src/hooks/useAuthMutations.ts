import { useMutation, useQueryClient } from "@tanstack/react-query";
import { requestCode, verifyCode, type Me } from "@/api/auth";

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
