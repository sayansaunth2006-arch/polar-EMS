import numpy as np
import pandas as pd

from app.services.forecasting import EnergyCondition, build_demand_forecaster, classify_energy_condition


def _synthetic_demand_df(days: int = 30) -> pd.DataFrame:
    hours = days * 24
    ts = pd.date_range("2026-01-01", periods=hours, freq="h")
    hour = ts.hour.values
    day_idx = np.arange(hours) // 24
    seasonal = 5 * np.sin(2 * np.pi * day_idx / 30)
    diurnal = 15 * np.sin(2 * np.pi * (hour - 8) / 24)
    rng = np.random.default_rng(1)
    demand = 60 + seasonal + diurnal + rng.normal(0, 1.5, hours)
    temp = -20 + 5 * np.sin(2 * np.pi * (hour - 14) / 24)
    return pd.DataFrame({"timestamp": ts, "demand_kw": demand, "temperature_celsius": temp})


def test_demand_forecaster_trains_and_reports_metrics_for_all_horizons():
    df = _synthetic_demand_df()
    forecaster = build_demand_forecaster(df)
    assert set(forecaster.models.keys()) == {1, 6, 24}
    for h in (1, 6, 24):
        assert forecaster.metrics[h].n_test > 0
        assert forecaster.metrics[h].mae >= 0
        assert forecaster.metrics[h].rmse >= 0


def test_demand_forecaster_predicts_positive_reasonable_value():
    df = _synthetic_demand_df()
    forecaster = build_demand_forecaster(df)
    result = forecaster.predict(df, 1)
    assert result.predicted_value_kw > 0
    assert 0 <= result.confidence <= 1


def test_demand_forecaster_handles_sparse_data_gracefully():
    df = _synthetic_demand_df(days=1)  # only 24 rows, below minimum for reliable split
    forecaster = build_demand_forecaster(df)
    # Should not crash; may simply have no trained horizons if insufficient rows.
    assert isinstance(forecaster.models, dict)


def test_classify_energy_condition_surplus():
    assert classify_energy_condition(predicted_demand_kw=50, predicted_renewable_kw=80, battery_available_kwh=100, horizon_hours=6) == EnergyCondition.SURPLUS


def test_classify_energy_condition_balanced_when_battery_covers_shortfall():
    cond = classify_energy_condition(predicted_demand_kw=100, predicted_renewable_kw=70, battery_available_kwh=200, horizon_hours=6)
    assert cond == EnergyCondition.BALANCED


def test_classify_energy_condition_deficit_when_battery_insufficient():
    cond = classify_energy_condition(predicted_demand_kw=200, predicted_renewable_kw=20, battery_available_kwh=10, horizon_hours=6)
    assert cond == EnergyCondition.DEFICIT
