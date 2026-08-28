from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    severity: AlertSeverity
    affected_system: str
    message: str
    explanation: str
    recommended_action: str
    is_resolved: bool = Field(default=False)
    resolved_at: datetime | None = None
