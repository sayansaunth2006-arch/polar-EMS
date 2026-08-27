"use client";

import { SlidersHorizontal, Battery, Fuel, Power, ArrowDownCircle } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { PriorityBadge, StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState } from "@/components/ui/States";

const ACTION_ICON: Record<string, React.ElementType> = {
  charge_battery: Battery,
  discharge_battery: Battery,
  start_generator: Power,
  stop_generator: Power,
  shed_deferrable_load: ArrowDownCircle,
  shed_non_critical_load: ArrowDownCircle,
  maintain: SlidersHorizontal,
};

export default function OptimizationPage() {
  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [recs, comparison] = await Promise.all([api.optimizationRecommendations(), api.optimizationBaselineComparison()]);
      return { recs, comparison };
    },
    [],
    { pollMs: 30000 }
  );

  if (loading && !data) return <LoadingState label="Computing optimization recommendations…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { recs, comparison } = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Energy Optimization Engine</h1>
          <p className="text-xs text-muted">Explainable rule-based dispatch: protects critical loads, maximizes renewables, minimizes diesel & CO₂</p>
        </div>
        <div className="flex gap-2">
          <StatusBadge status={recs.battery_status} />
          <StatusBadge status={recs.fuel_status} />
        </div>
      </div>

      <div className="space-y-3">
        {recs.recommendations.map((r, i) => {
          const Icon = ACTION_ICON[r.action_type] ?? SlidersHorizontal;
          return (
            <Card key={i}>
              <CardBody className="space-y-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-start gap-2.5">
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                    <div>
                      <p className="text-sm font-medium text-foreground">{r.recommendation}</p>
                      <span className="text-[10px] uppercase tracking-wide text-muted-2">{r.kind.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                  <PriorityBadge priority={r.priority} />
                </div>
                <div className="grid grid-cols-1 gap-2 border-t border-border pt-2 text-xs sm:grid-cols-2">
                  <p>
                    <span className="text-muted-2">Why: </span>
                    <span className="text-muted">{r.reason}</span>
                  </p>
                  <p>
                    <span className="text-muted-2">Expected benefit: </span>
                    <span className="text-muted">{r.expected_benefit}</span>
                  </p>
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>24H Baseline vs. Optimized Estimate</CardTitle>
          <Fuel className="h-4 w-4 text-muted" />
        </CardHeader>
        <CardBody className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="text-[11px] text-muted-2">Baseline fuel</p>
            <p className="font-data text-lg text-foreground">{comparison.baseline_fuel_l} L</p>
          </div>
          <div className="rounded-md border border-status-normal/30 bg-surface-raised p-3 text-center">
            <p className="text-[11px] text-muted-2">Optimized fuel</p>
            <p className="font-data text-lg text-status-normal">{comparison.optimized_fuel_l} L</p>
          </div>
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="text-[11px] text-muted-2">Baseline CO₂</p>
            <p className="font-data text-lg text-foreground">{comparison.baseline_co2_kg} kg</p>
          </div>
          <div className="rounded-md border border-status-normal/30 bg-surface-raised p-3 text-center">
            <p className="text-[11px] text-muted-2">Optimized CO₂</p>
            <p className="font-data text-lg text-status-normal">{comparison.optimized_co2_kg} kg</p>
          </div>
        </CardBody>
        {comparison.note && <p className="border-t border-border px-4 py-2 text-[11px] text-muted-2">{comparison.note}</p>}
      </Card>
    </div>
  );
}
