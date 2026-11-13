import type { EventHistoryItem } from "@/api/eventHistory";

export function HistoryEventDetails({ item }: { item: EventHistoryItem }) {
  return <div data-event={item.id} />;
}
