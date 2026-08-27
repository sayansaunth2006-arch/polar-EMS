"use client";

import { useAuthStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  timeoutMs?: number;
  authRequired?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, timeoutMs = 15000, authRequired = true } = options;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  if (authRequired) {
    const token = useAuthStore.getState().token;
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "Request timed out — the backend may be unreachable.");
    }
    throw new ApiError(0, "Unable to reach the POLAR-EMS backend. Is it running on " + API_BASE + "?");
  }
  clearTimeout(timeout);

  if (response.status === 401) {
    useAuthStore.getState().clearSession();
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // response body wasn't JSON — keep generic message
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  // --- auth ---
  login: (email: string, password: string) =>
    request<{ access_token: string; role: string; full_name: string }>("/auth/login", {
      method: "POST",
      body: { email, password },
      authRequired: false,
    }),
  me: () => request<{ id: number; email: string; full_name: string; role: string; station_id: number | null }>("/auth/me"),

  // --- energy ---
  energyCurrent: () => request<EnergyCurrent>("/energy/current"),
  energyHistory: (hours = 24) => request<{ points: EnergyHistoryPoint[] }>(`/energy/history?hours=${hours}`),

  // --- battery ---
  batteryStatus: () => request<BatteryStatus>("/battery/status"),
  batteryHistory: (hours = 24) => request<{ points: BatteryHistoryPoint[] }>(`/battery/history?hours=${hours}`),

  // --- generator ---
  generatorStatus: () => request<GeneratorStatus>("/generator/status"),
  generatorHistory: (hours = 24) => request<{ total_fuel_consumed_l: number; total_co2_kg: number; points: GeneratorHistoryPoint[] }>(`/generator/history?hours=${hours}`),
  generatorComparison: () => request<BaselineComparison>("/generator/comparison"),

  // --- loads ---
  loadsList: () => request<LoadItem[]>("/loads/"),
  updateLoadPriority: (id: number, priority: number) => request(`/loads/${id}`, { method: "PATCH", body: { priority } }),

  // --- weather ---
  weatherCurrent: () => request<WeatherCurrent>("/weather/current"),
  weatherHistory: (hours = 24) => request<{ points: WeatherPoint[] }>(`/weather/history?hours=${hours}`),

  // --- forecast ---
  forecastDemand: () => request<DemandForecastResponse>("/forecast/demand"),
  forecastRenewable: () => request<RenewableForecastResponse>("/forecast/renewable"),

  // --- anomaly ---
  anomalyScan: () => request<{ scanned_findings: number; new_anomalies_saved: number }>("/anomaly/scan", { method: "POST" }),
  anomalyList: (resolved?: boolean) => request<AnomalyItem[]>(`/anomaly/${resolved !== undefined ? `?resolved=${resolved}` : ""}`),
  anomalyResolve: (id: number) => request(`/anomaly/${id}/resolve`, { method: "POST" }),

  // --- optimization ---
  optimizationRecommendations: () => request<RecommendationsResponse>("/optimization/recommendations"),
  optimizationBaselineComparison: () => request<BaselineComparison>("/optimization/baseline-comparison"),

  // --- alerts ---
  alertsGenerate: () => request<{ alerts_created: number }>("/alerts/generate", { method: "POST" }),
  alertsList: (resolved?: boolean) => request<AlertItem[]>(`/alerts/${resolved !== undefined ? `?resolved=${resolved}` : ""}`),
  alertResolve: (id: number) => request(`/alerts/${id}/resolve`, { method: "POST" }),

  // --- simulation ---
  simulationScenarios: () => request<ScenarioItem[]>("/simulation/scenarios"),
  simulationRun: (key: string) => request<SimulationOutcome>(`/simulation/run/${key}`, { method: "POST" }),
  whatIf: (modifiers: Record<string, unknown>) => request<SimulationOutcome>("/simulation/what-if", { method: "POST", body: modifiers }),

  // --- analytics ---
  analyticsSummary: (range = "7d") => request<AnalyticsSummary>(`/analytics/summary?range=${range}`),

  // --- reports ---
  reportsGenerate: (range = "30d") => request<ReportData>(`/reports/generate?range=${range}`),
  reportsList: () => request<{ id: number; generated_at: string; period_start: string; period_end: string; summary: ReportData }[]>("/reports/"),

  // --- stations ---
  stations: () => request<{ id: number; name: string; location: string; is_synthetic_demo: boolean }[]>("/stations/"),
};

// ---------------- Types (mirroring backend response shapes) ----------------

export interface EnergyCurrent {
  station_id: number;
  is_synthetic: boolean;
  timestamp: string;
  demand_kw: number;
  total_generation_kw: number;
  solar_kw: number;
  wind_kw: number;
  generator_output_kw: number;
  renewable_contribution_pct: number;
  battery_soc_pct: number;
  fuel_pct: number;
}

export interface EnergyHistoryPoint {
  timestamp: string;
  demand_kw: number;
  solar_kw: number;
  wind_kw: number;
  temperature_celsius: number | null;
}

export interface BatteryStatus {
  battery_id: number;
  name: string;
  capacity_kwh: number;
  soc_pct: number;
  status: "NORMAL" | "WARNING" | "CRITICAL";
  voltage_v: number | null;
  current_a: number | null;
  temperature_celsius: number | null;
  temperature_status: string;
  power_kw: number;
  charge_rate_kw: number;
  discharge_rate_kw: number;
  health_pct: number;
  cycle_count: number;
  min_soc_pct: number;
  max_soc_pct: number;
  estimated_runtime_hours: number | null;
  is_synthetic: boolean;
}

