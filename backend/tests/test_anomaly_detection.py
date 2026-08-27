import numpy as np
import pandas as pd

from app.services.anomaly_detection import (
    detect_generator_inefficiency,
    detect_sensor_anomalies,
    detect_via_isolation_forest,
)


def _make_demand_df(n_days: int = 20, spike_idx: int | None = None) -> pd.DataFrame:
    hours = n_days * 24
    ts = pd.date_range("2026-01-01", periods=hours, freq="h")
    hour = ts.hour.values
    base = 60 + 15 * np.sin(2 * np.pi * (hour - 8) / 24)
    rng = np.random.default_rng(0)
    values = base + rng.normal(0, 2, hours)
    if spike_idx is not None:
        values[spike_idx] = base[spike_idx] * 2.5  # inject a clear anomaly
    return pd.DataFrame({"timestamp": ts, "demand_kw": values})


def test_isolation_forest_flags_injected_consumption_spike():
    df = _make_demand_df(spike_idx=300)
    findings = detect_via_isolation_forest(df, "demand_kw", "Lab Block A", "consumption")
    assert len(findings) > 0
    flagged_timestamps = {f.timestamp for f in findings}
    assert df["timestamp"].iloc[300].to_pydatetime() in flagged_timestamps


def test_isolation_forest_returns_empty_for_too_little_data():
    df = _make_demand_df(n_days=1)[:10]
    findings = detect_via_isolation_forest(df, "demand_kw", "Lab Block A", "consumption")
    assert findings == []


def test_generator_inefficiency_flags_high_fuel_burn():
    ts = pd.date_range("2026-01-01", periods=5, freq="h")
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "output_kw": [50, 50, 50, 50, 50],
            "fuel_consumed_l": [16, 16, 16, 40, 16],  # row 3 is ~2.5x the rated rate
        }
    )
    findings = detect_generator_inefficiency(df, rated_l_per_kwh=0.32, generator_name="Gen 1", tolerance_pct=15)
    assert len(findings) == 1
    assert findings[0].affected_asset == "Gen 1"


def test_generator_inefficiency_ignores_idle_periods():
    ts = pd.date_range("2026-01-01", periods=3, freq="h")
    df = pd.DataFrame({"timestamp": ts, "output_kw": [0, 0, 0], "fuel_consumed_l": [0, 0, 0]})
    findings = detect_generator_inefficiency(df, rated_l_per_kwh=0.32, generator_name="Gen 1")
    assert findings == []


def test_sensor_anomaly_detects_missing_and_out_of_range_values():
    ts = pd.date_range("2026-01-01", periods=5, freq="h")
    df = pd.DataFrame({"timestamp": ts, "soc_pct": [50, np.nan, 105, -10, 60]})
    findings = detect_sensor_anomalies(df, "soc_pct", "Battery", (0, 100), "SOC")
    assert len(findings) == 3  # NaN, 105, -10
    assert all(f.severity.value == "critical" for f in findings)


def test_sensor_anomaly_passes_all_valid_values():
    ts = pd.date_range("2026-01-01", periods=3, freq="h")
    df = pd.DataFrame({"timestamp": ts, "soc_pct": [50, 60, 70]})
    findings = detect_sensor_anomalies(df, "soc_pct", "Battery", (0, 100), "SOC")
    assert findings == []
