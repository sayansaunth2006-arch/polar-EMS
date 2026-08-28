from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class GeneratorStatus(str, Enum):
    RUNNING = "running"
    STANDBY = "standby"
    OFF = "off"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


class Generator(SQLModel, table=True):
    __tablename__ = "generators"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    name: str
    rated_capacity_kw: float
    fuel_tank_capacity_l: float
    fuel_consumption_l_per_kwh: float = Field(default=0.32)
    co2_kg_per_l_diesel: float = Field(default=2.68)
    last_maintenance_at: datetime | None = None
    next_maintenance_due_hours: float = Field(default=250.0)
    runtime_hours: float = Field(default=0.0)


class GeneratorReading(SQLModel, table=True):
    __tablename__ = "generator_readings"

    id: int | None = Field(default=None, primary_key=True)
    generator_id: int = Field(foreign_key="generators.id", index=True)
    timestamp: datetime = Field(index=True)
    status: GeneratorStatus
    output_kw: float
    fuel_level_pct: float
    fuel_consumed_l: float = Field(default=0.0)
    is_synthetic: bool = Field(default=True)
