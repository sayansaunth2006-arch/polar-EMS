"""Deterministic safety-first control layer.

These functions are the hard boundary the AI recommendation/optimization
layer is NOT allowed to cross. They never depend on a model's confidence and
are always evaluated last, after any AI recommendation, so that a bad or
low-confidence prediction can never push the system into an unsafe state.

Per the project's safety requirement: an "AI RECOMMENDATION" is advisory
text; an "ACTUAL CONTROL COMMAND" (simulated, in this prototype) always
passes through `enforce_battery_limits` / `enforce_generator_limits` /
`validate_sensor_value` before being considered valid.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


@dataclass
class SafetyViolation:
    rule: str
    detail: str


def enforce_battery_limits(soc_pct: float, min_soc_pct: float, max_soc_pct: float) -> tuple[float, list[SafetyViolation]]:
    violations: list[SafetyViolation] = []
    clamped = soc_pct
    if soc_pct < min_soc_pct:
        violations.append(SafetyViolation("battery_min_soc", f"SOC {soc_pct:.1f}% below configured minimum reserve {min_soc_pct:.1f}%"))
        clamped = min_soc_pct
    if soc_pct > max_soc_pct:
        violations.append(SafetyViolation("battery_max_soc", f"SOC {soc_pct:.1f}% exceeds configured maximum {max_soc_pct:.1f}%"))
        clamped = max_soc_pct
    return clamped, violations


def enforce_generator_limits(requested_kw: float, rated_capacity_kw: float) -> tuple[float, list[SafetyViolation]]:
    if requested_kw > rated_capacity_kw:
        return rated_capacity_kw, [
            SafetyViolation(
                "generator_capacity",
                f"Requested {requested_kw:.1f} kW exceeds rated capacity {rated_capacity_kw:.1f} kW; capped.",
            )
        ]
    return max(requested_kw, 0.0), []


def validate_sensor_value(value: float | None, valid_range: tuple[float, float], name: str) -> tuple[bool, list[SafetyViolation]]:
    if value is None:
        return False, [SafetyViolation("missing_sensor_data", f"{name} reading missing; safe fallback applied.")]
    lo, hi = valid_range
    if value < lo or value > hi:
        return False, [SafetyViolation("invalid_sensor_value", f"{name}={value} outside plausible range [{lo}, {hi}]; rejected.")]
    return True, []


def should_use_deterministic_fallback(model_confidence: float) -> bool:
    """Low-confidence AI predictions must fall back to deterministic logic
    (e.g. persistence / rule-based dispatch) rather than be trusted blindly."""
    return model_confidence < settings.forecast_confidence_low_threshold


def battery_status_from_soc(soc_pct: float) -> str:
    if soc_pct <= settings.battery_soc_critical_pct:
        return "CRITICAL"
    if soc_pct <= settings.battery_soc_warning_pct:
        return "WARNING"
    return "NORMAL"


def fuel_status_from_pct(fuel_pct: float) -> str:
    if fuel_pct <= settings.generator_min_fuel_critical_pct:
        return "CRITICAL"
    if fuel_pct <= settings.generator_min_fuel_warning_pct:
        return "WARNING"
    return "NORMAL"


def battery_temperature_status(temp_c: float) -> str:
    if temp_c >= settings.battery_temp_max_celsius or temp_c <= settings.battery_temp_min_celsius:
        return "CRITICAL"
    return "NORMAL"
