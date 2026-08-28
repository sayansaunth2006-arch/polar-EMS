"""Rule-based energy optimization / recommendation engine.

This is an explainable, deterministic decision engine (not a black-box
model) that turns the current + forecast station state into prioritized,
human-readable recommendations. It is intentionally rule-based so every
recommendation can state WHY it was made — the project's explainability
requirement is much harder to satisfy with an opaque RL/optimizer, and a
transparent rules engine is the more defensible choice for safety-critical
energy dispatch in a hackathon prototype.

Hard safety constraints (see app.services.safety) are applied on top of
every recommendation and always win.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.core.config import get_settings
from app.services.safety import battery_status_from_soc, enforce_battery_limits, enforce_generator_limits, fuel_status_from_pct

settings = get_settings()


class ActionType(str, Enum):
    CHARGE_BATTERY = "charge_battery"
    DISCHARGE_BATTERY = "discharge_battery"
    START_GENERATOR = "start_generator"
    STOP_GENERATOR = "stop_generator"
    SHED_DEFERRABLE_LOAD = "shed_deferrable_load"
    SHED_NON_CRITICAL_LOAD = "shed_non_critical_load"
    MAINTAIN = "maintain"


class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LoadState:
    name: str
    priority: int  # 1=critical .. 4=non-critical
    power_kw: float
    is_deferrable: bool = False


@dataclass
class StationState:
    demand_kw: float
    predicted_demand_kw: float
    solar_kw: float
    wind_kw: float
    predicted_renewable_kw: float
    battery_soc_pct: float
    battery_capacity_kwh: float
    battery_min_soc_pct: float
    battery_max_soc_pct: float
    battery_max_charge_kw: float
    battery_max_discharge_kw: float
    generator_available: bool
    generator_capacity_kw: float
    generator_output_kw: float
    fuel_pct: float
    co2_kg_per_l: float
    fuel_l_per_kwh: float
    loads: list[LoadState] = field(default_factory=list)


@dataclass
class Recommendation:
    action_type: ActionType
    recommendation: str
    reason: str
    expected_benefit: str
    priority: RecommendationPriority


def _battery_available_kwh(state: StationState) -> float:
    return max((state.battery_soc_pct - state.battery_min_soc_pct) / 100 * state.battery_capacity_kwh, 0.0)


def _battery_headroom_kwh(state: StationState) -> float:
    return max((state.battery_max_soc_pct - state.battery_soc_pct) / 100 * state.battery_capacity_kwh, 0.0)


def generate_recommendations(state: StationState) -> list[Recommendation]:
    """Core optimization objectives, evaluated in priority order:
    1) protect critical loads, 2) maximize renewable utilization,
    3) minimize diesel, 4) minimize unnecessary cycling, 5) maintain reserve,
    6) reduce CO2, 7) maintain reliability."""

    recs: list[Recommendation] = []
    renewable_kw = state.solar_kw + state.wind_kw
    net_kw = state.demand_kw - renewable_kw  # positive = shortfall, negative = surplus

    battery_status = battery_status_from_soc(state.battery_soc_pct)
    fuel_status = fuel_status_from_pct(state.fuel_pct)

    # 1. Surplus renewables -> charge battery instead of wasting it.
    if net_kw < -1.0:
        surplus = -net_kw
        chargeable = min(surplus, state.battery_max_charge_kw, _battery_headroom_kwh(state))
        if chargeable > 0.5:
            recs.append(
                Recommendation(
                    action_type=ActionType.CHARGE_BATTERY,
                    recommendation=f"Charge battery using {chargeable:.0f} kW of excess renewable energy.",
                    reason=(
                        f"Renewable generation ({renewable_kw:.0f} kW) currently exceeds demand "
                        f"({state.demand_kw:.0f} kW) by {surplus:.0f} kW."
                    ),
                    expected_benefit="Stores otherwise-curtailed renewable energy, reducing future generator runtime.",
                    priority=RecommendationPriority.MEDIUM,
                )
            )

    # 2. Shortfall -> prefer battery discharge over generator when reserve allows.
    elif net_kw > 1.0:
        shortfall = net_kw
        available = _battery_available_kwh(state)
        dischargeable_kw = min(shortfall, state.battery_max_discharge_kw)

        if available > 0 and battery_status == "NORMAL":
            recs.append(
                Recommendation(
                    action_type=ActionType.DISCHARGE_BATTERY,
                    recommendation=f"Use battery to cover {dischargeable_kw:.0f} kW of the current shortfall.",
                    reason=(
                        f"Demand ({state.demand_kw:.0f} kW) exceeds renewable generation "
                        f"({renewable_kw:.0f} kW) and battery reserve ({state.battery_soc_pct:.0f}% SOC) "
                        "is above the safety threshold."
                    ),
                    expected_benefit="Avoids starting/loading the diesel generator, reducing fuel use and CO2.",
                    priority=RecommendationPriority.MEDIUM,
                )
            )
            shortfall = max(shortfall - dischargeable_kw, 0.0)

        if shortfall > 1.0:
            if state.generator_available and fuel_status != "CRITICAL":
                recs.append(
                    Recommendation(
                        action_type=ActionType.START_GENERATOR,
                        recommendation=f"Start generator to cover the remaining {shortfall:.0f} kW deficit.",
                        reason=(
                            "Battery reserve is insufficient or already near its minimum safety threshold; "
                            f"predicted 24h demand of {state.predicted_demand_kw:.0f} kW cannot be met by "
                            f"renewables + battery alone."
                        ),
                        expected_benefit="Maintains reliable supply to all load tiers, including critical loads.",
                        priority=RecommendationPriority.HIGH if battery_status != "NORMAL" else RecommendationPriority.MEDIUM,
                    )
                )
            else:
                deferrable = [ld for ld in state.loads if ld.is_deferrable]
                if deferrable:
                    total_deferrable_kw = sum(ld.power_kw for ld in deferrable)
                    recs.append(
                        Recommendation(
                            action_type=ActionType.SHED_DEFERRABLE_LOAD,
                            recommendation=(
                                f"Delay deferrable loads ({', '.join(l.name for l in deferrable)}) "
                                f"totalling {total_deferrable_kw:.0f} kW."
                            ),
                            reason=(
                                "Generator is unavailable or fuel is critically low, and battery reserve cannot "
                                "cover the full deficit without breaching the safety floor."
                            ),
                            expected_benefit="Protects critical and important loads by shedding only optional load.",
                            priority=RecommendationPriority.CRITICAL,
                        )
                    )
                non_critical = [ld for ld in state.loads if ld.priority == 4]
                if non_critical:
                    recs.append(
                        Recommendation(
                            action_type=ActionType.SHED_NON_CRITICAL_LOAD,
                            recommendation=f"Reduce non-critical load ({', '.join(l.name for l in non_critical)}).",
                            reason="Emergency reserve conditions: reliability of critical systems takes priority over comfort/non-essential load.",
                            expected_benefit="Extends remaining safe operating time for life-support and critical systems.",
                            priority=RecommendationPriority.CRITICAL,
                        )
                    )

    # Battery/fuel reserve alerts feed into recommendations too, even absent an
    # immediate shortfall, so operators get advance warning.
    if battery_status != "NORMAL":
        recs.append(
            Recommendation(
                action_type=ActionType.MAINTAIN,
                recommendation="Avoid further battery discharge; prioritize generator or load shedding for any new deficit.",
                reason=f"Battery SOC is {state.battery_soc_pct:.0f}%, at or below the {battery_status.lower()} threshold.",
                expected_benefit="Preserves battery health and emergency reserve for critical loads.",
                priority=RecommendationPriority.HIGH if battery_status == "CRITICAL" else RecommendationPriority.MEDIUM,
            )
        )

    if fuel_status != "NORMAL" and state.generator_output_kw > 0:
        recs.append(
            Recommendation(
                action_type=ActionType.MAINTAIN,
                recommendation="Schedule diesel resupply / minimize non-essential generator runtime.",
                reason=f"Fuel level is {state.fuel_pct:.0f}%, at or below the {fuel_status.lower()} threshold.",
                expected_benefit="Avoids a future full deficit event if resupply is delayed.",
                priority=RecommendationPriority.HIGH if fuel_status == "CRITICAL" else RecommendationPriority.MEDIUM,
            )
        )

    if not recs:
        recs.append(
            Recommendation(
                action_type=ActionType.MAINTAIN,
                recommendation="No action needed — renewables and battery are covering demand within safe limits.",
                reason=f"Net balance is {-net_kw:+.0f} kW with battery SOC at {state.battery_soc_pct:.0f}%.",
                expected_benefit="System is operating optimally; continue monitoring.",
                priority=RecommendationPriority.LOW,
            )
        )

    return recs


def apply_safety_constraints(state: StationState) -> tuple[StationState, list[str]]:
    """Clamp the state to hard safety limits and report any violations found
    (used to distinguish an AI recommendation from a safety-checked actual
    control command)."""

    notes: list[str] = []
    clamped_soc, soc_violations = enforce_battery_limits(state.battery_soc_pct, state.battery_min_soc_pct, state.battery_max_soc_pct)
    notes += [v.detail for v in soc_violations]

    clamped_gen, gen_violations = enforce_generator_limits(state.generator_output_kw, state.generator_capacity_kw)
    notes += [v.detail for v in gen_violations]

    state.battery_soc_pct = clamped_soc
    state.generator_output_kw = clamped_gen
    return state, notes


@dataclass
class BaselineComparison:
    baseline_fuel_l: float
    optimized_fuel_l: float
    baseline_co2_kg: float
    optimized_co2_kg: float
    baseline_renewable_utilization_pct: float
    optimized_renewable_utilization_pct: float
    estimated_fuel_saved_l: float
    estimated_co2_saved_kg: float


def compare_baseline_vs_optimized(state: StationState, horizon_hours: float = 24.0) -> BaselineComparison:
    """Simple baseline strategy: generator follows demand directly with only
    minimal renewable use (no forecast-driven battery pre-charging or load
    shedding) vs. this engine's forecast+battery-aware dispatch.

    This is a simulation/prototype estimate, not a guaranteed real-world
    saving — the numbers are labeled as such wherever they're surfaced."""

    renewable_kw = state.solar_kw + state.wind_kw

    # Baseline: renewables offset demand 1:1 up to their output, generator covers 100% of the rest.
    baseline_gen_kw = max(state.demand_kw - renewable_kw, 0.0)
    baseline_fuel_l = baseline_gen_kw * horizon_hours * state.fuel_l_per_kwh
    baseline_renewable_util = min(renewable_kw, state.demand_kw) / max(state.demand_kw, 1e-6) * 100

    # Optimized: battery absorbs part of the shortfall before generator engages.
    net_kw = state.demand_kw - renewable_kw
    battery_cover_kw = min(max(net_kw, 0.0), state.battery_max_discharge_kw, _battery_available_kwh(state) / max(horizon_hours, 0.25))
    optimized_gen_kw = max(net_kw - battery_cover_kw, 0.0)
    optimized_fuel_l = optimized_gen_kw * horizon_hours * state.fuel_l_per_kwh
    optimized_renewable_util = min(renewable_kw + battery_cover_kw, state.demand_kw) / max(state.demand_kw, 1e-6) * 100

    baseline_co2 = baseline_fuel_l * state.co2_kg_per_l
    optimized_co2 = optimized_fuel_l * state.co2_kg_per_l

    return BaselineComparison(
        baseline_fuel_l=round(baseline_fuel_l, 1),
        optimized_fuel_l=round(optimized_fuel_l, 1),
        baseline_co2_kg=round(baseline_co2, 1),
        optimized_co2_kg=round(optimized_co2, 1),
        baseline_renewable_utilization_pct=round(baseline_renewable_util, 1),
        optimized_renewable_utilization_pct=round(optimized_renewable_util, 1),
        estimated_fuel_saved_l=round(baseline_fuel_l - optimized_fuel_l, 1),
        estimated_co2_saved_kg=round(baseline_co2 - optimized_co2, 1),
    )
