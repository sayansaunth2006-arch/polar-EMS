"use client";

import { useState } from "react";
import { Bell, RefreshCcw, CheckCircle2 } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/utils";
import { toast } from "@/lib/toast";

export default function AlertsPage() {
  const [generating, setGenerating] = useState(false);
  const { data: alerts, loading, error, refetch } = useApiQuery(() => api.alertsList(), [], { pollMs: 30000 });

  async function generate() {
    setGenerating(true);
    try {
      const res = await api.alertsGenerate();
      toast.info(`${res.alerts_created} new alert(s) generated from current thresholds.`);
      refetch();
    } catch {
      toast.error("Failed to generate alerts.");
    } finally {
      setGenerating(false);
    }
  }

  async function resolve(id: number) {
    try {
      await api.alertResolve(id);
      toast.success("Alert resolved.");
      refetch();
    } catch {
      toast.error("Failed to resolve alert.");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Alert Center</h1>
          <p className="text-xs text-muted">Threshold + forecast-driven alerts, evaluated against centrally configured safety limits</p>
        </div>
        <Button variant="primary" onClick={generate} disabled={generating}>
          <RefreshCcw className="h-4 w-4" />
          {generating ? "Checking…" : "Re-check Alerts"}
        </Button>
      </div>

      {loading && !alerts && <LoadingState label="Loading alerts…" />}
      {error && !alerts && <ErrorState message={error} onRetry={refetch} />}
      {alerts && alerts.length === 0 && <EmptyState label="No alerts. All monitored systems within safe thresholds." />}

      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((a) => (
            <Card key={a.id}>
              <CardBody className="space-y-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-status-warning" />
                    <span className="text-sm font-medium text-foreground">{a.message}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={a.severity} pulse />
                    <span className="text-[11px] text-muted-2">{formatDateTime(a.timestamp)}</span>
                  </div>
                </div>
                <p className="text-xs text-muted">{a.explanation}</p>
                <div className="rounded-md border border-accent/20 bg-accent/5 px-2.5 py-1.5 text-xs text-accent">→ {a.recommended_action}</div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-2">{a.affected_system}</span>
                  {!a.is_resolved ? (
                    <button onClick={() => resolve(a.id)} className="flex items-center gap-1 text-xs text-status-normal hover:underline">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Mark resolved
                    </button>
                  ) : (
                    <span className="text-xs text-status-normal">Resolved</span>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
