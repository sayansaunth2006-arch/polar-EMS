"use client";

import { useState } from "react";
import { FileText, Printer, RefreshCw } from "lucide-react";
import { api, type ReportData } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/utils";
import { toast } from "@/lib/toast";

export default function ReportsPage() {
  const [range, setRange] = useState("30d");
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    try {
      const res = await api.reportsGenerate(range);
      setReport(res);
    } catch {
      toast.error("Failed to generate report.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2 print:hidden">
        <div>
          <h1 className="text-base font-semibold text-foreground">Reports</h1>
          <p className="text-xs text-muted">Generate a station energy report for the selected period.</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={range} onChange={(e) => setRange(e.target.value)} className="rounded-md border border-border-strong bg-surface px-2 py-1.5 text-xs text-foreground">
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="24h">Last 24 hours</option>
          </select>
          <Button variant="primary" onClick={generate} disabled={loading}>
            <RefreshCw className="h-4 w-4" />
            {loading ? "Generating…" : "Generate Report"}
          </Button>
          {report && (
            <Button variant="secondary" onClick={() => window.print()}>
              <Printer className="h-4 w-4" /> Print
            </Button>
          )}
        </div>
      </div>

      {loading && <LoadingState label="Compiling report…" />}

      {!loading && !report && (
        <Card>
          <CardBody className="flex flex-col items-center gap-2 py-12 text-center text-muted">
            <FileText className="h-6 w-6" />
            <p className="text-sm">No report generated yet. Choose a period and click Generate Report.</p>
          </CardBody>
        </Card>
      )}

      {!loading && report && (
        <div id="report-content" className="space-y-4 rounded-lg border border-border bg-surface p-6 print:border-0 print:bg-white print:text-black">
          <div className="border-b border-border pb-3 print:border-black">
            <h2 className="text-lg font-semibold text-foreground print:text-black">POLAR-EMS Energy Report</h2>
            <p className="text-xs text-muted print:text-black">
              Period: {formatDateTime(report.period_start)} — {formatDateTime(report.period_end)} · Generated {formatDateTime(report.generated_at)}
            </p>
            <p className="mt-1 text-[11px] text-status-warning print:text-black">Based on synthetic/demo station data — prototype output.</p>
          </div>

          <table className="w-full text-sm">
            <tbody className="divide-y divide-border print:divide-black">
              {[
                ["Energy Consumption", `${report.energy_consumption_kwh.toFixed(0)} kWh`],
                ["Renewable Generation", `${report.renewable_generation_kwh.toFixed(0)} kWh`],
                ["Renewable Contribution", `${report.renewable_contribution_pct.toFixed(1)}%`],
                ["Diesel Consumption", `${report.diesel_consumption_l.toFixed(0)} L`],
                ["CO₂ Emissions", `${report.co2_emissions_kg.toFixed(0)} kg`],
                ["Average Battery SOC", `${report.average_battery_soc_pct.toFixed(0)}%`],
                ["Anomalies Detected", String(report.anomaly_count)],
                ["Estimated Fuel Saved (AI optimization)", `${report.estimated_fuel_saved_l.toFixed(0)} L`],
              ].map(([label, value]) => (
                <tr key={label}>
                  <td className="py-1.5 text-muted print:text-black">{label}</td>
                  <td className="py-1.5 text-right font-data font-semibold text-foreground print:text-black">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="text-[11px] text-muted-2 print:text-black">{report.estimated_savings_note}</p>
        </div>
      )}
    </div>
  );
}
