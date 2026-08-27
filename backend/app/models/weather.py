from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class WeatherData(SQLModel, table=True):
    __tablename__ = "weather_data"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    timestamp: datetime = Field(index=True)
    temperature_celsius: float
    wind_speed_mps: float
    solar_irradiance_w_m2: float
    cloud_cover_pct: float
    visibility_km: float
    condition: str  # e.g. "clear", "overcast", "blizzard", "polar_night"
    is_synthetic: bool = Field(default=True)