export interface BatteryHistoryPoint {
  timestamp: string;
  soc_pct: number;
  power_kw: number;
  temperature_celsius: number;
}

export interface GeneratorStatus {
  generator_id: number;
  name: string;
  status: string;
  output_kw: number;
  rated_capacity_kw: number;
  fuel_level_pct: number;
  fuel_status: "NORMAL" | "WARNING" | "CRITICAL";
  fuel_tank_capacity_l: number;
  fuel_consumption_l_per_kwh: number;
  co2_kg_per_l: number;
  runtime_hours: number;
  maintenance_status: string;
  is_synthetic: boolean;
}

export interface GeneratorHistoryPoint {
  timestamp: string;
  output_kw: number;
  fuel_level_pct: number;
  status: string;
}

export interface LoadItem {
  id: number;
  name: string;
  category: string;
  priority: number;
  priority_label: string;
  rated_power_kw: number;
  current_power_kw: number;
  is_deferrable: boolean;
  is_shed: boolean;
}

export interface WeatherCurrent {
  source: string;
  available: boolean;
  timestamp?: string;
  temperature_celsius?: number;
  wind_speed_mps?: number;
  solar_irradiance_w_m2?: number;
  cloud_cover_pct?: number;
  visibility_km?: number;
  condition?: string;
}

export interface WeatherPoint {
  timestamp: string;
  temperature_celsius: number;
  wind_speed_mps: number;
  solar_irradiance_w_m2: number;
  cloud_cover_pct: number;
  condition: string;
}

export interface ForecastMetrics {
  mae_kw: number;
  rmse_kw: number;
  r2: number;
  n_train: number;
  n_test: number;
}

export interface DemandForecastResponse {
  available: boolean;
  reason?: string;
  model_type?: string;
  is_synthetic_training_data?: boolean;
  forecasts: { horizon_hours: number; predicted_demand_kw: number; confidence: number; model_name: string; metrics: ForecastMetrics }[];
  recent_actual: { timestamp: string; demand_kw: number }[];
}

export interface RenewableForecastResponse {
  available: boolean;
  is_synthetic_training_data: boolean;
  solar: { horizon_hours: number; predicted_kw: number; confidence: number; metrics: ForecastMetrics }[];
  wind: { horizon_hours: number; predicted_kw: number; confidence: number; metrics: ForecastMetrics }[];
  energy_condition_6h: "surplus" | "balanced" | "deficit";
}

export interface AnomalyItem {
  id: number;
  timestamp: string;
  severity: "info" | "warning" | "critical";
  affected_asset: string;
  metric: string;
  observed_value: number;
  expected_value: number;
  deviation_pct: number;
  explanation: string;
  is_resolved: boolean;
}

export interface Recommendation {
  action_type: string;
  recommendation: string;
  reason: string;
  expected_benefit: string;
  priority: "low" | "medium" | "high" | "critical";
  kind: string;
}

export interface RecommendationsResponse {
  station_id: number;
  battery_status: string;
  fuel_status: string;
  recommendations: Recommendation[];
}

export interface BaselineComparison {
  baseline_fuel_l: number;
  optimized_fuel_l: number;
  baseline_co2_kg: number;
  optimized_co2_kg: number;
  baseline_renewable_utilization_pct: number;
  optimized_renewable_utilization_pct: number;
  estimated_fuel_saved_l: number;
  estimated_co2_saved_kg: number;
  note?: string;
}

export interface AlertItem {
  id: number;
  timestamp: string;
  severity: "info" | "warning" | "critical";
  affected_system: string;
  message: string;
  explanation: string;
  recommended_action: string;
  is_resolved: boolean;
}

export interface ScenarioItem {
  key: string;
  name: string;
  description: string;
  modifiers: Record<string, unknown>;
}

export interface SimulationOutcome {
  scenario?: { key: string; name: string; description: string };
  modifiers_applied?: Record<string, unknown>;
  baseline: { demand_kw: number; solar_kw: number; wind_kw: number; battery_soc_pct: number; generator_output_kw: number; fuel_pct: number };
  result: {
    demand_kw: number;
    solar_kw: number;
    wind_kw: number;
    battery_soc_pct: number;
    generator_output_kw: number;
    fuel_pct: number;
    battery_status: string;
    fuel_status: string;
  };
  recommendations: Recommendation[];
  comparison: BaselineComparison;
  safety_notes: string[];
}

export interface AnalyticsSummary {
  range: string;
  period_start: string;
  period_end: string;
  is_synthetic: boolean;
  totals: {
    total_demand_kwh: number;
    total_solar_kwh: number;
    total_wind_kwh: number;
    total_renewable_kwh: number;
    renewable_contribution_pct: number;
    total_diesel_l: number;
    total_co2_kg: number;
    average_battery_soc_pct: number;
    anomaly_count: number;
    efficiency_kwh_per_l: number | null;
  };
  daily: { date: string; demand_kwh: number; solar_kwh: number; wind_kwh: number; fuel_l: number; co2_kg: number }[];
}

export interface ReportData {
  station_id: number;
  generated_at: string;
  period_start: string;
  period_end: string;
  is_synthetic: boolean;
  energy_consumption_kwh: number;
  renewable_generation_kwh: number;
  renewable_contribution_pct: number;
  diesel_consumption_l: number;
  co2_emissions_kg: number;
  average_battery_soc_pct: number;
  anomaly_count: number;
  estimated_fuel_saved_l: number;
  estimated_savings_note: string;
  daily_breakdown: AnalyticsSummary["daily"];
}
