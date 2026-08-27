"""Battery/generator safety-constraint edge cases: SOC 0/100, invalid sensors, extreme temps."""

from app.services.safety import (
    battery_status_from_soc,
    battery_temperature_status,
    enforce_battery_limits,
    enforce_generator_limits,
    fuel_status_from_pct,
    should_use_deterministic_fallback,
    validate_sensor_value,
)


def test_battery_soc_zero_is_clamped_to_minimum():
    clamped, violations = enforce_battery_limits(0.0, min_soc_pct=15.0, max_soc_pct=100.0)
    assert clamped == 15.0
    assert len(violations) == 1
    assert violations[0].rule == "battery_min_soc"


def test_battery_soc_hundred_is_within_bounds():
    clamped, violations = enforce_battery_limits(100.0, min_soc_pct=15.0, max_soc_pct=100.0)
    assert clamped == 100.0
    assert violations == []


def test_battery_soc_above_max_is_clamped():
    clamped, violations = enforce_battery_limits(105.0, min_soc_pct=15.0, max_soc_pct=100.0)
    assert clamped == 100.0
    assert violations[0].rule == "battery_max_soc"


def test_battery_status_thresholds():
    assert battery_status_from_soc(50) == "NORMAL"
    assert battery_status_from_soc(20) == "WARNING"
    assert battery_status_from_soc(10) == "CRITICAL"
    assert battery_status_from_soc(0) == "CRITICAL"


def test_battery_temperature_extremes_flagged_critical():
    assert battery_temperature_status(10) == "NORMAL"
    assert battery_temperature_status(50) == "CRITICAL"  # too hot
    assert battery_temperature_status(-25) == "CRITICAL"  # too cold


def test_generator_output_capped_at_rated_capacity():
    capped, violations = enforce_generator_limits(300.0, rated_capacity_kw=250.0)
    assert capped == 250.0
    assert len(violations) == 1


def test_generator_output_negative_is_clamped_to_zero():
    capped, violations = enforce_generator_limits(-10.0, rated_capacity_kw=250.0)
    assert capped == 0.0
    assert violations == []


def test_fuel_status_thresholds():
    assert fuel_status_from_pct(50) == "NORMAL"
    assert fuel_status_from_pct(25) == "WARNING"
    assert fuel_status_from_pct(5) == "CRITICAL"


def test_missing_sensor_value_is_rejected():
    valid, violations = validate_sensor_value(None, (0, 100), "SOC sensor")
    assert valid is False
    assert violations[0].rule == "missing_sensor_data"


def test_invalid_sensor_value_out_of_range_is_rejected():
    valid, violations = validate_sensor_value(-999, (0, 100), "SOC sensor")
    assert valid is False
    assert violations[0].rule == "invalid_sensor_value"


def test_valid_sensor_value_passes():
    valid, violations = validate_sensor_value(55.0, (0, 100), "SOC sensor")
    assert valid is True
    assert violations == []


def test_low_confidence_triggers_deterministic_fallback():
    assert should_use_deterministic_fallback(0.2) is True
    assert should_use_deterministic_fallback(0.9) is False
