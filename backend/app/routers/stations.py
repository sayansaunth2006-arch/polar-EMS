from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.deps import get_current_user
from app.database import get_session
from app.models.station import Station

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/")
def list_stations(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> list[Station]:
    return session.exec(select(Station)).all()


@router.get("/{station_id}")
def get_station(station_id: int, session: Session = Depends(get_session), _user=Depends(get_current_user)) -> Station:
    station = session.get(Station, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station
