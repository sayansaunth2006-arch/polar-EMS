from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class LoadPriority(int, Enum):
    CRITICAL = 1
    IMPORTANT = 2
    DEFERRABLE = 3
    NON_CRITICAL = 4


class Load(SQLModel, table=True):
    __tablename__ = "loads"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    name: str
    category: str  # e.g. "life_support", "laboratory", "hvac", "recreation"
    priority: LoadPriority
    rated_power_kw: float
    is_deferrable: bool = Field(default=False)
    is_shed: bool = Field(default=False, description="Whether this load is currently shed by optimization")


class LoadReading(SQLModel, table=True):
    __tablename__ = "load_readings"

    id: int | None = Field(default=None, primary_key=True)
    load_id: int = Field(foreign_key="loads.id", index=True)
    timestamp: datetime = Field(index=True)
    power_kw: float
    is_synthetic: bool = Field(default=True)
