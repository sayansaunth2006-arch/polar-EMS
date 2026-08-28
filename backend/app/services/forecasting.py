"""AI energy demand + renewable generation forecasting.

Uses scikit-learn ensemble regressors (RandomForest/GradientBoosting) trained
on the station's historical (synthetic, in this prototype) time series. Every
prediction returned by this module is explicitly a *model prediction*, never
presented as a measured value.

Forecasting approach: for each horizon (1h, 6h, 24h) we train a direct
multi-step model whose target is demand (or renewable output) `horizon`
hours ahead of the feature row. Features are everything knowable at
prediction time: calendar features of the *target* timestamp (hour, month,
weekend), and the most recent lag/rolling statistics of the signal itself
plus the latest weather reading as a proxy for near-term conditions. This is
a standard, explainable approach for a resource-constrained prototype -- a
production system would instead condition on an actual weather forecast.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class EnergyCondition(str, Enum):
    SURPLUS = "surplus"
    BALANCED = "balanced"
    DEFICIT = "deficit"


@dataclass
class ModelMetrics:
    mae: float
    rmse: float
    r2: float
    n_train: int
    n_test: int

    def as_dict(self) -> dict:
        return {
            "mae_kw": round(self.mae, 3),
            "rmse_kw": round(self.rmse, 3),
            "r2": round(self.r2, 4),
            "n_train": self.n_train,
            "n_test": self.n_test,
        }


@dataclass
class ForecastResult:
    horizon_hours: int
    predicted_value_kw: float
    model_name: str
    confidence: float
    metrics: ModelMetrics


def _evaluate(y_true: np.ndarray, y_pred: np.ndarray, n_train: int) -> ModelMetrics:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else 0.0
    return ModelMetrics(mae=mae, rmse=rmse, r2=r2, n_train=n_train, n_test=len(y_true))


def _confidence_from_r2(r2: float) -> float:
    """Map R^2 to a friendlier 0-1 "confidence" score shown in the UI."""
    return float(np.clip(0.5 + r2 / 2, 0.05, 0.98))


def _calendar_features(ts: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hour": ts.dt.hour,
            "month": ts.dt.month,
            "day_of_week": ts.dt.dayofweek,
            "is_weekend": (ts.dt.dayofweek >= 5).astype(int),
            "hour_sin": np.sin(2 * np.pi * ts.dt.hour / 24),
            "hour_cos": np.cos(2 * np.pi * ts.dt.hour / 24),
            "month_sin": np.sin(2 * np.pi * ts.dt.month / 12),
            "month_cos": np.cos(2 * np.pi * ts.dt.month / 12),
        }
    )


class TimeSeriesForecaster:
    """Direct multi-step forecaster for a single target signal (demand, solar, wind)."""

    def __init__(self, target_col: str, extra_feature_cols: list[str], model_name: str = "random_forest") -> None:
        self.target_col = target_col
        self.extra_feature_cols = extra_feature_cols
        self.model_name = model_name
        self.models: dict[int, object] = {}
        self.metrics: dict[int, ModelMetrics] = {}

    def _build_model(self):
        if self.model_name == "gradient_boosting":
            return GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        return RandomForestRegressor(n_estimators=200, max_depth=10, min_samples_leaf=3, random_state=42, n_jobs=-1)

    def _make_supervised(self, df: pd.DataFrame, horizon_hours: int) -> tuple[pd.DataFrame, pd.Series]:
        df = df.sort_values("timestamp").reset_index(drop=True)
        target = df[self.target_col]

        feats = _calendar_features(df["timestamp"] + pd.to_timedelta(horizon_hours, unit="h"))
        feats["lag_1"] = target.shift(0)  # most recent known value at feature time t
        feats["lag_24"] = target.shift(23)
        feats["lag_168"] = target.shift(167)
        feats["rolling_mean_6"] = target.rolling(6, min_periods=1).mean()
        feats["rolling_std_6"] = target.rolling(6, min_periods=1).std().fillna(0)
        for col in self.extra_feature_cols:
            feats[col] = df[col]

        y = target.shift(-horizon_hours)  # value `horizon_hours` after feature row t

        valid = feats.notna().all(axis=1) & y.notna()
        return feats[valid], y[valid]

    def fit(self, df: pd.DataFrame, horizons: list[int]) -> None:
        for h in horizons:
            X, y = self._make_supervised(df, h)
            if len(X) < 20:
                continue
            split = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split], X.iloc[split:]
            y_train, y_test = y.iloc[:split], y.iloc[split:]

            model = self._build_model()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test) if len(X_test) else np.array([])

            self.models[h] = model
            if len(y_test):
                self.metrics[h] = _evaluate(y_test.to_numpy(), y_pred, n_train=len(X_train))
            else:
                self.metrics[h] = ModelMetrics(mae=0, rmse=0, r2=0, n_train=len(X_train), n_test=0)

    def predict(self, df: pd.DataFrame, horizon_hours: int) -> ForecastResult:
        if horizon_hours not in self.models:
            raise ValueError(f"No trained model for horizon={horizon_hours}h")

        df = df.sort_values("timestamp").reset_index(drop=True)
        latest_ts = df["timestamp"].iloc[-1]
        target = df[self.target_col]

        row = _calendar_features(pd.Series([latest_ts + pd.Timedelta(hours=horizon_hours)]))
        row["lag_1"] = target.iloc[-1]
        row["lag_24"] = target.iloc[-24] if len(target) >= 24 else target.iloc[0]
        row["lag_168"] = target.iloc[-168] if len(target) >= 168 else target.iloc[0]
        row["rolling_mean_6"] = target.tail(6).mean()
        row["rolling_std_6"] = target.tail(6).std() if len(target) >= 2 else 0.0
        for col in self.extra_feature_cols:
            row[col] = df[col].iloc[-1]

        model = self.models[horizon_hours]
        pred = float(model.predict(row[self._feature_order(row)])[0])
        pred = max(pred, 0.0)

        metrics = self.metrics[horizon_hours]
        return ForecastResult(
            horizon_hours=horizon_hours,
            predicted_value_kw=round(pred, 2),
            model_name=type(model).__name__,
            confidence=_confidence_from_r2(metrics.r2),
            metrics=metrics,
        )

    @staticmethod
    def _feature_order(row: pd.DataFrame) -> list[str]:
        return list(row.columns)


DEMAND_HORIZONS = [1, 6, 24]


def build_demand_forecaster(df: pd.DataFrame) -> TimeSeriesForecaster:
    """df must have columns: timestamp, demand_kw, temperature_celsius."""
    forecaster = TimeSeriesForecaster(
        target_col="demand_kw",
        extra_feature_cols=["temperature_celsius"],
        model_name="random_forest",
    )
    forecaster.fit(df, DEMAND_HORIZONS)
    return forecaster


def build_renewable_forecaster(df: pd.DataFrame, target_col: str) -> TimeSeriesForecaster:
    """df must have columns: timestamp, <target_col>, cloud_cover_pct, wind_speed_mps, solar_irradiance_w_m2."""
    forecaster = TimeSeriesForecaster(
        target_col=target_col,
        extra_feature_cols=["cloud_cover_pct", "wind_speed_mps", "solar_irradiance_w_m2"],
        model_name="gradient_boosting",
    )
    forecaster.fit(df, DEMAND_HORIZONS)
    return forecaster


def classify_energy_condition(
    predicted_demand_kw: float,
    predicted_renewable_kw: float,
    battery_available_kwh: float,
    horizon_hours: float,
    surplus_margin_kw: float = 5.0,
) -> EnergyCondition:
    """Classify the forecast net-energy condition for a horizon.

    net = renewable - demand (kW). Positive net for the whole horizon implies
    a surplus; a shortfall the battery cannot absorb implies a deficit.
    """

    net_kw = predicted_renewable_kw - predicted_demand_kw
    if net_kw >= surplus_margin_kw:
        return EnergyCondition.SURPLUS

    shortfall_kwh = max(-net_kw, 0) * horizon_hours
    if shortfall_kwh <= battery_available_kwh:
        return EnergyCondition.BALANCED
    return EnergyCondition.DEFICIT
