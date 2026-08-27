"use client";

import { Settings as SettingsIcon, User, Radio, ShieldCheck, Info } from "lucide-react";
import { useApiQuery } from "@/hooks/useApiQuery";
import { api } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { useAuthStore } from "@/lib/store";

const ROLE_LABEL: Record<string, string> = {
  operator: "Station Energy Operator",
  administrator: "Station Administrator",
  scientist: "Research Scientist",
};

export default function SettingsPage() {
  const { fullName, email, role } = useAuthStore();

  const { data, loading, error, refetch } = useApiQuery(async () => {
    const [stations, battery, generator] = await Promise.all([api.stations(), api.batteryStatus(), api.generatorStatus()]);
    return { stations, battery, generator };
  }, []);

  if (loading && !data) return <LoadingState label="Loading settings…" />;
  if (error && !data) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const station = data.stations[0];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <SettingsIcon className="h-5 w-5 text-muted" />
        <h1 className="text-base font-semibold text-foreground">Settings</h1>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <User className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Name</span>
              <span className="text-foreground">{fullName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Email</span>
              <span className="font-data text-foreground">{email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Role</span>
              <span className="text-foreground">{role ? ROLE_LABEL[role] : "—"}</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Station</CardTitle>
            <Radio className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Name</span>
              <span className="text-foreground">{station?.name ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Location</span>
              <span className="text-foreground">{station?.location ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Data source</span>
              <span className="text-status-warning">{station?.is_synthetic_demo ? "Synthetic / demo" : "Live"}</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Battery Safety Thresholds</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Minimum reserve (hard floor)</span>
              <span className="font-data text-foreground">{data.battery.min_soc_pct}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Maximum SOC</span>
              <span className="font-data text-foreground">{data.battery.max_soc_pct}%</span>
            </div>
            <p className="pt-2 text-[11px] text-muted-2">
              These limits are centrally configured on the backend (app/core/config.py) and enforced by the deterministic safety layer — the AI
              optimization engine can never override them.
            </p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generator Configuration</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Rated capacity</span>
              <span className="font-data text-foreground">{data.generator.rated_capacity_kw} kW</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Fuel consumption rate</span>
              <span className="font-data text-foreground">{data.generator.fuel_consumption_l_per_kwh} L/kWh</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">CO₂ factor</span>
              <span className="font-data text-foreground">{data.generator.co2_kg_per_l} kg/L</span>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody className="flex items-start gap-2 text-xs text-muted">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <p>
            POLAR-EMS prototype build. All energy readings, weather, and forecasts on this instance are synthetic demonstration data generated for the
            Smart India Hackathon prototype — see the README for details on connecting real sensors, a live weather API, and a production database.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
