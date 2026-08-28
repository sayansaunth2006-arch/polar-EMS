"use client";

import { Fuel, Gauge, Clock, Leaf, Wrench, TrendingDown } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

export default function GeneratorPage() {
  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [status, history, comparison] = await Promise.all([api.generatorStatus(), api.generatorHistory(48), api.generatorComparison()]);
      return { status, history, comparison };
    },
    [],
    { pollMs: 20000 }
  );

  if (loading && !data) return <LoadingState label="Loading generator telemetry…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { status, history, comparison } = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Generator Management — {status.name}</h1>
          <p className="text-xs text-muted">Rated {status.rated_capacity_kw} kW · synthetic telemetry</p>
        </div>
        <StatusBadge status={status.status === "running" ? "NORMAL" : "INFO"} />
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
        <StatTile icon={Gauge} label="Output" value={status.output_kw.toFixed(0)} unit="kW" hint={`of ${status.rated_capacity_kw} kW rated`} />
        <StatTile icon={Fuel} label="Fuel Level" value={status.fuel_level_pct.toFixed(0)} unit="%" status={status.fuel_status} />
        <StatTile icon={Clock} label="Runtime" value={status.runtime_hours.toFixed(0)} unit="h" />
        <StatTile icon={Wrench} label="Maintenance" value={status.maintenance_status} />
        <StatTile icon={Leaf} label="CO₂ Factor" value={status.co2_kg_per_l.toFixed(2)} unit="kg/L" />
        <StatTile icon={TrendingDown} label="Fuel Rate" value={status.fuel_consumption_l_per_kwh.toFixed(2)} unit="L/kWh" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Output & Fuel Level (48h)</CardTitle>
          <span className="text-[10px] text-muted-2">
            {history.total_fuel_consumed_l.toFixed(0)} L consumed · {history.total_co2_kg.toFixed(0)} kg CO₂ (period)
          </span>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart
            data={history.points}
            series={[
              { key: "output_kw", label: "Output", color: "#f59e0b", unit: "kW" },
              { key: "fuel_level_pct", label: "Fuel", color: "#38bdf8", unit: "%" },
            ]}
            height={280}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Baseline vs. AI-Optimized Dispatch</CardTitle>
          <span className="text-[10px] text-muted-2">{comparison.note}</span>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-2">BASELINE (generator follows demand directly)</p>
            <div className="flex justify-between rounded-md border border-border bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">Fuel use (24h)</span>
              <span className="font-data text-foreground">{comparison.baseline_fuel_l} L</span>
            </div>
            <div className="flex justify-between rounded-md border border-border bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">CO₂ emissions</span>
              <span className="font-data text-foreground">{comparison.baseline_co2_kg} kg</span>
            </div>
            <div className="flex justify-between rounded-md border border-border bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">Renewable utilization</span>
              <span className="font-data text-foreground">{comparison.baseline_renewable_utilization_pct}%</span>
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-status-normal">AI-OPTIMIZED (forecast + battery aware)</p>
            <div className="flex justify-between rounded-md border border-status-normal/30 bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">Fuel use (24h)</span>
              <span className="font-data text-status-normal">{comparison.optimized_fuel_l} L</span>
            </div>
            <div className="flex justify-between rounded-md border border-status-normal/30 bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">CO₂ emissions</span>
              <span className="font-data text-status-normal">{comparison.optimized_co2_kg} kg</span>
            </div>
            <div className="flex justify-between rounded-md border border-status-normal/30 bg-surface-raised px-3 py-2 text-sm">
              <span className="text-muted">Renewable utilization</span>
              <span className="font-data text-status-normal">{comparison.optimized_renewable_utilization_pct}%</span>
            </div>
          </div>
          <div className="sm:col-span-2 rounded-md border border-accent/30 bg-accent/5 px-3 py-2 text-center text-sm">
            Estimated savings: <span className="font-data text-accent">{comparison.estimated_fuel_saved_l} L</span> fuel ·{" "}
            <span className="font-data text-accent">{comparison.estimated_co2_saved_kg} kg</span> CO₂
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
