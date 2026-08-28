from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.database import get_session
from app.models.weather import WeatherData
from app.services.station_state import get_default_station_id

router = APIRouter(prefix="/weather", tags=["weather"])
settings = get_settings()


@router.get("/current")
def current_weather(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    """Returns the latest synthetic weather reading. A real provider can be
    plugged in later by setting WEATHER_API_KEY and swapping this query for
    a live API call — the response shape is designed to stay stable."""
    station_id = get_default_station_id(session)
    latest = session.exec(select(WeatherData).where(WeatherData.station_id == station_id).order_by(WeatherData.timestamp.desc())).first()
    if latest is None:
        return {"source": "synthetic", "available": False}
    return {
        "source": "synthetic" if not settings.weather_api_key else "live_api",
        "available": True,
        "timestamp": latest.timestamp.isoformat(),
        "temperature_celsius": round(latest.temperature_celsius, 1),
        "wind_speed_mps": round(latest.wind_speed_mps, 1),
        "solar_irradiance_w_m2": round(latest.solar_irradiance_w_m2, 1),
        "cloud_cover_pct": round(latest.cloud_cover_pct, 1),
        "visibility_km": round(latest.visibility_km, 1),
        "condition": latest.condition,
    }


@router.get("/history")
def weather_history(hours: int = Query(24, ge=1, le=24 * 90), session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = session.exec(
        select(WeatherData).where(WeatherData.station_id == station_id, WeatherData.timestamp >= since).order_by(WeatherData.timestamp)
    ).all()
    return {
        "points": [
            {
                "timestamp": r.timestamp.isoformat(),
                "temperature_celsius": round(r.temperature_celsius, 1),
                "wind_speed_mps": round(r.wind_speed_mps, 1),
                "solar_irradiance_w_m2": round(r.solar_irradiance_w_m2, 1),
                "cloud_cover_pct": round(r.cloud_cover_pct, 1),
                "condition": r.condition,
            }
            for r in readings
        ]
    }
