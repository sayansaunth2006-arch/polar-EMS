from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class EnergySourceType(str, Enum):
    SOLAR = "solar"
    WIND = "wind"
    BATTERY = "battery"
    GENERATOR = "generator"


class EnergySource(SQLModel, table=True):
    __tablename__ = "energy_sources"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    name: str
    source_type: EnergySourceType
    rated_capacity_kw: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnergyReading(SQLModel, table=True):
    """Time-series generation reading per energy source."""

    __tablename__ = "energy_readings"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    source_id: int = Field(foreign_key="energy_sources.id", index=True)
    timestamp: datetime = Field(index=True)
    power_kw: float
    is_synthetic: bool = Field(default=True)


class EnergyConsumption(SQLModel, table=True):
    """Aggregate station-wide consumption time-series."""

    __tablename__ = "energy_consumption"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    timestamp: datetime = Field(index=True)
    demand_kw: float
    temperature_celsius: float | None = None
    is_synthetic: bool = Field(default=True)
