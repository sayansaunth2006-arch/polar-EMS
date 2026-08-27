from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="stations.id", index=True)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    period_start: datetime
    period_end: datetime
    summary_json: str  # serialized aggregate metrics used to render the report
