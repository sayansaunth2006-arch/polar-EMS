from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.deps import get_current_user
from app.database import get_session
from app.services.forecasting import classify_energy_condition
from app.services.station_state import get_history_frames, get_default_station_id, get_or_train_models

router = APIRouter(prefix="/forecast", tags=["forecast"])

HORIZONS = [1, 6, 24]


@router.get("/demand")
def forecast_demand(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    df_cons, _w, _s, _wd, _ss, _ws = get_history_frames(session, station_id)
    models = get_or_train_models(session, station_id)

    if "demand" not in models:
        return {"available": False, "reason": "Not enough historical data to train a forecasting model."}

    forecasts = []
    for h in HORIZONS:
        if h in models["demand"].models:
            result = models["demand"].predict(df_cons, h)
            forecasts.append(
                {
                    "horizon_hours": h,
                    "predicted_demand_kw": result.predicted_value_kw,
                    "confidence": round(result.confidence, 2),
                    "model_name": result.model_name,
                    "metrics": result.metrics.as_dict(),
                }
            )

    actual_recent = [
        {"timestamp": row.timestamp.isoformat(), "demand_kw": round(row.demand_kw, 1)}
        for row in df_cons.tail(48).itertuples()
    ]

    return {
        "available": True,
        "model_type": "RandomForestRegressor",
        "is_synthetic_training_data": True,
        "forecasts": forecasts,
        "recent_actual": actual_recent,
    }


@router.get("/renewable")
def forecast_renewable(session: Session = Depends(get_session), _user=Depends(get_current_user)) -> dict:
    station_id = get_default_station_id(session)
    df_cons, _w, df_solar, df_wind, _ss, _ws = get_history_frames(session, station_id)
    models = get_or_train_models(session, station_id)

    result = {"available": True, "is_synthetic_training_data": True, "solar": [], "wind": []}

    for key, df, target_col in (("solar", df_solar, "solar_kw"), ("wind", df_wind, "wind_kw")):
        if key not in models or df.empty:
            continue
        for h in HORIZONS:
            if h in models[key].models:
                r = models[key].predict(df, h)
                result[key].append(
                    {
                        "horizon_hours": h,
                        "predicted_kw": r.predicted_value_kw,
                        "confidence": round(r.confidence, 2),
                        "metrics": r.metrics.as_dict(),
                    }
                )

    # Energy condition classification for the 6h horizon, using latest battery reserve.
    from app.models.battery import Battery, BatteryReading
    from sqlmodel import select

    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    latest_batt = session.exec(select(BatteryReading).where(BatteryReading.battery_id == battery.id).order_by(BatteryReading.timestamp.desc())).first()
    available_kwh = max(((latest_batt.soc_pct if latest_batt else 50) - battery.min_soc_pct) / 100 * battery.capacity_kwh, 0.0)

    demand_forecasts = get_or_train_models(session, station_id).get("demand")
    predicted_demand_6h = demand_forecasts.predict(df_cons, 6).predicted_value_kw if demand_forecasts and 6 in demand_forecasts.models else float(df_cons["demand_kw"].iloc[-1])
    predicted_solar_6h = next((f["predicted_kw"] for f in result["solar"] if f["horizon_hours"] == 6), 0.0)
    predicted_wind_6h = next((f["predicted_kw"] for f in result["wind"] if f["horizon_hours"] == 6), 0.0)

    condition = classify_energy_condition(
        predicted_demand_kw=predicted_demand_6h,
        predicted_renewable_kw=predicted_solar_6h + predicted_wind_6h,
        battery_available_kwh=available_kwh,
        horizon_hours=6,
    )
    result["energy_condition_6h"] = condition.value
    return result
