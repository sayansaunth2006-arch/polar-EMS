"use client";

import { useState } from "react";
import { BarChart3, Leaf, Fuel, Gauge, AlertTriangle } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { cn, formatDateTime } from "@/lib/utils";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const RANGES = [
  { label: "24H", key: "24h" },
  { label: "7D", key: "7d" },
  { label: "30D", key: "30d" },
];

export default function AnalyticsPage() {
  const [range, setRange] = useState("7d");
  const { data, loading, error, refetch } = useApiQuery(() => api.analyticsSummary(range), [range]);

  if (loading && !data) return <LoadingState label="Crunching analytics…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { totals, daily } = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-base font-semibold text-foreground">Historical Analytics</h1>
          <p className="text-xs text-muted">
            {formatDateTime(data.period_start)} — {formatDateTime(data.period_end)} · synthetic data
          </p>
        </div>
        <div className="flex gap-1 rounded-md border border-border bg-surface p-1">
          {RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRange(r.key)}
              className={cn("rounded px-2.5 py-1 text-xs", range === r.key ? "bg-accent text-[#04141d] font-semibold" : "text-muted hover:text-foreground")}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
        <StatTile icon={Gauge} label="Total Demand" value={totals.total_demand_kwh.toFixed(0)} unit="kWh" />
        <StatTile icon={Leaf} label="Renewable Share" value={totals.renewable_contribution_pct.toFixed(0)} unit="%" />
        <StatTile icon={Fuel} label="Diesel Used" value={totals.total_diesel_l.toFixed(0)} unit="L" />
        <StatTile icon={BarChart3} label="CO₂ Emissions" value={totals.total_co2_kg.toFixed(0)} unit="kg" />
        <StatTile icon={Gauge} label="Avg Battery SOC" value={totals.average_battery_soc_pct.toFixed(0)} unit="%" />
        <StatTile icon={AlertTriangle} label="Anomalies" value={String(totals.anomaly_count)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Daily Consumption vs. Renewable Generation</CardTitle>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={daily} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="#23303f" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" stroke="#5b6b7f" tick={{ fontSize: 10 }} minTickGap={20} />
              <YAxis stroke="#5b6b7f" tick={{ fontSize: 11 }} width={40} />
              <Tooltip
                contentStyle={{ background: "#151d29", border: "1px solid #34445a", borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: "#8695a7" }}
                formatter={(value) => (typeof value === "number" ? value.toFixed(1) : value)}
              />
              <Bar dataKey="demand_kwh" name="Demand (kWh)" fill="#f59e0b" radius={[2, 2, 0, 0]} />
              <Bar dataKey="solar_kwh" name="Solar (kWh)" fill="#38bdf8" radius={[2, 2, 0, 0]} />
              <Bar dataKey="wind_kwh" name="Wind (kWh)" fill="#22c55e" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fuel Consumption & CO₂ Emissions</CardTitle>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={daily} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="#23303f" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" stroke="#5b6b7f" tick={{ fontSize: 10 }} minTickGap={20} />
              <YAxis stroke="#5b6b7f" tick={{ fontSize: 11 }} width={40} />
              <Tooltip
                contentStyle={{ background: "#151d29", border: "1px solid #34445a", borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: "#8695a7" }}
                formatter={(value) => (typeof value === "number" ? value.toFixed(1) : value)}
              />
              <Bar dataKey="fuel_l" name="Fuel (L)" fill="#ef4444" radius={[2, 2, 0, 0]} />
              <Bar dataKey="co2_kg" name="CO₂ (kg)" fill="#8695a7" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </div>
  );
}
