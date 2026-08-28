from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.deps import get_current_user, require_role
from app.database import get_session
from app.models.load import Load, LoadPriority, LoadReading
from app.models.user import UserRole
from app.services.station_state import get_default_station_id

router = APIRouter(prefix="/loads", tags=["loads"])


class LoadPriorityUpdate(BaseModel):
    priority: LoadPriority


@router.get("/")
def list_loads(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> list[dict]:
    station_id = get_default_station_id(session)
    loads = session.exec(select(Load).where(Load.station_id == station_id)).all()
    result = []
    for ld in loads:
        latest = session.exec(select(LoadReading).where(LoadReading.load_id == ld.id).order_by(LoadReading.timestamp.desc())).first()
        result.append(
            {
                "id": ld.id,
                "name": ld.name,
                "category": ld.category,
                "priority": int(ld.priority),
                "priority_label": ld.priority.name,
                "rated_power_kw": ld.rated_power_kw,
                "current_power_kw": round(latest.power_kw, 1) if latest else 0.0,
                "is_deferrable": ld.is_deferrable,
                "is_shed": ld.is_shed,
            }
        )
    return result


@router.patch("/{load_id}")
def update_load_priority(
    load_id: int,
    payload: LoadPriorityUpdate,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.ADMIN)),
) -> dict:
    load = session.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=404, detail="Load not found")
    load.priority = payload.priority
    session.add(load)
    session.commit()
    session.refresh(load)
    return {"id": load.id, "name": load.name, "priority": int(load.priority), "priority_label": load.priority.name}
