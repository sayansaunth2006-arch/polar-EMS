"use client";

import { Sun, Wind, Fuel, BatteryCharging, ArrowDown, ArrowUp } from "lucide-react";
import { cn, formatKw } from "@/lib/utils";

interface FlowNodeProps {
  icon: React.ReactNode;
  label: string;
  valueKw: number;
  active: boolean;
  tone?: "source" | "bus" | "load";
}

function FlowNode({ icon, label, valueKw, active, tone = "source" }: FlowNodeProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-1 rounded-lg border px-3 py-2.5 text-center",
        tone === "bus" ? "border-accent/40 bg-accent/5" : "border-border bg-surface-raised",
        !active && "opacity-50"
      )}
    >
      <div className={cn("text-muted", tone === "bus" && "text-accent")}>{icon}</div>
      <span className="text-[11px] text-muted">{label}</span>
      <span className="font-data text-sm font-semibold text-foreground">
        {formatKw(valueKw)} <span className="text-[10px] text-muted">kW</span>
      </span>
    </div>
  );
}

function FlowArrow({ active, direction = "down" }: { active: boolean; direction?: "down" | "up" | "both" }) {
  return (
    <div className="flex flex-col items-center justify-center py-0.5">
      <div className={cn("h-4 w-px", active ? "bg-accent" : "bg-border-strong")} />
      {direction !== "up" && <ArrowDown className={cn("h-3 w-3 -mt-1", active ? "text-accent animate-pulse-dot" : "text-border-strong")} />}
      {direction === "up" && <ArrowUp className={cn("h-3 w-3 -mt-1", active ? "text-accent animate-pulse-dot" : "text-border-strong")} />}
    </div>
  );
}

export interface EnergyFlowData {
  solarKw: number;
  windKw: number;
  generatorKw: number;
  batteryPowerKw: number; // + charging, - discharging
  loads: { label: string; kw: number }[];
}

export function EnergyFlowDiagram({ data }: { data: EnergyFlowData }) {
  const renewableKw = data.solarKw + data.windKw;
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="grid w-full grid-cols-3 gap-3">
        <FlowNode icon={<Sun className="h-4 w-4" />} label="Solar" valueKw={data.solarKw} active={data.solarKw > 0.5} />
        <FlowNode icon={<Wind className="h-4 w-4" />} label="Wind" valueKw={data.windKw} active={data.windKw > 0.5} />
        <FlowNode icon={<Fuel className="h-4 w-4" />} label="Generator" valueKw={data.generatorKw} active={data.generatorKw > 0.5} />
      </div>

      <FlowArrow active={renewableKw + data.generatorKw > 0.5} />

      <div className="flex w-full items-stretch gap-3">
        <div className="flex-1">
          <FlowNode icon={<div className="h-4 w-4 rounded-full border-2 border-current" />} label="ENERGY BUS" valueKw={renewableKw + data.generatorKw} active tone="bus" />
        </div>
        <div className="flex flex-col items-center justify-center">
          <FlowArrow active={Math.abs(data.batteryPowerKw) > 0.5} direction={data.batteryPowerKw >= 0 ? "down" : "up"} />
        </div>
        <div className="flex-1">
          <FlowNode
            icon={<BatteryCharging className="h-4 w-4" />}
            label={data.batteryPowerKw >= 0 ? "Battery (charging)" : "Battery (discharging)"}
            valueKw={Math.abs(data.batteryPowerKw)}
            active={Math.abs(data.batteryPowerKw) > 0.5}
          />
        </div>
      </div>

      <FlowArrow active />

      <div className="grid w-full grid-cols-2 gap-2 sm:grid-cols-4">
        {data.loads.map((ld) => (
          <FlowNode key={ld.label} icon={<div className="h-2 w-2 rounded-full bg-current" />} label={ld.label} valueKw={ld.kw} active={ld.kw > 0.5} tone="load" />
        ))}
      </div>
    </div>
  );
}
