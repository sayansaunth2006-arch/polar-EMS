"use client";

import { useState } from "react";
import { PlayCircle, Snowflake, CloudRain, Wind, BatteryWarning, TrendingUp, PowerOff, Fuel, AlertOctagon } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api, type SimulationOutcome } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PriorityBadge, StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { toast } from "@/lib/toast";

const SCENARIO_ICON: Record<string, React.ElementType> = {
  extreme_cold_wave: Snowflake,
  solar_drop: CloudRain,
  high_wind: Wind,
  battery_low_soc: BatteryWarning,
  demand_spike: TrendingUp,
  generator_unavailable: PowerOff,
  low_fuel: Fuel,
  equipment_failure: AlertOctagon,
};

export default function SimulationPage() {
  const { data: scenarios, loading, error, refetch } = useApiQuery(() => api.simulationScenarios(), []);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [outcome, setOutcome] = useState<SimulationOutcome | null>(null);

  async function runScenario(key: string) {
    setRunning(true);
    setActiveKey(key);
    try {
      const result = await api.simulationRun(key);
      setOutcome(result);
      toast.success(`Scenario "${result.scenario?.name}" applied — dashboard recalculated.`);
    } catch {
      toast.error("Simulation failed to run.");
    } finally {
      setRunning(false);
    }
  }

  if (loading && !scenarios) return <LoadingState label="Loading simulation scenarios…" />;
  if (error && !scenarios) return <ErrorState message={error} onRetry={refetch} />;
  if (!scenarios) return null;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-base font-semibold text-foreground">Simulation Mode</h1>
        <p className="text-xs text-muted">Activate a scenario to see AI forecasting, alerts, and optimization recalculate against a stressed condition.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {scenarios.map((s) => {
          const Icon = SCENARIO_ICON[s.key] ?? PlayCircle;
          const active = activeKey === s.key;
          return (
            <Card key={s.key} className={active ? "border-accent/50" : undefined}>
              <CardBody className="flex h-full flex-col gap-2">
                <Icon className={active ? "h-5 w-5 text-accent" : "h-5 w-5 text-muted"} />
                <p className="text-sm font-medium text-foreground">{s.name}</p>
                <p className="flex-1 text-[11px] text-muted">{s.description}</p>
                <Button variant={active ? "primary" : "secondary"} size="sm" onClick={() => runScenario(s.key)} disabled={running}>
                  <PlayCircle className="h-3.5 w-3.5" />
                  {running && active ? "Running…" : "Activate"}
                </Button>
              </CardBody>
            </Card>
          );
        })}
      </div>

      {outcome && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recalculated State — {outcome.scenario?.name}</CardTitle>
              <div className="flex gap-2">
                <StatusBadge status={outcome.result.battery_status} />
                <StatusBadge status={outcome.result.fuel_status} />
              </div>
            </CardHeader>
            <CardBody className="grid grid-cols-2 gap-3 sm:grid-cols-6">
              {(
                [
                  ["Demand", outcome.baseline.demand_kw, outcome.result.demand_kw, "kW"],
                  ["Solar", outcome.baseline.solar_kw, outcome.result.solar_kw, "kW"],
                  ["Wind", outcome.baseline.wind_kw, outcome.result.wind_kw, "kW"],
                  ["Battery SOC", outcome.baseline.battery_soc_pct, outcome.result.battery_soc_pct, "%"],
                  ["Generator", outcome.baseline.generator_output_kw, outcome.result.generator_output_kw, "kW"],
                  ["Fuel", outcome.baseline.fuel_pct, outcome.result.fuel_pct, "%"],
                ] as [string, number, number, string][]
              ).map(([label, before, after, unit]) => (
                <div key={label} className="rounded-md border border-border bg-surface-raised p-2.5 text-center">
                  <p className="text-[10px] text-muted-2">{label}</p>
                  <p className="font-data text-sm text-foreground">
                    {before.toFixed(0)} → <span className="text-accent">{after.toFixed(0)}</span> {unit}
                  </p>
                </div>
              ))}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Recommendations Under This Scenario</CardTitle>
            </CardHeader>
            <CardBody className="space-y-2">
              {outcome.recommendations.map((r, i) => (
                <div key={i} className="rounded-md border border-border bg-surface-raised p-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-foreground">{r.recommendation}</span>
                    <PriorityBadge priority={r.priority} />
                  </div>
                  <p className="mt-1 text-[11px] text-muted">{r.reason}</p>
                </div>
              ))}
            </CardBody>
          </Card>

          {outcome.safety_notes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Safety Constraints Applied</CardTitle>
              </CardHeader>
              <CardBody className="space-y-1">
                {outcome.safety_notes.map((n, i) => (
                  <p key={i} className="text-xs text-status-warning">
                    ⚠ {n}
                  </p>
                ))}
              </CardBody>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Estimated Fuel & CO₂ Savings vs. Baseline Strategy</CardTitle>
            </CardHeader>
            <CardBody className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
                <p className="text-[11px] text-muted-2">Fuel saved</p>
                <p className="font-data text-lg text-status-normal">{outcome.comparison.estimated_fuel_saved_l} L</p>
              </div>
              <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
                <p className="text-[11px] text-muted-2">CO₂ saved</p>
                <p className="font-data text-lg text-status-normal">{outcome.comparison.estimated_co2_saved_kg} kg</p>
              </div>
              <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
                <p className="text-[11px] text-muted-2">Renewable util. (optimized)</p>
                <p className="font-data text-lg text-foreground">{outcome.comparison.optimized_renewable_utilization_pct}%</p>
              </div>
              <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
                <p className="text-[11px] text-muted-2">Renewable util. (baseline)</p>
                <p className="font-data text-lg text-foreground">{outcome.comparison.baseline_renewable_utilization_pct}%</p>
              </div>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}
