from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.simulation import SimulationRun, SimulationScenario
from app.services.simulation import run_scenario
from app.services.station_state import build_current_snapshot, get_default_station_id

router = APIRouter(prefix="/simulation", tags=["simulation"])


def _outcome_to_dict(baseline_state, outcome) -> dict:
    return {
        "baseline": {
            "demand_kw": round(baseline_state.demand_kw, 1),
            "solar_kw": round(baseline_state.solar_kw, 1),
            "wind_kw": round(baseline_state.wind_kw, 1),
            "battery_soc_pct": round(baseline_state.battery_soc_pct, 1),
            "generator_output_kw": round(baseline_state.generator_output_kw, 1),
            "fuel_pct": round(baseline_state.fuel_pct, 1),
        },
        "result": {
            "demand_kw": round(outcome.state.demand_kw, 1),
            "solar_kw": round(outcome.state.solar_kw, 1),
            "wind_kw": round(outcome.state.wind_kw, 1),
            "battery_soc_pct": round(outcome.state.battery_soc_pct, 1),
            "generator_output_kw": round(outcome.state.generator_output_kw, 1),
            "fuel_pct": round(outcome.state.fuel_pct, 1),
            "battery_status": outcome.battery_status,
            "fuel_status": outcome.fuel_status,
        },
        "recommendations": [
            {
                "action_type": r.action_type.value,
                "recommendation": r.recommendation,
                "reason": r.reason,
                "expected_benefit": r.expected_benefit,
                "priority": r.priority.value,
            }
            for r in outcome.recommendations
        ],
        "comparison": asdict(outcome.comparison),
        "safety_notes": outcome.safety_notes,
    }


@router.get("/scenarios")
def list_scenarios(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> list[dict]:
    rows = session.exec(select(SimulationScenario)).all()
    return [{"key": s.key, "name": s.name, "description": s.description, "modifiers": json.loads(s.modifiers_json)} for s in rows]


@router.post("/run/{scenario_key}")
def run_named_scenario(scenario_key: str, session: Session = Depends(get_session), user=Depends(get_current_user)) -> dict:
    scenario = session.exec(select(SimulationScenario).where(SimulationScenario.key == scenario_key)).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown scenario")

    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    modifiers = json.loads(scenario.modifiers_json)
    outcome = run_scenario(snap.state, modifiers)

    session.add(SimulationRun(station_id=station_id, scenario_key=scenario_key, result_json=json.dumps(_outcome_to_dict(snap.state, outcome))))
    session.commit()

    return {"scenario": {"key": scenario.key, "name": scenario.name, "description": scenario.description}, **_outcome_to_dict(snap.state, outcome)}


class WhatIfRequest(BaseModel):
    temperature_delta_c: float | None = None
    demand_multiplier: float | None = None
    demand_override_kw: float | None = None
    solar_multiplier: float | None = None
    wind_multiplier: float | None = None
    battery_soc_override_pct: float | None = None
    battery_capacity_override_kwh: float | None = None
    generator_available: bool | None = None
    fuel_override_pct: float | None = None
    active_loads: list[str] | None = None


@router.post("/what-if")
def what_if(payload: WhatIfRequest, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    snap = build_current_snapshot(session, station_id)
    modifiers = {k: v for k, v in payload.model_dump().items() if v is not None}
    outcome = run_scenario(snap.state, modifiers)
    return {"modifiers_applied": modifiers, **_outcome_to_dict(snap.state, outcome)}
