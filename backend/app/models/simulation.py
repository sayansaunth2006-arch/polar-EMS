from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SimulationScenario(SQLModel, table=True):
    __tablename__ = "simulation_scenarios"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)  # e.g. "extreme_cold_wave"
    name: str
    description: str
    # JSON-encoded modifiers applied to baseline state, e.g.
    # {"solar_multiplier": 0.1, "temperature_delta": -25}
    modifiers_json: str


class SimulationRun(SQLModel, table=True):
    __tablename__ = "simulation_runs"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    scenario_key: str
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_json: str  # full recalculated state snapshot, serialized
