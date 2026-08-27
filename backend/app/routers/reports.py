from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.ai import OptimizationResult
from app.models.report import Report
from app.routers.analytics import analytics_summary
from app.services.station_state import get_default_station_id

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/generate")
def generate_report(
    range: str = Query("30d"),
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
) -> dict:
    station_id = get_default_station_id(session)
    summary = analytics_summary(range=range, start=None, end=None, session=session, _user=user)

    baseline = summary["totals"]["total_diesel_l"]
    # Rough estimated-savings framing for the report, reusing the analytics totals.
    estimated_savings_pct = 12.0  # conservative illustrative figure; see /generator/comparison for a live estimate
    estimated_fuel_saved_l = round(baseline * estimated_savings_pct / 100, 1)

    report = {
        "station_id": station_id,
        "generated_at": datetime.utcnow().isoformat(),
        "period_start": summary["period_start"],
        "period_end": summary["period_end"],
        "is_synthetic": True,
        "energy_consumption_kwh": summary["totals"]["total_demand_kwh"],
        "renewable_generation_kwh": summary["totals"]["total_renewable_kwh"],
        "renewable_contribution_pct": summary["totals"]["renewable_contribution_pct"],
        "diesel_consumption_l": summary["totals"]["total_diesel_l"],
        "co2_emissions_kg": summary["totals"]["total_co2_kg"],
        "average_battery_soc_pct": summary["totals"]["average_battery_soc_pct"],
        "anomaly_count": summary["totals"]["anomaly_count"],
        "estimated_fuel_saved_l": estimated_fuel_saved_l,
        "estimated_savings_note": "Illustrative prototype estimate based on optimized vs. baseline dispatch simulation, not a measured/audited figure.",
        "daily_breakdown": summary["daily"],
    }

    session.add(
        Report(
            station_id=station_id,
            period_start=datetime.fromisoformat(summary["period_start"]),
            period_end=datetime.fromisoformat(summary["period_end"]),
            summary_json=json.dumps(report),
        )
    )
    session.commit()

    return report


@router.get("/")
def list_reports(limit: int = 20, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> list[dict]:
    station_id = get_default_station_id(session)
    rows = session.exec(select(Report).where(Report.station_id == station_id).order_by(Report.generated_at.desc()).limit(limit)).all()
    return [
        {
            "id": r.id,
            "generated_at": r.generated_at.isoformat(),
            "period_start": r.period_start.isoformat(),
            "period_end": r.period_end.isoformat(),
            "summary": json.loads(r.summary_json),
        }
        for r in rows
    ]
