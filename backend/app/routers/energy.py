from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.energy import EnergyConsumption, EnergyReading, EnergySource, EnergySourceType
from app.services.station_state import build_current_snapshot, get_default_station_id

router = APIRouter(prefix="/energy", tags=["energy"])


@router.get("/current")
def current_energy(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    s = snap.state
    renewable_kw = s.solar_kw + s.wind_kw
    total_generation_kw = renewable_kw + s.generator_output_kw
    renewable_contribution_pct = (renewable_kw / total_generation_kw * 100) if total_generation_kw > 0 else 0.0

    return {
        "station_id": station_id,
        "is_synthetic": snap.station.is_synthetic_demo,
        "timestamp": datetime.utcnow().isoformat(),
        "demand_kw": round(s.demand_kw, 1),
        "total_generation_kw": round(total_generation_kw, 1),
        "solar_kw": round(s.solar_kw, 1),
        "wind_kw": round(s.wind_kw, 1),
        "battery_power_kw": None,  # see /battery/status for signed charge/discharge power
        "generator_output_kw": round(s.generator_output_kw, 1),
        "renewable_contribution_pct": round(renewable_contribution_pct, 1),
        "battery_soc_pct": round(s.battery_soc_pct, 1),
        "fuel_pct": round(s.fuel_pct, 1),
    }


@router.get("/history")
def energy_history(
    hours: int = Query(24, ge=1, le=24 * 90),
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> dict:
    station_id = get_default_station_id(session)
    since = datetime.utcnow() - timedelta(hours=hours)

    consumption = session.exec(
        select(EnergyConsumption)
        .where(EnergyConsumption.station_id == station_id, EnergyConsumption.timestamp >= since)
        .order_by(EnergyConsumption.timestamp)
    ).all()

    solar_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.SOLAR)).first()
    wind_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.WIND)).first()

    solar_readings = {}
    wind_readings = {}
    if solar_src:
        for r in session.exec(select(EnergyReading).where(EnergyReading.source_id == solar_src.id, EnergyReading.timestamp >= since)).all():
            solar_readings[r.timestamp] = r.power_kw
    if wind_src:
        for r in session.exec(select(EnergyReading).where(EnergyReading.source_id == wind_src.id, EnergyReading.timestamp >= since)).all():
            wind_readings[r.timestamp] = r.power_kw

    points = [
        {
            "timestamp": c.timestamp.isoformat(),
            "demand_kw": round(c.demand_kw, 1),
            "solar_kw": round(solar_readings.get(c.timestamp, 0.0), 1),
            "wind_kw": round(wind_readings.get(c.timestamp, 0.0), 1),
            "temperature_celsius": round(c.temperature_celsius, 1) if c.temperature_celsius is not None else None,
        }
        for c in consumption
    ]
    return {"station_id": station_id, "hours": hours, "is_synthetic": True, "points": points}
