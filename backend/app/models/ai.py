from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class PredictionType(str, Enum):
    DEMAND = "demand"
    SOLAR = "solar"
    WIND = "wind"


class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    prediction_type: PredictionType
    generated_at: datetime = Field(index=True)
    target_timestamp: datetime = Field(index=True)
    horizon_hours: float
    predicted_value_kw: float
    actual_value_kw: float | None = None
    model_name: str
    confidence: float = Field(default=0.7)


class AnomalySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Anomaly(SQLModel, table=True):
    __tablename__ = "anomalies"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    timestamp: datetime = Field(index=True)
    severity: AnomalySeverity
    affected_asset: str
    metric: str
    observed_value: float
    expected_value: float
    deviation_pct: float
    explanation: str
    is_resolved: bool = Field(default=False)


class OptimizationResult(SQLModel, table=True):
    __tablename__ = "optimization_results"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    generated_at: datetime = Field(index=True)
    recommendation: str
    reason: str
    expected_benefit: str
    action_type: str  # e.g. "battery_discharge", "start_generator", "shed_load"
    priority: str  # low / medium / high / critical
    is_applied: bool = Field(default=False)
