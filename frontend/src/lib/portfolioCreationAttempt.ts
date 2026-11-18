import {
  normalizePortfolioDescription,
  portfolioNameDisplay,
  type PortfolioCreation,
} from "@/api/portfolioManagement";

export const CREATION_STORAGE_KEY = "birja:portfolio-creation:v1";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
type Original = Readonly<Required<PortfolioCreation>>;
type Envelope = { version: 1; nonce: string; binding: string; attempt: Original | null };
const storageError = () =>
  new Error("Creation recovery storage unavailable. Keep the original request for recovery.");
function original(value: unknown): Original {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw storageError();
  const v = value as Record<string, unknown>;
  if (
    Object.keys(v).sort().join() !== "description,key,name" ||
    typeof v.key !== "string" ||
    !uuid.test(v.key) ||
    portfolioNameDisplay(v.name) === null ||
    normalizePortfolioDescription(v.description) === null
  )
    throw storageError();
  return Object.freeze({
    key: v.key,
    name: v.name as string,
    description: v.description as string,
  });
}
async function binding(owner: string, nonce: string) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(`${nonce}\0${owner}`),
  );
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}
function read(): Envelope | null {
  const raw = sessionStorage.getItem(CREATION_STORAGE_KEY);
  if (raw === null) return null;
  if (raw.length > 16000) throw storageError();
  const v = JSON.parse(raw) as Envelope;
  if (
    !v ||
    Object.keys(v).sort().join() !== "attempt,binding,nonce,version" ||
    v.version !== 1 ||
    typeof v.nonce !== "string" ||
    !uuid.test(v.nonce) ||
    typeof v.binding !== "string" ||
    !/^[a-f0-9]{64}$/.test(v.binding)
  )
    throw storageError();
  return { ...v, attempt: v.attempt === null ? null : original(v.attempt) };
}
export function clearCreationRecovery() {
  try {
    sessionStorage.removeItem(CREATION_STORAGE_KEY);
  } catch {
    /* A failed clear remains fail-closed on next read. */
  }
}
/** Only non-secret intent metadata is persisted. Binding never authorizes an API call. */
export async function openCreationRecovery(owner: string, isCurrent: () => boolean = () => true) {
  try {
    let envelope = read();
    if (envelope && envelope.binding !== (await binding(owner, envelope.nonce))) {
      if (!isCurrent()) throw storageError();
      sessionStorage.removeItem(CREATION_STORAGE_KEY);
      envelope = null;
    }
    if (!envelope) {
      const nonce = crypto.randomUUID();
      envelope = { version: 1, nonce, binding: await binding(owner, nonce), attempt: null };
      if (!isCurrent()) throw storageError();
      sessionStorage.setItem(CREATION_STORAGE_KEY, JSON.stringify(envelope));
    }
    const captured = envelope;
    return {
      get attempt() {
        return captured.attempt;
      },
      persist(input: PortfolioCreation) {
        if (!isCurrent()) throw storageError();
        const attempt = original({ ...input, description: input.description ?? "" });
        const stored = read();
        if (
          !stored ||
          stored.binding !== captured.binding ||
          stored.nonce !== captured.nonce ||
          (stored.attempt && JSON.stringify(stored.attempt) !== JSON.stringify(attempt))
        )
          throw storageError();
        const next = { ...captured, attempt };
        const encoded = JSON.stringify(next);
        if (encoded.length > 16000) throw storageError();
        sessionStorage.setItem(CREATION_STORAGE_KEY, encoded);
        if (sessionStorage.getItem(CREATION_STORAGE_KEY) !== encoded) throw storageError();
        captured.attempt = attempt;
        return attempt;
      },
      resolve() {
        if (!isCurrent()) throw storageError();
        const stored = read();
        if (!stored || stored.binding !== captured.binding || stored.nonce !== captured.nonce)
          throw storageError();
        sessionStorage.setItem(
          CREATION_STORAGE_KEY,
          JSON.stringify({ ...captured, attempt: null }),
        );
        captured.attempt = null;
      },
    };
  } catch {
    throw storageError();
  }
}
export type CreationRecovery = Awaited<ReturnType<typeof openCreationRecovery>>;
