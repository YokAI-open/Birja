import { CircleDot, Clock, TriangleAlert } from "lucide-react";
import type { PriceStatus } from "@/api/prices";
import { Badge } from "@/components/ui/badge";
import { formatAge, statusLabel } from "@/lib/age";

const VARIANT = { fresh: "success", aging: "warning", stale: "danger" } as const;
const ICON = { fresh: CircleDot, aging: Clock, stale: TriangleAlert } as const;

export function FreshnessBadge({
  status,
  ageSeconds,
}: {
  status: PriceStatus;
  ageSeconds: number;
}) {
  const Icon = ICON[status];
  return (
    <Badge variant={VARIANT[status]}>
      <Icon aria-hidden="true" />
      {`${statusLabel(status)} · ${formatAge(ageSeconds)}`}
    </Badge>
  );
}
