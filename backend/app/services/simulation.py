"""Simulation-mode and what-if scenario engine.

Applies a set of modifiers to a baseline `StationState` snapshot and
recomputes everything downstream (safety-clamped state, recommendations,
baseline-vs-optimized comparison) so the effect of a scenario is visible
across the whole dashboard, not just one number.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass

from app.services.optimization import (
    BaselineComparison,
    Recommendation,
    StationState,
    apply_safety_constraints,
    compare_baseline_vs_optimized,
    generate_recommendations,
)
from app.services.safety import battery_status_from_soc, fuel_status_from_pct


@dataclass
class SimulationOutcome:
    state: StationState
    recommendations: list[Recommendation]
    comparison: BaselineComparison
    battery_status: str
    fuel_status: str
    safety_notes: list[str]

    def as_dict(self) -> dict:
        return {
            "state": asdict(self.state),
            "recommendations": [asdict(r) for r in self.recommendations],
            "comparison": asdict(self.comparison),
            "battery_status": self.battery_status,
            "fuel_status": self.fuel_status,
            "safety_notes": self.safety_notes,
        }


def apply_modifiers(base_state: StationState, modifiers: dict) -> StationState:
    """Apply a dict of scenario/what-if modifiers to a copy of the baseline state.

    Supported keys (all optional):
      temperature_delta_c, demand_multiplier, demand_override_kw,
      solar_multiplier, wind_multiplier,
      battery_soc_override_pct, battery_capacity_override_kwh,
      generator_available (bool), fuel_override_pct,
    """

    state = deepcopy(base_state)

    if "demand_override_kw" in modifiers:
        state.demand_kw = float(modifiers["demand_override_kw"])
        state.predicted_demand_kw = state.demand_kw
    if "demand_multiplier" in modifiers:
        state.demand_kw *= modifiers["demand_multiplier"]
        state.predicted_demand_kw *= modifiers["demand_multiplier"]
    if "temperature_delta_c" in modifiers:
        # Simplified: colder temperature increases heating-driven demand.
        heating_bump_kw = max(-modifiers["temperature_delta_c"], 0) * 0.9
        state.demand_kw += heating_bump_kw
        state.predicted_demand_kw += heating_bump_kw

    if "solar_multiplier" in modifiers:
        state.solar_kw *= modifiers["solar_multiplier"]
    if "wind_multiplier" in modifiers:
        state.wind_kw *= modifiers["wind_multiplier"]
    state.predicted_renewable_kw = state.solar_kw + state.wind_kw

    if "battery_soc_override_pct" in modifiers:
        state.battery_soc_pct = float(modifiers["battery_soc_override_pct"])
    if "battery_capacity_override_kwh" in modifiers:
        state.battery_capacity_kwh = float(modifiers["battery_capacity_override_kwh"])

    if "generator_available" in modifiers:
        state.generator_available = bool(modifiers["generator_available"])
        if not state.generator_available:
            state.generator_output_kw = 0.0
    if "fuel_override_pct" in modifiers:
        state.fuel_pct = float(modifiers["fuel_override_pct"])

    if "active_loads" in modifiers:
        # list of load names that should be treated as active; others zeroed.
        active = set(modifiers["active_loads"])
        for ld in state.loads:
            if ld.name not in active:
                ld.power_kw = 0.0

    state.demand_kw = max(state.demand_kw, 0.0)
    state.predicted_demand_kw = max(state.predicted_demand_kw, 0.0)
    state.solar_kw = max(state.solar_kw, 0.0)
    state.wind_kw = max(state.wind_kw, 0.0)
    return state


def run_scenario(base_state: StationState, modifiers: dict) -> SimulationOutcome:
    modified = apply_modifiers(base_state, modifiers)
    clamped_state, safety_notes = apply_safety_constraints(modified)
    recommendations = generate_recommendations(clamped_state)
    comparison = compare_baseline_vs_optimized(clamped_state)

    return SimulationOutcome(
        state=clamped_state,
        recommendations=recommendations,
        comparison=comparison,
        battery_status=battery_status_from_soc(clamped_state.battery_soc_pct),
        fuel_status=fuel_status_from_pct(clamped_state.fuel_pct),
        safety_notes=safety_notes,
    )
