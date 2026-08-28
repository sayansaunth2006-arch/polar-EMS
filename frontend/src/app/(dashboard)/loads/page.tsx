"use client";

import { useState } from "react";
import { ListTree, Clock3 } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api, type LoadItem } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { useAuthStore } from "@/lib/store";
import { toast } from "@/lib/toast";
import { cn } from "@/lib/utils";

const TIERS = [
  { priority: 1, label: "Critical", description: "Life support, comms, medical — never shed", color: "border-status-critical/40" },
  { priority: 2, label: "Important", description: "Research, labs, refrigeration", color: "border-status-warning/40" },
  { priority: 3, label: "Deferrable", description: "Scheduled charging, non-urgent experiments", color: "border-status-info/40" },
  { priority: 4, label: "Non-Critical", description: "Recreation, optional lighting", color: "border-border-strong" },
];

export default function LoadsPage() {
  const role = useAuthStore((s) => s.role);
  const isAdmin = role === "administrator";
  const [pending, setPending] = useState<number | null>(null);

  const { data: loads, loading, error, refetch } = useApiQuery(() => api.loadsList(), []);

  async function changePriority(load: LoadItem, priority: number) {
    if (!isAdmin) return;
    setPending(load.id);
    try {
      await api.updateLoadPriority(load.id, priority);
      toast.success(`${load.name} priority updated.`);
      refetch();
    } catch {
      toast.error("Failed to update load priority.");
    } finally {
      setPending(null);
    }
  }

  if (loading && !loads) return <LoadingState label="Loading load registry…" />;
  if (error && !loads) return <ErrorState message={error} onRetry={refetch} />;
  if (!loads) return null;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Load Management</h1>
          <p className="text-xs text-muted">
            {isAdmin ? "As Station Administrator, you can reassign load priorities." : "Priority changes require Station Administrator access."}
          </p>
        </div>
        <ListTree className="h-5 w-5 text-muted" />
      </div>

      {TIERS.map((tier) => {
        const tierLoads = loads.filter((l) => l.priority === tier.priority);
        const totalKw = tierLoads.reduce((s, l) => s + l.current_power_kw, 0);
        return (
          <Card key={tier.priority} className={cn("border-l-4", tier.color)}>
            <CardHeader>
              <div>
                <CardTitle>
                  Priority {tier.priority} — {tier.label}
                </CardTitle>
                <p className="text-[11px] text-muted">{tier.description}</p>
              </div>
              <span className="font-data text-sm text-foreground">{totalKw.toFixed(1)} kW</span>
            </CardHeader>
            <CardBody className="space-y-2">
              {tierLoads.length === 0 && <p className="text-xs text-muted">No loads assigned to this tier.</p>}
              {tierLoads.map((load) => (
                <div key={load.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-surface-raised px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-foreground">{load.name}</span>
                    {load.is_deferrable && (
                      <span className="flex items-center gap-1 rounded border border-status-info/30 bg-[var(--status-info-bg)] px-1.5 py-0.5 text-[10px] text-status-info">
                        <Clock3 className="h-2.5 w-2.5" /> deferrable
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-data text-xs text-muted">
                      {load.current_power_kw.toFixed(1)} / {load.rated_power_kw.toFixed(1)} kW
                    </span>
                    <select
                      value={load.priority}
                      disabled={!isAdmin || pending === load.id}
                      onChange={(e) => changePriority(load, Number(e.target.value))}
                      className="rounded border border-border-strong bg-background px-1.5 py-1 text-xs text-foreground disabled:opacity-50"
                    >
                      {TIERS.map((t) => (
                        <option key={t.priority} value={t.priority}>
                          {t.priority} — {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>
        );
      })}
    </div>
  );
}
