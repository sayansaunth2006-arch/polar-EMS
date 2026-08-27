"use client";

import { useState } from "react";
import { GitCompareArrows, Play } from "lucide-react";
import { api, type SimulationOutcome } from "@/lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PriorityBadge, StatusBadge } from "@/components/ui/StatusBadge";
import { toast } from "@/lib/toast";
import { LoadingState } from "@/components/ui/States";

function Slider({ label, value, min, max, step, unit, onChange }: { label: string; value: number; min: number; max: number; step: number; unit: string; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted">{label}</span>
        <span className="font-data text-foreground">
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[var(--accent)]"
      />
    </div>
  );
}

export default function WhatIfPage() {
  const [temperatureDelta, setTemperatureDelta] = useState(0);
  const [demandMultiplier, setDemandMultiplier] = useState(1);
  const [solarMultiplier, setSolarMultiplier] = useState(1);
  const [windMultiplier, setWindMultiplier] = useState(1);
  const [batterySoc, setBatterySoc] = useState(50);
  const [generatorAvailable, setGeneratorAvailable] = useState(true);
  const [fuelPct, setFuelPct] = useState(70);

  const [outcome, setOutcome] = useState<SimulationOutcome | null>(null);
  const [running, setRunning] = useState(false);

  async function runWhatIf() {
    setRunning(true);
    try {
      const result = await api.whatIf({
        temperature_delta_c: temperatureDelta,
        demand_multiplier: demandMultiplier,
        solar_multiplier: solarMultiplier,
        wind_multiplier: windMultiplier,
        battery_soc_override_pct: batterySoc,
        generator_available: generatorAvailable,
        fuel_override_pct: fuelPct,
      });
      setOutcome(result);
    } catch {
      toast.error("What-if analysis failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-base font-semibold text-foreground">What-If Analysis</h1>
        <p className="text-xs text-muted">Adjust conditions below, then run the analysis to compare against the current baseline.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Scenario Inputs</CardTitle>
            <GitCompareArrows className="h-4 w-4 text-muted" />
          </CardHeader>
          <CardBody className="space-y-4">
            <Slider label="Temperature Δ" value={temperatureDelta} min={-30} max={15} step={1} unit="°C" onChange={setTemperatureDelta} />
            <Slider label="Demand Multiplier" value={demandMultiplier} min={0.5} max={2.5} step={0.1} unit="×" onChange={setDemandMultiplier} />
            <Slider label="Solar Multiplier" value={solarMultiplier} min={0} max={1.5} step={0.05} unit="×" onChange={setSolarMultiplier} />
            <Slider label="Wind Multiplier" value={windMultiplier} min={0} max={2} step={0.1} unit="×" onChange={setWindMultiplier} />
            <Slider label="Battery SOC" value={batterySoc} min={0} max={100} step={1} unit="%" onChange={setBatterySoc} />
            <Slider label="Fuel Level" value={fuelPct} min={0} max={100} step={1} unit="%" onChange={setFuelPct} />
            <label className="flex items-center gap-2 text-xs text-muted">
              <input type="checkbox" checked={generatorAvailable} onChange={(e) => setGeneratorAvailable(e.target.checked)} />
              Generator available
            </label>
            <Button variant="primary" onClick={runWhatIf} disabled={running} className="w-full">
              <Play className="h-4 w-4" />
              {running ? "Calculating…" : "Run What-If Analysis"}
            </Button>
          </CardBody>
        </Card>

        <div className="space-y-4 xl:col-span-2">
          {running && <LoadingState label="Recalculating station state…" />}

          {!running && outcome && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Baseline vs. What-If</CardTitle>
                  <div className="flex gap-2">
                    <StatusBadge status={outcome.result.battery_status} />
                    <StatusBadge status={outcome.result.fuel_status} />
                  </div>
                </CardHeader>
                <CardBody className="overflow-x-auto">
                  <table className="w-full min-w-[420px] text-xs">
                    <thead>
                      <tr className="text-left text-muted-2">
                        <th className="pb-2 font-medium">Metric</th>
                        <th className="pb-2 font-medium">Baseline</th>
                        <th className="pb-2 font-medium">What-If</th>
                      </tr>
                    </thead>
                    <tbody className="font-data text-foreground">
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">Demand</td>
                        <td>{outcome.baseline.demand_kw.toFixed(1)} kW</td>
                        <td className="text-accent">{outcome.result.demand_kw.toFixed(1)} kW</td>
                      </tr>
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">Solar + Wind</td>
                        <td>{(outcome.baseline.solar_kw + outcome.baseline.wind_kw).toFixed(1)} kW</td>
                        <td className="text-accent">{(outcome.result.solar_kw + outcome.result.wind_kw).toFixed(1)} kW</td>
                      </tr>
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">Battery SOC</td>
                        <td>{outcome.baseline.battery_soc_pct.toFixed(0)}%</td>
                        <td className="text-accent">{outcome.result.battery_soc_pct.toFixed(0)}%</td>
                      </tr>
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">Generator Output</td>
                        <td>{outcome.baseline.generator_output_kw.toFixed(1)} kW</td>
                        <td className="text-accent">{outcome.result.generator_output_kw.toFixed(1)} kW</td>
                      </tr>
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">Fuel Consumption (24h est.)</td>
                        <td>{outcome.comparison.baseline_fuel_l} L</td>
                        <td className="text-accent">{outcome.comparison.optimized_fuel_l} L</td>
                      </tr>
                      <tr className="border-t border-border">
                        <td className="py-1.5 text-muted">CO₂ Emissions (24h est.)</td>
                        <td>{outcome.comparison.baseline_co2_kg} kg</td>
                        <td className="text-accent">{outcome.comparison.optimized_co2_kg} kg</td>
                      </tr>
                    </tbody>
                  </table>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Resulting Recommendations</CardTitle>
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
            </>
          )}

          {!running && !outcome && (
            <Card>
              <CardBody className="py-12 text-center text-sm text-muted">Adjust the inputs and run the analysis to see results here.</CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
