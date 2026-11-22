import { isPortfolioId } from "@/api/portfolios";

type MetadataEvent = Readonly<{ scope: string; portfolioId: string; kind?: "lifecycle" }>;
const listeners = new Set<(id: string, kind?: "lifecycle") => void>();
const channelName = "birja:portfolio-metadata:v1";
let sourceScope: string | undefined;
const source = () => (sourceScope ??= crypto.randomUUID());
/** A source nonce is routing metadata only, never proof of owner or authority. */
export function metadataEvent(value: unknown): MetadataEvent | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const v = value as Record<string, unknown>;
  if (
    !(
      Object.keys(v).sort().join() === "portfolioId,scope" ||
      (Object.keys(v).sort().join() === "kind,portfolioId,scope" && v.kind === "lifecycle")
    ) ||
    typeof v.scope !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(v.scope) ||
    !isPortfolioId(v.portfolioId)
  )
    return null;
  return Object.freeze({
    scope: v.scope,
    portfolioId: v.portfolioId,
    ...(v.kind === "lifecycle" ? { kind: "lifecycle" as const } : {}),
  });
}
export function subscribeMetadataEvents(changed: (id: string, kind?: "lifecycle") => void) {
  listeners.add(changed);
  let channel: BroadcastChannel | undefined;
  const receive = (event: MessageEvent) => {
    const parsed = metadataEvent(event.data);
    if (parsed && parsed.scope !== source()) {
      if (parsed.kind) changed(parsed.portfolioId, parsed.kind);
      else changed(parsed.portfolioId);
    }
  };
  try {
    channel = new BroadcastChannel(channelName);
    channel.addEventListener("message", receive);
  } catch {
    /* Window focus revalidation remains available. */
  }
  return () => {
    listeners.delete(changed);
    channel?.removeEventListener("message", receive);
    channel?.close();
  };
}
export function broadcastMetadataChange(portfolioId: string, kind?: "lifecycle") {
  if (!isPortfolioId(portfolioId)) return;
  listeners.forEach((fn) => (kind ? fn(portfolioId, kind) : fn(portfolioId)));
  let channel: BroadcastChannel | undefined;
  try {
    channel = new BroadcastChannel(channelName);
    channel.postMessage({ scope: source(), portfolioId, ...(kind ? { kind } : {}) });
  } catch {
    /* Advisory only: authoritative reads are always required. */
  } finally {
    channel?.close();
  }
}
