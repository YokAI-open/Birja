import { CircleDot, Clock, TriangleAlert } from "lucide-react";
import type { PriceStatus } from "@/api/prices";
import { Badge } from "@/components/ui/badge";
import { formatAge, statusLabel } from "@/lib/age";

const VARIANT = { fresh: "success", aging: "warning", stale: "danger" } as const;
const ICON = { fresh: CircleDot, aging: Clock, stale: TriangleAlert } as const;

export function FreshnessBadge({
  status,
  ageSeconds,
  asOf,
}: {
  status: PriceStatus;
  ageSeconds: number;
  asOf?: string;
}) {
  const Icon = ICON[status];
  const timestamp =
    asOf && Number.isFinite(Date.parse(asOf)) ? new Date(asOf).toLocaleString() : undefined;
  return (
    <Badge variant={VARIANT[status]} title={timestamp}>
      <Icon aria-hidden="true" />
      {`${statusLabel(status)} · ${formatAge(ageSeconds)}`}
    </Badge>
  );
}
