import type { StockAction } from "@/api/stocks";

import { stockActionSummary } from "@/lib/stockActionCopy";

/** Fixed public enum copy only: no provider event or privileged review payload. */
export function StockActionState({
  action,
  valuationAvailable,
}: {
  action?: StockAction;
  valuationAvailable: boolean;
}) {
  const checked = action?.checked_at;
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return (
    <div className="flex min-w-0 flex-col gap-1 break-words">
      <p className="font-medium">Corporate actions</p>
      <p className={action?.state === "current" ? undefined : "text-warn-text"}>
        {stockActionSummary(action)}
      </p>
      {action?.state === "suspended" && action.reason !== "post_split_quote_missing" && (
        <p>Corporate-action review is still required. A price update does not clear it.</p>
      )}
      {!valuationAvailable && <p>Valuation unavailable</p>}
      {checked ? (
        <p>
          Corporate actions checked:{" "}
          <time dateTime={checked} className="tabular-nums">
            {new Intl.DateTimeFormat(undefined, {
              dateStyle: "medium",
              timeStyle: "long",
              timeZone: zone,
            }).format(new Date(checked))}{" "}
            ({zone})
          </time>
          .
        </p>
      ) : (
        <p>Corporate-action check time unavailable.</p>
      )}
    </div>
  );
}
