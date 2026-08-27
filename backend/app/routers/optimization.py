from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import get_current_user
from app.database import get_session
from app.services.optimization import compare_baseline_vs_optimized, generate_recommendations
from app.services.safety import battery_status_from_soc, fuel_status_from_pct
from app.services.station_state import build_current_snapshot, get_default_station_id

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.get("/recommendations")
def recommendations(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    recs = generate_recommendations(snap.state)
    return {
        "station_id": station_id,
        "battery_status": battery_status_from_soc(snap.state.battery_soc_pct),
        "fuel_status": fuel_status_from_pct(snap.state.fuel_pct),
        "recommendations": [
            {
                "action_type": r.action_type.value,
                "recommendation": r.recommendation,
                "reason": r.reason,
                "expected_benefit": r.expected_benefit,
                "priority": r.priority.value,
                "kind": "ai_recommendation",
            }
            for r in recs
        ],
    }


@router.get("/baseline-comparison")
def baseline_comparison(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    comparison = compare_baseline_vs_optimized(snap.state)
    result = asdict(comparison) if hasattr(comparison, "__dataclass_fields__") else comparison.__dict__
    result["note"] = "Simulated/prototype estimate — not a guaranteed real-world saving."
    return result
