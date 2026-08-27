from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.ai import Anomaly, AnomalySeverity as DbAnomalySeverity
from app.models.battery import Battery, BatteryReading
from app.models.energy import EnergyConsumption
from app.models.generator import Generator, GeneratorReading
from app.services.anomaly_detection import (
    detect_generator_inefficiency,
    detect_sensor_anomalies,
    detect_via_isolation_forest,
)
from app.services.station_state import get_default_station_id
import pandas as pd

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


@router.post("/scan")
def run_anomaly_scan(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    """Runs detection over the last 14 days and persists new findings."""
    station_id = get_default_station_id(session)
    since = datetime.utcnow() - timedelta(days=14)

    cons = session.exec(select(EnergyConsumption).where(EnergyConsumption.station_id == station_id, EnergyConsumption.timestamp >= since)).all()
    df_cons = pd.DataFrame([{"timestamp": c.timestamp, "demand_kw": c.demand_kw} for c in cons])

    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    batt_readings = session.exec(select(BatteryReading).where(BatteryReading.battery_id == battery.id, BatteryReading.timestamp >= since)).all()
    df_batt = pd.DataFrame([{"timestamp": b.timestamp, "discharge_kw": max(-b.power_kw, 0)} for b in batt_readings])

    generator = session.exec(select(Generator).where(Generator.station_id == station_id)).first()
    gen_readings = session.exec(select(GeneratorReading).where(GeneratorReading.generator_id == generator.id, GeneratorReading.timestamp >= since)).all()
    df_gen = pd.DataFrame([{"timestamp": g.timestamp, "output_kw": g.output_kw, "fuel_consumed_l": g.fuel_consumed_l} for g in gen_readings])

    # Discharge rate is bimodal (zero while charging, positive while discharging); scoring the
    # full series against an hour-of-day median would flag ordinary discharge events just for
    # being non-zero. Restrict the isolation-forest pass to actual discharge events so a finding
    # means "unusually large discharge for this time of day", not "battery discharged at all".
    df_batt_discharging = df_batt[df_batt["discharge_kw"] > 0.5]

    findings = []
    findings += detect_via_isolation_forest(df_cons, "demand_kw", "Station Total Demand", "consumption")
    findings += detect_via_isolation_forest(df_batt_discharging, "discharge_kw", battery.name, "discharge rate")
    findings += detect_generator_inefficiency(df_gen, generator.fuel_consumption_l_per_kwh, generator.name)
    findings += detect_sensor_anomalies(df_cons, "demand_kw", "Station Total Demand", (0, 1000))
    findings += detect_sensor_anomalies(df_batt.rename(columns={"discharge_kw": "value"}), "value", battery.name, (0, battery.max_discharge_rate_kw * 1.05))

    saved = 0
    for f in findings:
        exists = session.exec(
            select(Anomaly).where(Anomaly.station_id == station_id, Anomaly.timestamp == f.timestamp, Anomaly.affected_asset == f.affected_asset, Anomaly.metric == f.metric)
        ).first()
        if exists:
            continue
        session.add(
            Anomaly(
                station_id=station_id,
                timestamp=f.timestamp,
                severity=DbAnomalySeverity(f.severity.value),
                affected_asset=f.affected_asset,
                metric=f.metric,
                observed_value=f.observed_value,
                expected_value=f.expected_value,
                deviation_pct=f.deviation_pct,
                explanation=f.explanation,
            )
        )
        saved += 1
    session.commit()
    return {"scanned_findings": len(findings), "new_anomalies_saved": saved}


@router.get("/")
def list_anomalies(
    resolved: bool | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[dict]:
    station_id = get_default_station_id(session)
    query = select(Anomaly).where(Anomaly.station_id == station_id)
    if resolved is not None:
        query = query.where(Anomaly.is_resolved == resolved)
    query = query.order_by(Anomaly.timestamp.desc()).limit(limit)
    rows = session.exec(query).all()
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "severity": a.severity.value,
            "affected_asset": a.affected_asset,
            "metric": a.metric,
            "observed_value": a.observed_value,
            "expected_value": a.expected_value,
            "deviation_pct": a.deviation_pct,
            "explanation": a.explanation,
            "is_resolved": a.is_resolved,
        }
        for a in rows
    ]


@router.post("/{anomaly_id}/resolve")
def resolve_anomaly(anomaly_id: int, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    anomaly = session.get(Anomaly, anomaly_id)
    if anomaly is None:
        return {"error": "not_found"}
    anomaly.is_resolved = True
    session.add(anomaly)
    session.commit()
    return {"id": anomaly.id, "is_resolved": True}
