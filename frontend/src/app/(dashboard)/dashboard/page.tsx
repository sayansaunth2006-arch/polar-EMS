"use client";

import {
  Zap,
  Sun,
  Wind,
  BatteryCharging,
  Fuel,
  Leaf,
  Gauge,
  ThermometerSnowflake,
  ShieldAlert,
} from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { StatusBadge, PriorityBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { EnergyFlowDiagram } from "@/components/dashboard/EnergyFlowDiagram";
import { formatDateTime } from "@/lib/utils";

async function loadDashboard() {
  const [energy, battery, generator, weather, history, alerts, recs, loads] = await Promise.all([
    api.energyCurrent(),
    api.batteryStatus(),
    api.generatorStatus(),
    api.weatherCurrent(),
    api.energyHistory(24),
    api.alertsList(false),
    api.optimizationRecommendations(),
    api.loadsList(),
  ]);
  return { energy, battery, generator, weather, history, alerts, recs, loads };
}

export default function DashboardPage() {
  const { data, loading, error, refetch } = useApiQuery(loadDashboard, [], { pollMs: 30000 });

  if (loading && !data) return <LoadingState label="Loading station overview…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { energy, battery, generator, weather, history, alerts, recs, loads } = data;

  const loadTiers = [
    { label: "Critical", kw: loads.filter((l) => l.priority === 1).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Important", kw: loads.filter((l) => l.priority === 2).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Deferrable", kw: loads.filter((l) => l.priority === 3).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Non-Critical", kw: loads.filter((l) => l.priority === 4).reduce((s, l) => s + l.current_power_kw, 0) },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Polar Research Station Alpha — Command Center</h1>
          <p className="text-xs text-muted">Synthetic demo data · last updated {formatDateTime(energy.timestamp)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        <StatTile icon={Zap} label="Generation" value={energy.total_generation_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Gauge} label="Demand" value={energy.demand_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Sun} label="Solar" value={energy.solar_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Wind} label="Wind" value={energy.wind_kw.toFixed(0)} unit="kW" />
        <StatTile icon={BatteryCharging} label="Battery" value={battery.soc_pct.toFixed(0)} unit="%" status={battery.status} />
        <StatTile icon={Fuel} label="Fuel" value={generator.fuel_level_pct.toFixed(0)} unit="%" status={generator.fuel_status} />
        <StatTile icon={Leaf} label="Renewable" value={energy.renewable_contribution_pct.toFixed(0)} unit="%" />
        <StatTile icon={ThermometerSnowflake} label="Temp" value={weather.temperature_celsius?.toFixed(0) ?? "—"} unit="°C" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>24H Energy Trend</CardTitle>
            <span className="text-[10px] text-muted-2">demand vs. renewable generation</span>
          </CardHeader>
          <CardBody>
            <TimeSeriesChart
              data={history.points}
              series={[
                { key: "demand_kw", label: "Demand", color: "#f59e0b", unit: "kW" },
                { key: "solar_kw", label: "Solar", color: "#38bdf8", unit: "kW" },
                { key: "wind_kw", label: "Wind", color: "#22c55e", unit: "kW" },
              ]}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Energy Flow</CardTitle>
          </CardHeader>
          <CardBody>
            <EnergyFlowDiagram
              data={{
                solarKw: energy.solar_kw,
                windKw: energy.wind_kw,
                generatorKw: energy.generator_output_kw,
                batteryPowerKw: battery.power_kw,
                loads: loadTiers,
              }}
            />
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Alerts</CardTitle>
            <span className="text-[10px] text-muted-2">{alerts.length} unresolved</span>
          </CardHeader>
          <CardBody className="max-h-72 space-y-2 overflow-y-auto">
            {alerts.length === 0 && <p className="py-6 text-center text-xs text-muted">No active alerts. All systems nominal.</p>}
            {alerts.map((a) => (
              <div key={a.id} className="rounded-md border border-border bg-surface-raised p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                    <ShieldAlert className="h-3.5 w-3.5 text-status-warning" />
                    {a.affected_system}
                  </span>
                  <StatusBadge status={a.severity} />
                </div>
                <p className="mt-1 text-xs text-muted">{a.message}</p>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI Recommendations</CardTitle>
            <span className="text-[10px] text-muted-2">explainable · rule-based engine</span>
          </CardHeader>
          <CardBody className="max-h-72 space-y-2 overflow-y-auto">
            {recs.recommendations.map((r, i) => (
              <div key={i} className="rounded-md border border-border bg-surface-raised p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-foreground">{r.recommendation}</span>
                  <PriorityBadge priority={r.priority} />
                </div>
                <p className="mt-1 text-[11px] text-muted">
                  <span className="text-muted-2">Why: </span>
                  {r.reason}
                </p>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
