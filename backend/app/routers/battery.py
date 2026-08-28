from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.battery import Battery, BatteryReading
from app.services.safety import battery_status_from_soc, battery_temperature_status
from app.services.station_state import get_default_station_id

router = APIRouter(prefix="/battery", tags=["battery"])


@router.get("/status")
def battery_status(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    latest = session.exec(select(BatteryReading).where(BatteryReading.battery_id == battery.id).order_by(BatteryReading.timestamp.desc())).first()

    soc = latest.soc_pct if latest else 0.0
    status_ = battery_status_from_soc(soc)
    temp_status = battery_temperature_status(latest.temperature_celsius) if latest else "NORMAL"
    est_runtime_hours = None
    if latest and latest.power_kw < 0:
        available_kwh = max((soc - battery.min_soc_pct) / 100 * battery.capacity_kwh, 0)
        est_runtime_hours = round(available_kwh / abs(latest.power_kw), 1) if latest.power_kw != 0 else None

    return {
        "battery_id": battery.id,
        "name": battery.name,
        "capacity_kwh": battery.capacity_kwh,
        "soc_pct": round(soc, 1),
        "status": status_ if temp_status == "NORMAL" else "CRITICAL",
        "voltage_v": round(latest.voltage_v, 2) if latest else None,
        "current_a": round(latest.current_a, 1) if latest else None,
        "temperature_celsius": round(latest.temperature_celsius, 1) if latest else None,
        "temperature_status": temp_status,
        "power_kw": round(latest.power_kw, 1) if latest else 0.0,
        "charge_rate_kw": round(latest.power_kw, 1) if latest and latest.power_kw > 0 else 0.0,
        "discharge_rate_kw": round(abs(latest.power_kw), 1) if latest and latest.power_kw < 0 else 0.0,
        "health_pct": battery.health_pct,
        "cycle_count": battery.cycle_count,
        "min_soc_pct": battery.min_soc_pct,
        "max_soc_pct": battery.max_soc_pct,
        "estimated_runtime_hours": est_runtime_hours,
        "is_synthetic": True,
    }


@router.get("/history")
def battery_history(hours: int = Query(24, ge=1, le=24 * 90), session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = session.exec(
        select(BatteryReading).where(BatteryReading.battery_id == battery.id, BatteryReading.timestamp >= since).order_by(BatteryReading.timestamp)
    ).all()
    return {
        "battery_id": battery.id,
        "points": [
            {"timestamp": r.timestamp.isoformat(), "soc_pct": round(r.soc_pct, 1), "power_kw": round(r.power_kw, 1), "temperature_celsius": round(r.temperature_celsius, 1)}
            for r in readings
        ],
    }
