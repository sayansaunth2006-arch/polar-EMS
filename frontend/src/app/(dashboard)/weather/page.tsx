"use client";

import { CloudSnow, Wind, Sun, Eye, ThermometerSnowflake, CloudCog } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";

export default function WeatherPage() {
  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [current, history] = await Promise.all([api.weatherCurrent(), api.weatherHistory(72)]);
      return { current, history };
    },
    [],
    { pollMs: 60000 }
  );

  if (loading && !data) return <LoadingState label="Loading environmental data…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { current, history } = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">Polar Weather</h1>
          <p className="text-xs text-muted">
            Source: {current.source === "synthetic" ? "synthetic simulator (no live weather API configured)" : "live weather API"}
          </p>
        </div>
        <span className="rounded-md border border-border bg-surface-raised px-3 py-1.5 text-sm capitalize text-foreground">
          {current.condition?.replace(/_/g, " ") ?? "unknown"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatTile icon={ThermometerSnowflake} label="Temperature" value={current.temperature_celsius?.toFixed(1) ?? "—"} unit="°C" />
        <StatTile icon={Wind} label="Wind Speed" value={current.wind_speed_mps?.toFixed(1) ?? "—"} unit="m/s" />
        <StatTile icon={Sun} label="Solar Irradiance" value={current.solar_irradiance_w_m2?.toFixed(0) ?? "—"} unit="W/m²" />
        <StatTile icon={CloudCog} label="Cloud Cover" value={current.cloud_cover_pct?.toFixed(0) ?? "—"} unit="%" />
        <StatTile icon={Eye} label="Visibility" value={current.visibility_km?.toFixed(1) ?? "—"} unit="km" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Temperature & Wind (72h)</CardTitle>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart
            data={history.points}
            series={[
              { key: "temperature_celsius", label: "Temperature", color: "#a78bfa", unit: "°C" },
              { key: "wind_speed_mps", label: "Wind Speed", color: "#22c55e", unit: "m/s" },
            ]}
            height={280}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Solar Irradiance & Cloud Cover (72h)</CardTitle>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart
            data={history.points}
            series={[
              { key: "solar_irradiance_w_m2", label: "Irradiance", color: "#f59e0b", unit: "W/m²" },
              { key: "cloud_cover_pct", label: "Cloud Cover", color: "#38bdf8", unit: "%" },
            ]}
            height={280}
            areaMode
          />
        </CardBody>
      </Card>

      <div className="flex items-center gap-2 rounded-md border border-border bg-surface p-3 text-xs text-muted">
        <CloudSnow className="h-4 w-4 shrink-0 text-accent" />
        This service is designed so a real weather provider can be plugged in later (set <code className="font-data text-accent">WEATHER_API_KEY</code>)
        without changing the response shape consumed here.
      </div>
    </div>
  );
}
