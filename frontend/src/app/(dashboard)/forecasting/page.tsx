"use client";

import { Brain, Gauge, Target } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { TimeSeriesChart } from "@/components/charts/TimeSeriesChart";
import { StatusBadge } from "@/components/ui/StatusBadge";

const CONDITION_STATUS: Record<string, "NORMAL" | "WARNING" | "CRITICAL"> = { surplus: "NORMAL", balanced: "WARNING", deficit: "CRITICAL" };

export default function ForecastingPage() {
  const { data, loading, error, refetch } = useApiQuery(
    async () => {
      const [demand, renewable] = await Promise.all([api.forecastDemand(), api.forecastRenewable()]);
      return { demand, renewable };
    },
    [],
    { pollMs: 60000 }
  );

  if (loading && !data) return <LoadingState label="Training / loading forecasting models…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { demand, renewable } = data;

  if (!demand.available) {
    return <ErrorState message={demand.reason ?? "Forecasting unavailable."} />;
  }

  const actualChartData = demand.recent_actual.map((p) => ({ timestamp: p.timestamp, demand_kw: p.demand_kw }));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-base font-semibold text-foreground">AI Energy Demand Forecasting</h1>
          <p className="text-xs text-muted">
            Model: {demand.model_type} · trained on synthetic historical data · predictions are model outputs, not measured values
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {demand.forecasts.map((f) => (
          <Card key={f.horizon_hours}>
            <CardHeader>
              <CardTitle>+{f.horizon_hours}H Demand Forecast</CardTitle>
              <Brain className="h-4 w-4 text-accent" />
            </CardHeader>
            <CardBody>
              <div className="flex items-baseline gap-1">
                <span className="font-data text-2xl font-semibold text-foreground">{f.predicted_demand_kw.toFixed(1)}</span>
                <span className="text-xs text-muted">kW predicted</span>
              </div>
              <p className="mt-1 text-[11px] text-muted">Confidence: {(f.confidence * 100).toFixed(0)}%</p>
              <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border pt-2 text-center">
                <div>
                  <p className="font-data text-xs text-foreground">{f.metrics.mae_kw}</p>
                  <p className="text-[10px] text-muted-2">MAE (kW)</p>
                </div>
                <div>
                  <p className="font-data text-xs text-foreground">{f.metrics.rmse_kw}</p>
                  <p className="text-[10px] text-muted-2">RMSE (kW)</p>
                </div>
                <div>
                  <p className="font-data text-xs text-foreground">{f.metrics.r2}</p>
                  <p className="text-[10px] text-muted-2">R²</p>
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actual Demand (recent 48h)</CardTitle>
          <span className="text-[10px] text-muted-2">synthetic historical data</span>
        </CardHeader>
        <CardBody>
          <TimeSeriesChart data={actualChartData} series={[{ key: "demand_kw", label: "Actual Demand", color: "#f59e0b", unit: "kW" }]} height={260} />
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Solar Forecast</CardTitle>
            <Target className="h-4 w-4 text-status-info" />
          </CardHeader>
          <CardBody className="space-y-2">
            {renewable.solar.map((f) => (
              <div key={f.horizon_hours} className="flex items-center justify-between rounded-md border border-border bg-surface-raised px-3 py-2">
                <span className="text-xs text-muted">+{f.horizon_hours}h</span>
                <span className="font-data text-sm text-foreground">{f.predicted_kw.toFixed(1)} kW</span>
                <span className="text-[11px] text-muted-2">R² {f.metrics.r2}</span>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Wind Forecast</CardTitle>
            <Gauge className="h-4 w-4 text-status-info" />
          </CardHeader>
          <CardBody className="space-y-2">
            {renewable.wind.map((f) => (
              <div key={f.horizon_hours} className="flex items-center justify-between rounded-md border border-border bg-surface-raised px-3 py-2">
                <span className="text-xs text-muted">+{f.horizon_hours}h</span>
                <span className="font-data text-sm text-foreground">{f.predicted_kw.toFixed(1)} kW</span>
                <span className="text-[11px] text-muted-2">R² {f.metrics.r2}</span>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Forecast Energy Condition (+6h)</p>
            <p className="text-xs text-muted">Classification of predicted renewable supply vs. demand, accounting for battery reserve.</p>
          </div>
          <StatusBadge status={CONDITION_STATUS[renewable.energy_condition_6h]} />
        </CardBody>
      </Card>
    </div>
  );
}
