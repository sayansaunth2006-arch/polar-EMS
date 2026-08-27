"use client";

import { BatteryCharging, Thermometer, Zap, Activity, Clock, Heart } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

export default function BatteryPage() {
  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [status, history] = await Promise.all([api.batteryStatus(), api.batteryHistory(48)]);
      return { status, history };
    },
    [],
    { pollMs: 20000 }
  );

  if (loading && !data) return <LoadingState label="Loading battery telemetry…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { status, history } = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Battery Management — {status.name}</h1>
          <p className="text-xs text-muted">{status.capacity_kwh} kWh capacity · synthetic telemetry</p>
        </div>
        <StatusBadge status={status.status} pulse />
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        <StatTile icon={BatteryCharging} label="State of Charge" value={status.soc_pct.toFixed(0)} unit="%" status={status.status} />
        <StatTile icon={Zap} label="Power" value={status.power_kw.toFixed(1)} unit="kW" hint={status.power_kw >= 0 ? "charging" : "discharging"} />
        <StatTile icon={Activity} label="Voltage" value={status.voltage_v?.toFixed(1) ?? "—"} unit="V" />
        <StatTile icon={Activity} label="Current" value={status.current_a?.toFixed(1) ?? "—"} unit="A" />
        <StatTile icon={Thermometer} label="Temperature" value={status.temperature_celsius?.toFixed(1) ?? "—"} unit="°C" status={status.temperature_status as "NORMAL" | "CRITICAL"} />
        <StatTile icon={Heart} label="Health" value={status.health_pct.toFixed(0)} unit="%" hint={`${status.cycle_count} cycles`} />
        <StatTile icon={Clock} label="Est. Runtime" value={status.estimated_runtime_hours?.toFixed(1) ?? "—"} unit="h" hint={status.power_kw < 0 ? "at current discharge" : "not discharging"} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>SOC & Power History (48h)</CardTitle>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart
            data={history.points}
            series={[
              { key: "soc_pct", label: "SOC", color: "#38bdf8", unit: "%" },
              { key: "power_kw", label: "Power", color: "#f59e0b", unit: "kW" },
            ]}
            height={280}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Safety Thresholds</CardTitle>
          <span className="text-[10px] text-muted-2">centrally configured — never hard-coded per view</span>
        </CardHeader>
        <CardBody className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="font-data text-lg text-status-critical">{status.min_soc_pct}%</p>
            <p className="text-[11px] text-muted">Minimum reserve (hard floor)</p>
          </div>
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="font-data text-lg text-status-normal">{status.max_soc_pct}%</p>
            <p className="text-[11px] text-muted">Maximum SOC</p>
          </div>
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="font-data text-lg text-foreground">{status.health_pct}%</p>
            <p className="text-[11px] text-muted">Battery health</p>
          </div>
          <div className="rounded-md border border-border bg-surface-raised p-3 text-center">
            <p className="font-data text-lg text-foreground">{status.cycle_count}</p>
            <p className="text-[11px] text-muted">Charge cycles</p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
