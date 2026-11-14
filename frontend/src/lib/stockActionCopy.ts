import type { StockAction } from "@/api/stocks";

const reasons: Record<StockAction["reason"], string> = {
  none: "",
  monitor_unavailable: "",
  source_gap: "We cannot verify complete corporate-action information for this stock.",
  unsupported: "This corporate action needs review before this stock can be valued.",
  fractional: "This action may create fractional shares and needs review.",
  conflicting: "Corporate-action information has changed or conflicts and needs review.",
  identity_change: "This stock’s identity is changing and needs review.",
  post_split_quote_missing: "",
};

export function stockActionSummary(action?: StockAction): string {
  if (action?.reason === "post_split_quote_missing")
    return "Waiting for a post-split quote. Valuation is unavailable.";
  if (action?.state === "current") return "Corporate actions checked.";
  if (action?.state === "reconciling")
    return "Checking corporate actions… Valuation is unavailable until checks finish.";
  if (action?.state === "suspended")
    return `Suspended for corporate-action review. ${reasons[action.reason]}`.trim();
  return `Corporate-action checks unavailable. Valuation is unavailable until checks are current. ${action ? reasons[action.reason] : ""}`.trim();
}
