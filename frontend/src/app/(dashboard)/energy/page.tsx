"use client";

import { useState } from "react";
import { Zap, Sun, Wind, Fuel, Leaf } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { EnergyFlowDiagram } from "@/components/dashboard/EnergyFlowDiagram";
import { cn } from "@/lib/utils";

const RANGES = [
  { label: "6H", hours: 6 },
  { label: "24H", hours: 24 },
  { label: "7D", hours: 24 * 7 },
  { label: "30D", hours: 24 * 30 },
];

export default function EnergyMonitoringPage() {
  const [hours, setHours] = useState(24);

  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [current, history, battery, loads] = await Promise.all([
        api.energyCurrent(),
        api.energyHistory(hours),
        api.batteryStatus(),
        api.loadsList(),
      ]);
      return { current, history, battery, loads };
    },
    [hours],
    { pollMs: 30000 }
  );

  if (loading && !data) return <LoadingState label="Loading energy monitoring data…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { current, history, battery, loads } = data;
  const loadTiers = [
    { label: "Critical", kw: loads.filter((l) => l.priority === 1).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Important", kw: loads.filter((l) => l.priority === 2).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Deferrable", kw: loads.filter((l) => l.priority === 3).reduce((s, l) => s + l.current_power_kw, 0) },
    { label: "Non-Critical", kw: loads.filter((l) => l.priority === 4).reduce((s, l) => s + l.current_power_kw, 0) },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-base font-semibold text-foreground">Energy Monitoring</h1>
        <div className="flex gap-1 rounded-md border border-border bg-surface p-1">
          {RANGES.map((r) => (
            <button
              key={r.hours}
              onClick={() => setHours(r.hours)}
              className={cn(
                "rounded px-2.5 py-1 text-xs",
                hours === r.hours ? "bg-accent text-[#04141d] font-semibold" : "text-muted hover:text-foreground"
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatTile icon={Zap} label="Total Generation" value={current.total_generation_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Sun} label="Solar" value={current.solar_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Wind} label="Wind" value={current.wind_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Fuel} label="Generator" value={current.generator_output_kw.toFixed(0)} unit="kW" />
        <StatTile icon={Leaf} label="Renewable Share" value={current.renewable_contribution_pct.toFixed(0)} unit="%" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Demand vs. Generation ({hours}h)</CardTitle>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart
            height={300}
            data={history.points}
            series={[
              { key: "demand_kw", label: "Demand", color: "#f59e0b", unit: "kW" },
              { key: "solar_kw", label: "Solar", color: "#38bdf8", unit: "kW" },
              { key: "wind_kw", label: "Wind", color: "#22c55e", unit: "kW" },
            ]}
            areaMode
          />
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Temperature ({hours}h)</CardTitle>
          </CardHeader>
          <CardBody>
            <TimeSeriesChart data={history.points} series={[{ key: "temperature_celsius", label: "Temperature", color: "#a78bfa", unit: "°C" }]} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Energy Flow (live)</CardTitle>
          </CardHeader>
          <CardBody>
            <EnergyFlowDiagram
              data={{
                solarKw: current.solar_kw,
                windKw: current.wind_kw,
                generatorKw: current.generator_output_kw,
                batteryPowerKw: battery.power_kw,
                loads: loadTiers,
              }}
            />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
