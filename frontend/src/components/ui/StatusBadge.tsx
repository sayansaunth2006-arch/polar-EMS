import { cn } from "@/lib/utils";

type Status = "NORMAL" | "WARNING" | "CRITICAL" | "INFO" | string;

const STYLES: Record<string, string> = {
  NORMAL: "bg-[var(--status-normal-bg)] text-status-normal border-status-normal/30",
  WARNING: "bg-[var(--status-warning-bg)] text-status-warning border-status-warning/30",
  CRITICAL: "bg-[var(--status-critical-bg)] text-status-critical border-status-critical/30",
  INFO: "bg-[var(--status-info-bg)] text-status-info border-status-info/30",
};

const DOT: Record<string, string> = {
  NORMAL: "bg-status-normal",
  WARNING: "bg-status-warning",
  CRITICAL: "bg-status-critical",
  INFO: "bg-status-info",
};

export function StatusBadge({ status, pulse = false }: { status: Status; pulse?: boolean }) {
  const key = status.toUpperCase();
  const style = STYLES[key] ?? STYLES.INFO;
  const dot = DOT[key] ?? DOT.INFO;
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-medium", style)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", dot, pulse && key === "CRITICAL" && "animate-pulse-dot")} />
      {key}
    </span>
  );
}

const PRIORITY_STYLES: Record<string, string> = {
  low: "bg-surface-raised text-muted border-border-strong",
  medium: "bg-[var(--status-info-bg)] text-status-info border-status-info/30",
  high: "bg-[var(--status-warning-bg)] text-status-warning border-status-warning/30",
  critical: "bg-[var(--status-critical-bg)] text-status-critical border-status-critical/30",
};

export function PriorityBadge({ priority }: { priority: string }) {
  const style = PRIORITY_STYLES[priority.toLowerCase()] ?? PRIORITY_STYLES.low;
  return <span className={cn("inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium uppercase", style)}>{priority}</span>;
}
