from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.generator import Generator, GeneratorReading
from app.services.safety import fuel_status_from_pct
from app.services.station_state import build_current_snapshot, get_default_station_id

router = APIRouter(prefix="/generator", tags=["generator"])


@router.get("/status")
def generator_status(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    generator = session.exec(select(Generator).where(Generator.station_id == station_id)).first()
    latest = session.exec(select(GeneratorReading).where(GeneratorReading.generator_id == generator.id).order_by(GeneratorReading.timestamp.desc())).first()

    fuel_pct = latest.fuel_level_pct if latest else 100.0
    return {
        "generator_id": generator.id,
        "name": generator.name,
        "status": latest.status.value if latest else "off",
        "output_kw": round(latest.output_kw, 1) if latest else 0.0,
        "rated_capacity_kw": generator.rated_capacity_kw,
        "fuel_level_pct": round(fuel_pct, 1),
        "fuel_status": fuel_status_from_pct(fuel_pct),
        "fuel_tank_capacity_l": generator.fuel_tank_capacity_l,
        "fuel_consumption_l_per_kwh": generator.fuel_consumption_l_per_kwh,
        "co2_kg_per_l": generator.co2_kg_per_l_diesel,
        "runtime_hours": generator.runtime_hours,
        "next_maintenance_due_hours": generator.next_maintenance_due_hours,
        "maintenance_status": "DUE_SOON" if generator.runtime_hours % generator.next_maintenance_due_hours > generator.next_maintenance_due_hours * 0.9 else "OK",
        "is_synthetic": True,
    }


@router.get("/history")
def generator_history(hours: int = Query(24, ge=1, le=24 * 90), session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    generator = session.exec(select(Generator).where(Generator.station_id == station_id)).first()
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = session.exec(
        select(GeneratorReading).where(GeneratorReading.generator_id == generator.id, GeneratorReading.timestamp >= since).order_by(GeneratorReading.timestamp)
    ).all()
    total_fuel_l = sum(r.fuel_consumed_l for r in readings)
    total_co2_kg = total_fuel_l * generator.co2_kg_per_l_diesel
    return {
        "generator_id": generator.id,
        "total_fuel_consumed_l": round(total_fuel_l, 1),
        "total_co2_kg": round(total_co2_kg, 1),
        "points": [
            {"timestamp": r.timestamp.isoformat(), "output_kw": round(r.output_kw, 1), "fuel_level_pct": round(r.fuel_level_pct, 1), "status": r.status.value}
            for r in readings
        ],
    }


@router.get("/comparison")
def generator_comparison(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    """Baseline (generator-follows-demand) vs AI-optimized dispatch, simulated estimate."""
    from app.services.optimization import compare_baseline_vs_optimized

    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    comparison = compare_baseline_vs_optimized(snap.state)
    result = comparison.__dict__
    result["note"] = "Simulated/prototype estimate based on current forecast state, not a guaranteed real-world saving."
    return result
