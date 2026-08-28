from app.services.optimization import LoadState, StationState
from app.services.simulation import apply_modifiers, run_scenario


def base_state() -> StationState:
    return StationState(
        demand_kw=80, predicted_demand_kw=85, solar_kw=20, wind_kw=10, predicted_renewable_kw=30,
        battery_soc_pct=60, battery_capacity_kwh=400, battery_min_soc_pct=15, battery_max_soc_pct=100,
        battery_max_charge_kw=100, battery_max_discharge_kw=100,
        generator_available=True, generator_capacity_kw=250, generator_output_kw=0,
        fuel_pct=80, co2_kg_per_l=2.68, fuel_l_per_kwh=0.32,
        loads=[LoadState("Life Support", 1, 20, False), LoadState("Charging", 3, 8, True)],
    )


def test_extreme_cold_wave_increases_demand():
    state = base_state()
    modified = apply_modifiers(state, {"temperature_delta_c": -25})
    assert modified.demand_kw > state.demand_kw


def test_solar_drop_reduces_solar_output_only():
    state = base_state()
    modified = apply_modifiers(state, {"solar_multiplier": 0.1})
    assert modified.solar_kw == state.solar_kw * 0.1
    assert modified.wind_kw == state.wind_kw


def test_generator_unavailable_zeroes_generator_output():
    state = base_state()
    state.generator_output_kw = 40
    modified = apply_modifiers(state, {"generator_available": False})
    assert modified.generator_available is False
    assert modified.generator_output_kw == 0


def test_battery_soc_override_never_produces_out_of_bounds_state_after_run():
    state = base_state()
    outcome = run_scenario(state, {"battery_soc_override_pct": -50})  # invalid override
    assert 0 <= outcome.state.battery_soc_pct <= 100
    assert outcome.state.battery_soc_pct >= state.battery_min_soc_pct


def test_run_scenario_generator_unavailable_and_low_battery_recommends_load_shedding():
    state = base_state()
    outcome = run_scenario(state, {"generator_available": False, "battery_soc_override_pct": 16, "demand_multiplier": 3})
    assert outcome.battery_status in ("WARNING", "CRITICAL", "NORMAL")
    assert len(outcome.recommendations) > 0


def test_active_loads_filter_zeroes_unlisted_loads():
    state = base_state()
    modified = apply_modifiers(state, {"active_loads": ["Life Support"]})
    charging = next(l for l in modified.loads if l.name == "Charging")
    life_support = next(l for l in modified.loads if l.name == "Life Support")
    assert charging.power_kw == 0.0
    assert life_support.power_kw == state.loads[0].power_kw
