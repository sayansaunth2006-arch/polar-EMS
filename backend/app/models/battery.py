from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Battery(SQLModel, table=True):
    __tablename__ = "batteries"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    name: str
    capacity_kwh: float
    max_charge_rate_kw: float
    max_discharge_rate_kw: float
    min_soc_pct: float = Field(default=15.0)
    max_soc_pct: float = Field(default=100.0)
    cycle_count: int = Field(default=0)
    health_pct: float = Field(default=100.0)


class BatteryReading(SQLModel, table=True):
    __tablename__ = "battery_readings"

    id: int | None = Field(default=None, primary_key=True)
    battery_id: int = Field(foreign_key="batteries.id", index=True)
    timestamp: datetime = Field(index=True)
    soc_pct: float
    voltage_v: float
    current_a: float
    temperature_celsius: float
    power_kw: float  # positive = charging, negative = discharging
    is_synthetic: bool = Field(default=True)
