"""Explainable anomaly detection for POLAR-EMS.

Two complementary techniques are used, matched to what each anomaly class
actually needs:

  * IsolationForest (unsupervised, multivariate) for signals whose "normal"
    range is diurnal/seasonal and not a fixed threshold: consumption,
    battery discharge rate, renewable output.
  * Deterministic/statistical checks for signals with a known physical
    expectation: generator fuel efficiency (rated L/kWh) and raw sensor
    plausibility (out-of-range values, NaNs, physically impossible readings).

Every finding always reports observed vs. expected value and a human
explanation, per the project's explainability requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AnomalyFinding:
    timestamp: datetime
    severity: AnomalySeverity
    affected_asset: str
    metric: str
    observed_value: float
    expected_value: float
    deviation_pct: float
    explanation: str


def _severity_from_deviation(abs_deviation_pct: float) -> AnomalySeverity:
    if abs_deviation_pct >= 40:
        return AnomalySeverity.CRITICAL
    if abs_deviation_pct >= 20:
        return AnomalySeverity.WARNING
    return AnomalySeverity.INFO


def _hour_of_day_expected(df: pd.DataFrame, value_col: str) -> pd.Series:
    """Per-row expected value = median of that column for the same hour-of-day,
    a robust seasonally-naive baseline that's cheap and explainable."""

    hour = df["timestamp"].dt.hour
    return df.groupby(hour)[value_col].transform("median")


def detect_via_isolation_forest(
    df: pd.DataFrame,
    value_col: str,
    asset_name: str,
    metric_name: str,
    direction_phrase: tuple[str, str] = ("higher", "lower"),
    contamination: float = 0.03,
    max_findings: int = 15,
) -> list[AnomalyFinding]:
    """Flag statistically unusual points in `df[value_col]` relative to time-of-day baseline."""

    if len(df) < 30:
        return []

    df = df.sort_values("timestamp").reset_index(drop=True)
    hour = df["timestamp"].dt.hour
    features = pd.DataFrame(
        {
            "value": df[value_col],
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
        }
    )

    model = IsolationForest(n_estimators=150, contamination=contamination, random_state=42)
    preds = model.fit_predict(features)
    scores = model.decision_function(features)

    expected = _hour_of_day_expected(df, value_col)

    findings: list[AnomalyFinding] = []
    flagged_idx = np.where(preds == -1)[0]
    # Most anomalous first (most negative decision_function score).
    flagged_idx = flagged_idx[np.argsort(scores[flagged_idx])]

    for idx in flagged_idx[:max_findings]:
        observed = float(df[value_col].iloc[idx])
        exp_val = float(expected.iloc[idx]) if not pd.isna(expected.iloc[idx]) else observed
        deviation_pct = ((observed - exp_val) / exp_val * 100) if abs(exp_val) > 1e-6 else 0.0
        direction = direction_phrase[0] if deviation_pct >= 0 else direction_phrase[1]

        findings.append(
            AnomalyFinding(
                timestamp=df["timestamp"].iloc[idx].to_pydatetime(),
                severity=_severity_from_deviation(abs(deviation_pct)),
                affected_asset=asset_name,
                metric=metric_name,
                observed_value=round(observed, 2),
                expected_value=round(exp_val, 2),
                deviation_pct=round(deviation_pct, 1),
                explanation=(
                    f"{asset_name} shows {metric_name} of {observed:.1f} kW, "
                    f"approximately {abs(deviation_pct):.0f}% {direction} than the "
                    f"{exp_val:.1f} kW typically expected at this time of day."
                ),
            )
        )
    return findings


def detect_generator_inefficiency(
    df: pd.DataFrame,
    rated_l_per_kwh: float,
    generator_name: str,
    tolerance_pct: float = 15.0,
) -> list[AnomalyFinding]:
    """Deterministic check: actual fuel-per-kWh vs. the generator's rated efficiency."""

    findings: list[AnomalyFinding] = []
    running = df[df["output_kw"] > 5].copy()
    if running.empty:
        return findings

    running["actual_l_per_kwh"] = running["fuel_consumed_l"] / running["output_kw"].clip(lower=0.01)
    deviation_pct = (running["actual_l_per_kwh"] - rated_l_per_kwh) / rated_l_per_kwh * 100
    inefficient = running[deviation_pct > tolerance_pct]

    for idx, row in inefficient.iterrows():
        dev = float(deviation_pct.loc[idx])
        findings.append(
            AnomalyFinding(
                timestamp=row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
                severity=_severity_from_deviation(dev),
                affected_asset=generator_name,
                metric="fuel efficiency",
                observed_value=round(float(row["actual_l_per_kwh"]), 3),
                expected_value=round(rated_l_per_kwh, 3),
                deviation_pct=round(dev, 1),
                explanation=(
                    f"{generator_name} consumed {row['actual_l_per_kwh']:.2f} L/kWh, "
                    f"{dev:.0f}% above its rated {rated_l_per_kwh:.2f} L/kWh — "
                    "possible fouled injectors, poor load matching, or maintenance need."
                ),
            )
        )
    return findings[-15:]


def detect_sensor_anomalies(
    df: pd.DataFrame,
    value_col: str,
    asset_name: str,
    valid_range: tuple[float, float],
    metric_name: str = "sensor reading",
) -> list[AnomalyFinding]:
    """Deterministic plausibility check for raw sensor values (NaN, out-of-range)."""

    findings: list[AnomalyFinding] = []
    lo, hi = valid_range
    bad = df[(df[value_col].isna()) | (df[value_col] < lo) | (df[value_col] > hi)]
    for _, row in bad.iterrows():
        observed = row[value_col]
        observed_display = float(observed) if pd.notna(observed) else float("nan")
        findings.append(
            AnomalyFinding(
                timestamp=row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
                severity=AnomalySeverity.CRITICAL,
                affected_asset=asset_name,
                metric=metric_name,
                observed_value=observed_display if pd.notna(observed) else -9999.0,
                expected_value=(lo + hi) / 2,
                deviation_pct=100.0,
                explanation=(
                    f"{asset_name} reported an implausible {metric_name} "
                    f"({'missing/NaN' if pd.isna(observed) else f'{observed_display:.1f}'}, "
                    f"expected within [{lo}, {hi}]). Treated as a sensor fault; value rejected from control logic."
                ),
            )
        )
    return findings[-10:]
