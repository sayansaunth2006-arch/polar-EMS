from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Station(SQLModel, table=True):
    __tablename__ = "stations"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    location: str
    latitude: float
    longitude: float
    timezone: str = Field(default="UTC")
    is_synthetic_demo: bool = Field(
        default=True,
        description="True when the station's data is synthetic/simulated demo data.",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
