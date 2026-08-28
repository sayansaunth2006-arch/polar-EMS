from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.ai import Anomaly
from app.models.battery import Battery, BatteryReading
from app.models.energy import EnergyConsumption, EnergyReading, EnergySource, EnergySourceType
from app.models.generator import Generator, GeneratorReading
from app.services.station_state import get_default_station_id

router = APIRouter(prefix="/analytics", tags=["analytics"])

RANGE_HOURS = {"24h": 24, "7d": 24 * 7, "30d": 24 * 30}


@router.get("/summary")
def analytics_summary(
    range: str = Query("7d", description="24h | 7d | 30d | custom"),
    start: datetime | None = None,
    end: datetime | None = None,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> dict:
    station_id = get_default_station_id(session)

    if range == "custom" and start and end:
        since, until = start, end
    else:
        hours = RANGE_HOURS.get(range, 24 * 7)
        until = datetime.utcnow()
        since = until - timedelta(hours=hours)

    cons = session.exec(
        select(EnergyConsumption).where(EnergyConsumption.station_id == station_id, EnergyConsumption.timestamp >= since, EnergyConsumption.timestamp <= until)
    ).all()
    solar_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.SOLAR)).first()
    wind_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.WIND)).first()
    solar_readings = session.exec(select(EnergyReading).where(EnergyReading.source_id == solar_src.id, EnergyReading.timestamp >= since, EnergyReading.timestamp <= until)).all() if solar_src else []
    wind_readings = session.exec(select(EnergyReading).where(EnergyReading.source_id == wind_src.id, EnergyReading.timestamp >= since, EnergyReading.timestamp <= until)).all() if wind_src else []

    generator = session.exec(select(Generator).where(Generator.station_id == station_id)).first()
    gen_readings = session.exec(select(GeneratorReading).where(GeneratorReading.generator_id == generator.id, GeneratorReading.timestamp >= since, GeneratorReading.timestamp <= until)).all()

    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    batt_readings = session.exec(select(BatteryReading).where(BatteryReading.battery_id == battery.id, BatteryReading.timestamp >= since, BatteryReading.timestamp <= until)).all()

    anomalies_count = session.exec(select(Anomaly).where(Anomaly.station_id == station_id, Anomaly.timestamp >= since, Anomaly.timestamp <= until)).all()

    total_demand_kwh = sum(c.demand_kw for c in cons)  # hourly readings -> kWh == sum of kW
    total_solar_kwh = sum(r.power_kw for r in solar_readings)
    total_wind_kwh = sum(r.power_kw for r in wind_readings)
    total_renewable_kwh = total_solar_kwh + total_wind_kwh
    total_fuel_l = sum(g.fuel_consumed_l for g in gen_readings)
    total_co2_kg = total_fuel_l * generator.co2_kg_per_l_diesel
    renewable_pct = (total_renewable_kwh / total_demand_kwh * 100) if total_demand_kwh else 0.0
    avg_soc = sum(b.soc_pct for b in batt_readings) / len(batt_readings) if batt_readings else 0.0

    # Daily aggregation for trend charts.
    daily: dict[str, dict] = {}
    for c in cons:
        day = c.timestamp.date().isoformat()
        daily.setdefault(day, {"date": day, "demand_kwh": 0.0, "solar_kwh": 0.0, "wind_kwh": 0.0, "fuel_l": 0.0, "co2_kg": 0.0})
        daily[day]["demand_kwh"] += c.demand_kw
    for r in solar_readings:
        day = r.timestamp.date().isoformat()
        daily.setdefault(day, {"date": day, "demand_kwh": 0.0, "solar_kwh": 0.0, "wind_kwh": 0.0, "fuel_l": 0.0, "co2_kg": 0.0})
        daily[day]["solar_kwh"] += r.power_kw
    for r in wind_readings:
        day = r.timestamp.date().isoformat()
        daily.setdefault(day, {"date": day, "demand_kwh": 0.0, "solar_kwh": 0.0, "wind_kwh": 0.0, "fuel_l": 0.0, "co2_kg": 0.0})
        daily[day]["wind_kwh"] += r.power_kw
    for g in gen_readings:
        day = g.timestamp.date().isoformat()
        daily.setdefault(day, {"date": day, "demand_kwh": 0.0, "solar_kwh": 0.0, "wind_kwh": 0.0, "fuel_l": 0.0, "co2_kg": 0.0})
        daily[day]["fuel_l"] += g.fuel_consumed_l
        daily[day]["co2_kg"] += g.fuel_consumed_l * generator.co2_kg_per_l_diesel

    return {
        "range": range,
        "period_start": since.isoformat(),
        "period_end": until.isoformat(),
        "is_synthetic": True,
        "totals": {
            "total_demand_kwh": round(total_demand_kwh, 1),
            "total_solar_kwh": round(total_solar_kwh, 1),
            "total_wind_kwh": round(total_wind_kwh, 1),
            "total_renewable_kwh": round(total_renewable_kwh, 1),
            "renewable_contribution_pct": round(renewable_pct, 1),
            "total_diesel_l": round(total_fuel_l, 1),
            "total_co2_kg": round(total_co2_kg, 1),
            "average_battery_soc_pct": round(avg_soc, 1),
            "anomaly_count": len(anomalies_count),
            "efficiency_kwh_per_l": round(total_demand_kwh / total_fuel_l, 2) if total_fuel_l else None,
        },
        "daily": sorted(
            (
                {**d, "demand_kwh": round(d["demand_kwh"], 1), "solar_kwh": round(d["solar_kwh"], 1), "wind_kwh": round(d["wind_kwh"], 1), "fuel_l": round(d["fuel_l"], 1), "co2_kg": round(d["co2_kg"], 1)}
                for d in daily.values()
            ),
            key=lambda d: d["date"],
        ),
    }
