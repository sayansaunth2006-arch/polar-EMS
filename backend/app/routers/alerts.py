from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.alert import Alert, AlertSeverity
from app.services.safety import battery_status_from_soc, fuel_status_from_pct
from app.services.station_state import build_current_snapshot, get_default_station_id, get_history_frames, get_or_train_models

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _create_if_new(session: Session, station_id: int, severity: AlertSeverity, affected_system: str, message: str, explanation: str, recommended_action: str) -> bool:
    existing = session.exec(
        select(Alert).where(
            Alert.station_id == station_id,
            Alert.affected_system == affected_system,
            Alert.message == message,
            Alert.is_resolved == False,  # noqa: E712
        )
    ).first()
    if existing:
        return False
    session.add(
        Alert(
            station_id=station_id,
            severity=severity,
            affected_system=affected_system,
            message=message,
            explanation=explanation,
            recommended_action=recommended_action,
        )
    )
    return True


@router.post("/generate")
def generate_alerts(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    """Evaluate current + forecast state against thresholds and create alerts."""
    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    state = snap.state

    created = 0
    battery_status = battery_status_from_soc(state.battery_soc_pct)
    if battery_status != "NORMAL":
        created += _create_if_new(
            session,
            station_id,
            AlertSeverity.CRITICAL if battery_status == "CRITICAL" else AlertSeverity.WARNING,
            "Battery",
            f"Battery SOC at {state.battery_soc_pct:.0f}%, {battery_status.lower()} threshold reached.",
            f"State of charge has fallen to {state.battery_soc_pct:.0f}%, at or below the configured {battery_status.lower()} reserve threshold.",
            "Reduce battery discharge; prioritize generator or renewable coverage; avoid further deferrable load growth.",
        )

    fuel_status = fuel_status_from_pct(state.fuel_pct)
    if fuel_status != "NORMAL" and state.generator_output_kw > 0:
        created += _create_if_new(
            session,
            station_id,
            AlertSeverity.CRITICAL if fuel_status == "CRITICAL" else AlertSeverity.WARNING,
            "Generator",
            f"Generator fuel at {state.fuel_pct:.0f}%, {fuel_status.lower()} threshold reached.",
            f"Diesel fuel reserve has fallen to {state.fuel_pct:.0f}%.",
            "Schedule fuel resupply and minimize non-essential generator runtime until resupplied.",
        )

    # Forecast-based: predicted renewable drop vs recent average.
    df_cons, _w, df_solar, df_wind, _ss, _ws = get_history_frames(session, station_id, hours=24 * 7)
    models = get_or_train_models(session, station_id)
    if "solar" in models and 6 in models["solar"].models and not df_solar.empty:
        pred = models["solar"].predict(df_solar, 6).predicted_value_kw
        recent_avg = df_solar["solar_kw"].tail(24 * 3).mean()
        if recent_avg > 5 and pred < recent_avg * 0.4:
            created += _create_if_new(
                session,
                station_id,
                AlertSeverity.WARNING,
                "Solar",
                "Renewable generation expected to decrease sharply over the next 6 hours.",
                f"Solar forecast for +6h is {pred:.0f} kW, well below the recent 3-day average of {recent_avg:.0f} kW.",
                "Pre-charge battery now while renewables are available; review deferrable load schedule.",
            )

    net_kw = state.demand_kw - (state.solar_kw + state.wind_kw)
    if net_kw > state.generator_capacity_kw + 20:
        created += _create_if_new(
            session,
            station_id,
            AlertSeverity.CRITICAL,
            "Station Load",
            "Demand exceeds combined renewable + generator capacity.",
            f"Current demand ({state.demand_kw:.0f} kW) minus renewables ({state.solar_kw + state.wind_kw:.0f} kW) exceeds generator rated capacity ({state.generator_capacity_kw:.0f} kW).",
            "Shed deferrable and non-critical loads immediately to protect critical systems.",
        )

    session.commit()
    return {"alerts_created": created}


@router.get("/")
def list_alerts(resolved: bool | None = None, limit: int = 50, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> list[dict]:
    station_id = get_default_station_id(session)
    query = select(Alert).where(Alert.station_id == station_id)
    if resolved is not None:
        query = query.where(Alert.is_resolved == resolved)
    query = query.order_by(Alert.timestamp.desc()).limit(limit)
    rows = session.exec(query).all()
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "severity": a.severity.value,
            "affected_system": a.affected_system,
            "message": a.message,
            "explanation": a.explanation,
            "recommended_action": a.recommended_action,
            "is_resolved": a.is_resolved,
        }
        for a in rows
    ]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    alert = session.get(Alert, alert_id)
    if alert is None:
        return {"error": "not_found"}
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    session.add(alert)
    session.commit()
    return {"id": alert.id, "is_resolved": True}
