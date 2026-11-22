import { ApiError, apiFetch } from "./client";

/** Session identity is independent of the number of financial portfolios. */
export type Me = { email: string };

export function isMe(value: unknown): value is Me {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  return Object.keys(v).length === 1 && typeof v.email === "string" && v.email.length > 0;
}

function parseMe(body: unknown): Me {
  if (!isMe(body)) {
    throw new Error("Unexpected identity response");
  }
  return body;
}

/** Null means not signed in (401). Other failures throw. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  try {
    return parseMe(await apiFetch("/api/v2/me", { signal, cache: "no-store" }));
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
    await apiFetch("/api/v2/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({ email, code }),
      cache: "no-store",
    }),
  );
}

export async function logout(): Promise<void> {
  await apiFetch("/api/v1/auth/logout", { method: "POST" });
}
