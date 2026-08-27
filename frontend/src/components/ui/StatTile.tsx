import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusBadge } from "./StatusBadge";

export function StatTile({
  icon: Icon,
  label,
  value,
  unit,
  status,
  hint,
  className,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  unit?: string;
  status?: "NORMAL" | "WARNING" | "CRITICAL";
  hint?: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-border bg-surface p-3.5", className)}>
      <div className="flex flex-wrap items-start justify-between gap-x-2 gap-y-1">
        <div className="flex min-w-0 items-center gap-2 text-muted">
          <Icon className="h-4 w-4 shrink-0" />
          <span className="truncate text-xs">{label}</span>
        </div>
        {status && (
          <div className="shrink-0">
            <StatusBadge status={status} pulse />
          </div>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="font-data text-2xl font-semibold text-foreground">{value}</span>
        {unit && <span className="text-xs text-muted">{unit}</span>}
      </div>
      {hint && <p className="mt-1 text-[11px] text-muted-2">{hint}</p>}
    </div>
  );
}
