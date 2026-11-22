import {
  capturePortfolioDeletionIntent,
  type PortfolioDeletionIntent,
} from "@/api/portfolioDeletion";

export const DELETION_STORAGE_KEY = "birja:portfolio-deletion:v1";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const encoder = new TextEncoder();
type Envelope = {
  version: 1;
  nonce: string;
  binding: string;
  attempt: PortfolioDeletionIntent | null;
};
const storageError = () =>
  new Error("Deletion recovery storage unavailable. No new deletion can be sent.");
const encoded = (value: Envelope) => {
  const raw = JSON.stringify(value);
  if (encoder.encode(raw).byteLength > 16000) throw storageError();
  return raw;
};
function read(): Envelope | null {
  const raw = sessionStorage.getItem(DELETION_STORAGE_KEY);
  if (raw === null) return null;
  if (encoder.encode(raw).byteLength > 16000) throw storageError();
  const value: unknown = JSON.parse(raw);
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw storageError();
  const v = value as Record<string, unknown>;
  if (
    Object.keys(v).sort().join() !== "attempt,binding,nonce,version" ||
    v.version !== 1 ||
    typeof v.nonce !== "string" ||
    !uuid.test(v.nonce) ||
    typeof v.binding !== "string" ||
    !/^[a-f0-9]{64}$/.test(v.binding)
  )
    throw storageError();
  return {
    version: 1,
    nonce: v.nonce,
    binding: v.binding,
    attempt: v.attempt === null ? null : capturePortfolioDeletionIntent(v.attempt),
  };
}
async function binding(owner: string, nonce: string) {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(`${nonce}\0${owner}`));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}
function write(value: Envelope, check: () => void) {
  const raw = encoded(value);
  check();
  sessionStorage.setItem(DELETION_STORAGE_KEY, raw);
  check();
  if (sessionStorage.getItem(DELETION_STORAGE_KEY) !== raw) throw storageError();
  check();
}

/** Logout/owner-change cleanup requires the caller's current session guard. */
export function clearDeletionRecovery(isCurrent: () => boolean) {
  if (!isCurrent()) return;
  try {
    sessionStorage.removeItem(DELETION_STORAGE_KEY);
  } catch {
    /* Next read remains fail-closed. */
  }
}

/** Metadata is only recovery context: neither opening nor reading sends any API request. */
async function openRecovery(owner: string, isCurrent: () => boolean) {
  const check = () => {
    if (!isCurrent()) throw storageError();
  };
  try {
    check();
    if (typeof owner !== "string" || owner.length === 0 || owner.length > 1024)
      throw storageError();
    let envelope = read();
    if (envelope) {
      const expected = await binding(owner, envelope.nonce);
      check();
      const latest = read();
      check();
      if (!latest || latest.nonce !== envelope.nonce || latest.binding !== envelope.binding)
        throw storageError();
      envelope = latest;
      if (envelope.binding !== expected) {
        check();
        sessionStorage.removeItem(DELETION_STORAGE_KEY);
        check();
        envelope = null;
      }
    }
    if (!envelope) {
      const nonce = crypto.randomUUID();
      const hash = await binding(owner, nonce);
      check();
      // Do not overwrite an entry created while the digest was awaiting.
      if (read() !== null) throw storageError();
      envelope = { version: 1, nonce, binding: hash, attempt: null };
      write(envelope, check);
    }
    const captured = envelope;
    const latest = () => {
      check();
      const stored = read();
      check();
      if (!stored || stored.nonce !== captured.nonce || stored.binding !== captured.binding)
        throw storageError();
      return stored;
    };
    return {
      get attempt() {
        captured.attempt = latest().attempt;
        return captured.attempt;
      },
      persist(input: PortfolioDeletionIntent) {
        try {
          check();
          const attempt = capturePortfolioDeletionIntent(input);
          const stored = latest();
          if (stored.attempt !== null && JSON.stringify(stored.attempt) !== JSON.stringify(attempt))
            throw storageError();
          write({ ...captured, attempt }, check);
          captured.attempt = attempt;
          return attempt;
        } catch {
          throw storageError();
        }
      },
      /** Resolve only the original observed by this lease, never another observer's new intent. */
      resolve() {
        try {
          const stored = latest();
          if (JSON.stringify(stored.attempt) !== JSON.stringify(captured.attempt))
            throw storageError();
          write({ ...captured, attempt: null }, check);
          captured.attempt = null;
        } catch {
          throw storageError();
        }
      },
    };
  } catch {
    throw storageError();
  }
}
let opening: Promise<unknown> = Promise.resolve();
export function openDeletionRecovery(owner: string, isCurrent: () => boolean = () => true) {
  const result = opening.then(() => openRecovery(owner, isCurrent));
  opening = result.catch(() => undefined);
  return result;
}
export type DeletionRecovery = Awaited<ReturnType<typeof openDeletionRecovery>>;
