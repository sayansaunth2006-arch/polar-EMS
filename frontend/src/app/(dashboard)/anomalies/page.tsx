"use client";

import { useState } from "react";
import { AlertTriangle, ScanSearch, CheckCircle2 } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/utils";
import { toast } from "@/lib/toast";

export default function AnomaliesPage() {
  const [scanning, setScanning] = useState(false);
  const { data: anomalies, loading, error, refetch } = useApiQuery(() => api.anomalyList(), []);

  async function runScan() {
    setScanning(true);
    try {
      const res = await api.anomalyScan();
      toast.success(`Scan complete: ${res.new_anomalies_saved} new anomalies found (${res.scanned_findings} total flagged).`);
      refetch();
    } catch {
      toast.error("Anomaly scan failed.");
    } finally {
      setScanning(false);
    }
  }

  async function resolve(id: number) {
    try {
      await api.anomalyResolve(id);
      refetch();
    } catch {
      toast.error("Failed to resolve anomaly.");
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">AI Anomaly Detection</h1>
          <p className="text-xs text-muted">Isolation Forest (consumption/battery/renewable) + deterministic checks (generator efficiency, sensor faults)</p>
        </div>
        <Button variant="primary" onClick={runScan} disabled={scanning}>
          <ScanSearch className="h-4 w-4" />
          {scanning ? "Scanning…" : "Run Anomaly Scan"}
        </Button>
      </div>

      {loading && !anomalies && <LoadingState label="Loading anomalies…" />}
      {error && !anomalies && <ErrorState message={error} onRetry={refetch} />}

      {anomalies && anomalies.length === 0 && <EmptyState label="No anomalies detected. Run a scan to analyze recent telemetry." />}

      {anomalies && anomalies.length > 0 && (
        <div className="space-y-2">
          {anomalies.map((a) => (
            <Card key={a.id}>
              <CardBody className="flex flex-col gap-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-status-warning" />
                    <span className="text-sm font-medium text-foreground">{a.affected_asset}</span>
                    <span className="text-xs text-muted">· {a.metric}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={a.severity} />
                    <span className="text-[11px] text-muted-2">{formatDateTime(a.timestamp)}</span>
                  </div>
                </div>
                <p className="text-xs text-muted">{a.explanation}</p>
                <div className="flex flex-wrap items-center gap-4 text-[11px]">
                  <span>
                    Observed: <span className="font-data text-foreground">{a.observed_value}</span>
                  </span>
                  <span>
                    Expected: <span className="font-data text-foreground">{a.expected_value}</span>
                  </span>
                  <span>
                    Deviation: <span className="font-data text-foreground">{a.deviation_pct > 0 ? "+" : ""}{a.deviation_pct}%</span>
                  </span>
                  {!a.is_resolved && (
                    <button onClick={() => resolve(a.id)} className="ml-auto flex items-center gap-1 text-status-normal hover:underline">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Mark resolved
                    </button>
                  )}
                  {a.is_resolved && <span className="ml-auto text-status-normal">Resolved</span>}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
