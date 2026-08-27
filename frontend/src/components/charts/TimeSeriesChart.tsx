"use client";

import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatTime } from "@/lib/utils";

export interface SeriesConfig {
  key: string;
  label: string;
  color: string;
  unit?: string;
  type?: "line" | "area";
}

const GRID_COLOR = "#23303f";
const AXIS_COLOR = "#5b6b7f";

interface TooltipPayloadEntry {
  dataKey: string;
  value: number | string;
  color: string;
}

function ChartTooltip({
  active,
  payload,
  label,
  series,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
  series: SeriesConfig[];
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border-strong bg-surface-raised px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 text-muted">{formatTime(label)}</p>
      {payload.map((p) => {
        const cfg = series.find((s) => s.key === p.dataKey);
        return (
          <div key={p.dataKey} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
            <span className="text-foreground">{cfg?.label ?? p.dataKey}:</span>
            <span className="font-data text-foreground">
              {typeof p.value === "number" ? p.value.toFixed(1) : p.value} {cfg?.unit ?? ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function TimeSeriesChart<T extends { timestamp: string }>({
  data,
  series,
  height = 240,
  areaMode = false,
}: {
  data: T[];
  series: SeriesConfig[];
  height?: number;
  areaMode?: boolean;
}) {
  const Chart = areaMode ? AreaChart : LineChart;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="timestamp" tickFormatter={formatTime} stroke={AXIS_COLOR} tick={{ fontSize: 11 }} minTickGap={40} />
        <YAxis stroke={AXIS_COLOR} tick={{ fontSize: 11 }} width={40} />
        <Tooltip content={<ChartTooltip series={series} />} />
        {series.map((s) =>
          areaMode ? (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              stroke={s.color}
              fill={s.color}
              fillOpacity={0.12}
              strokeWidth={1.75}
              dot={false}
              isAnimationActive={false}
            />
          ) : (
            <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} strokeWidth={1.75} dot={false} isAnimationActive={false} />
          )
        )}
      </Chart>
    </ResponsiveContainer>
  );
}
