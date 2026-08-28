"""Optimization engine edge cases: zero renewable, extreme demand, generator unavailable, low fuel."""

import pytest

from app.services.optimization import (
    ActionType,
    LoadState,
    StationState,
    apply_safety_constraints,
    compare_baseline_vs_optimized,
    generate_recommendations,
)


def make_state(**overrides) -> StationState:
    base = dict(
        demand_kw=80,
        predicted_demand_kw=85,
        solar_kw=20,
        wind_kw=10,
        predicted_renewable_kw=30,
        battery_soc_pct=60,
        battery_capacity_kwh=400,
        battery_min_soc_pct=15,
        battery_max_soc_pct=100,
        battery_max_charge_kw=100,
        battery_max_discharge_kw=100,
        generator_available=True,
        generator_capacity_kw=250,
        generator_output_kw=0,
        fuel_pct=80,
        co2_kg_per_l=2.68,
        fuel_l_per_kwh=0.32,
        loads=[
            LoadState("Life Support", 1, 20, False),
            LoadState("Lab", 2, 15, False),
            LoadState("Charging", 3, 8, True),
            LoadState("Recreation", 4, 4, False),
        ],
    )
    base.update(overrides)
    return StationState(**base)


def test_surplus_renewables_recommends_charging():
    state = make_state(demand_kw=30, solar_kw=25, wind_kw=20)  # 45kW renewable vs 30kW demand
    recs = generate_recommendations(state)
    assert any(r.action_type == ActionType.CHARGE_BATTERY for r in recs)


def test_zero_renewable_generation_falls_back_to_battery_or_generator():
    state = make_state(solar_kw=0.0, wind_kw=0.0, battery_soc_pct=70)
    recs = generate_recommendations(state)
    assert any(r.action_type in (ActionType.DISCHARGE_BATTERY, ActionType.START_GENERATOR) for r in recs)


def test_extreme_demand_with_full_battery_and_generator_starts_generator():
    state = make_state(demand_kw=500, solar_kw=5, wind_kw=5, battery_soc_pct=90)
    recs = generate_recommendations(state)
    assert any(r.action_type == ActionType.START_GENERATOR for r in recs)


def test_generator_unavailable_sheds_deferrable_load_before_critical():
    state = make_state(demand_kw=300, solar_kw=0, wind_kw=0, battery_soc_pct=16, generator_available=False)
    recs = generate_recommendations(state)
    actions = {r.action_type for r in recs}
    assert ActionType.SHED_DEFERRABLE_LOAD in actions or ActionType.SHED_NON_CRITICAL_LOAD in actions
    # Critical load itself is never a shed target in this engine's output.
    for r in recs:
        assert "Life Support" not in r.recommendation


def test_low_fuel_with_active_generator_warns_but_does_not_stop_critical_supply():
    state = make_state(fuel_pct=8, generator_output_kw=40)
    recs = generate_recommendations(state)
    assert any("resupply" in r.recommendation.lower() or "fuel" in r.reason.lower() for r in recs)


def test_battery_at_critical_soc_never_recommended_for_further_discharge():
    state = make_state(demand_kw=150, solar_kw=0, wind_kw=0, battery_soc_pct=9, generator_available=True, fuel_pct=50)
    recs = generate_recommendations(state)
    assert not any(r.action_type == ActionType.DISCHARGE_BATTERY for r in recs)
    assert any(r.action_type == ActionType.START_GENERATOR for r in recs)


def test_no_action_needed_when_balanced():
    # Renewables ~= demand (within the +-1kW dead zone), battery/fuel both normal.
    state = make_state(demand_kw=25, solar_kw=13, wind_kw=12, battery_soc_pct=60)
    recs = generate_recommendations(state)
    assert any(r.action_type == ActionType.MAINTAIN for r in recs)


def test_apply_safety_constraints_clamps_out_of_range_soc():
    state = make_state(battery_soc_pct=150)  # impossible sensor value
    clamped_state, notes = apply_safety_constraints(state)
    assert clamped_state.battery_soc_pct == 100
    assert len(notes) == 1


def test_apply_safety_constraints_clamps_generator_over_capacity():
    state = make_state(generator_output_kw=999)
    clamped_state, notes = apply_safety_constraints(state)
    assert clamped_state.generator_output_kw == state.generator_capacity_kw
    assert len(notes) == 1


def test_baseline_vs_optimized_never_reports_negative_savings_as_optimized_worse_when_battery_helps():
    state = make_state(demand_kw=120, solar_kw=10, wind_kw=10, battery_soc_pct=80)
    comparison = compare_baseline_vs_optimized(state)
    assert comparison.optimized_fuel_l <= comparison.baseline_fuel_l
    assert comparison.optimized_co2_kg <= comparison.baseline_co2_kg


def test_baseline_comparison_handles_zero_demand_without_division_error():
    state = make_state(demand_kw=0, solar_kw=0, wind_kw=0)
    comparison = compare_baseline_vs_optimized(state)
    assert comparison.baseline_fuel_l == 0
    assert comparison.optimized_fuel_l == 0
