import { ApiError, apiFetch } from "./client";

export type Me = { email: string; cash_usd: string };

export function isMe(value: unknown): value is Me {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  return typeof v.email === "string" && typeof v.cash_usd === "string";
}

function parseMe(body: unknown): Me {
  if (!isMe(body)) {
    throw new Error("Unexpected account response");
  }
  return body;
}

/** Null means not signed in (401). Other failures throw. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  try {
    return parseMe(await apiFetch("/api/v1/me", { signal }));
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export async function requestCode(email: string): Promise<void> {
  await apiFetch("/api/v1/auth/request-code", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function verifyCode(email: string, code: string): Promise<Me> {
  return parseMe(
    await apiFetch("/api/v1/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  );
}
