"""Builds the current StationState snapshot (+ cached ML models) from the DB.

Centralizing this here means the dashboard, optimization, simulation, and
what-if endpoints all derive from exactly the same live data and forecasts,
instead of duplicating query/feature logic per router.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select

from app.models.battery import Battery, BatteryReading
from app.models.energy import EnergyConsumption, EnergyReading, EnergySource, EnergySourceType
from app.models.generator import Generator, GeneratorReading
from app.models.load import Load, LoadReading
from app.models.station import Station
from app.models.weather import WeatherData
from app.services.forecasting import TimeSeriesForecaster, build_demand_forecaster, build_renewable_forecaster
from app.services.optimization import LoadState, StationState

# Simple process-lifetime model cache keyed by station id. Retraining on every
# request would make the API unusably slow; a production system would retrain
# on a schedule instead of "once per process".
_MODEL_CACHE: dict[int, dict[str, TimeSeriesForecaster]] = {}


def get_history_frames(session: Session, station_id: int, hours: int = 24 * 60):
    since = datetime.utcnow() - timedelta(hours=hours)

    cons = session.exec(
        select(EnergyConsumption).where(EnergyConsumption.station_id == station_id, EnergyConsumption.timestamp >= since).order_by(EnergyConsumption.timestamp)
    ).all()
    weather = session.exec(
        select(WeatherData).where(WeatherData.station_id == station_id, WeatherData.timestamp >= since).order_by(WeatherData.timestamp)
    ).all()
    solar_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.SOLAR)).first()
    wind_src = session.exec(select(EnergySource).where(EnergySource.station_id == station_id, EnergySource.source_type == EnergySourceType.WIND)).first()
    solar_readings = session.exec(select(EnergyReading).where(EnergyReading.source_id == solar_src.id, EnergyReading.timestamp >= since).order_by(EnergyReading.timestamp)).all() if solar_src else []
    wind_readings = session.exec(select(EnergyReading).where(EnergyReading.source_id == wind_src.id, EnergyReading.timestamp >= since).order_by(EnergyReading.timestamp)).all() if wind_src else []

    df_cons = pd.DataFrame([{"timestamp": c.timestamp, "demand_kw": c.demand_kw, "temperature_celsius": c.temperature_celsius or 0.0} for c in cons])
    df_weather = pd.DataFrame(
        [{"timestamp": w.timestamp, "cloud_cover_pct": w.cloud_cover_pct, "wind_speed_mps": w.wind_speed_mps, "solar_irradiance_w_m2": w.solar_irradiance_w_m2} for w in weather]
    )
    df_solar = pd.DataFrame([{"timestamp": r.timestamp, "solar_kw": r.power_kw} for r in solar_readings])
    df_wind = pd.DataFrame([{"timestamp": r.timestamp, "wind_kw": r.power_kw} for r in wind_readings])
    if not df_solar.empty and not df_weather.empty:
        df_solar = df_solar.merge(df_weather, on="timestamp", how="left").ffill().bfill()
    if not df_wind.empty and not df_weather.empty:
        df_wind = df_wind.merge(df_weather, on="timestamp", how="left").ffill().bfill()

    return df_cons, df_weather, df_solar, df_wind, solar_src, wind_src


def get_or_train_models(session: Session, station_id: int) -> dict[str, TimeSeriesForecaster]:
    if station_id in _MODEL_CACHE:
        return _MODEL_CACHE[station_id]

    df_cons, _df_weather, df_solar, df_wind, _s, _w = get_history_frames(session, station_id)
    models: dict[str, TimeSeriesForecaster] = {}
    if not df_cons.empty:
        models["demand"] = build_demand_forecaster(df_cons)
    if not df_solar.empty:
        models["solar"] = build_renewable_forecaster(df_solar, "solar_kw")
    if not df_wind.empty:
        models["wind"] = build_renewable_forecaster(df_wind, "wind_kw")

    _MODEL_CACHE[station_id] = models
    return models


def invalidate_model_cache(station_id: int | None = None) -> None:
    if station_id is None:
        _MODEL_CACHE.clear()
    else:
        _MODEL_CACHE.pop(station_id, None)


@dataclass
class StationSnapshot:
    station: Station
    battery: Battery
    generator: Generator
    state: StationState
    latest_weather: WeatherData | None
    history: pd.DataFrame  # recent consumption history, for charts


def build_current_snapshot(session: Session, station_id: int, forecast_horizon_hours: int = 1) -> StationSnapshot:
    station = session.get(Station, station_id)
    if station is None:
        raise ValueError(f"Station {station_id} not found")

    battery = session.exec(select(Battery).where(Battery.station_id == station_id)).first()
    generator = session.exec(select(Generator).where(Generator.station_id == station_id)).first()

    df_cons, df_weather, df_solar, df_wind, solar_src, wind_src = get_history_frames(session, station_id, hours=24 * 14)
    if df_cons.empty:
        raise ValueError("No historical data available for this station; run the seed script first.")

    latest_cons = df_cons.iloc[-1]
    latest_battery = session.exec(select(BatteryReading).where(BatteryReading.battery_id == battery.id).order_by(BatteryReading.timestamp.desc())).first()
    latest_gen = session.exec(select(GeneratorReading).where(GeneratorReading.generator_id == generator.id).order_by(GeneratorReading.timestamp.desc())).first()
    latest_weather = session.exec(select(WeatherData).where(WeatherData.station_id == station_id).order_by(WeatherData.timestamp.desc())).first()

    latest_solar_kw = float(df_solar.iloc[-1]["solar_kw"]) if not df_solar.empty else 0.0
    latest_wind_kw = float(df_wind.iloc[-1]["wind_kw"]) if not df_wind.empty else 0.0

    models = get_or_train_models(session, station_id)
    predicted_demand_kw = float(latest_cons["demand_kw"])
    predicted_renewable_kw = latest_solar_kw + latest_wind_kw
    if "demand" in models and forecast_horizon_hours in models["demand"].models:
        predicted_demand_kw = models["demand"].predict(df_cons, forecast_horizon_hours).predicted_value_kw
    if "solar" in models and forecast_horizon_hours in models["solar"].models:
        predicted_solar = models["solar"].predict(df_solar, forecast_horizon_hours).predicted_value_kw
    else:
        predicted_solar = latest_solar_kw
    if "wind" in models and forecast_horizon_hours in models["wind"].models:
        predicted_wind = models["wind"].predict(df_wind, forecast_horizon_hours).predicted_value_kw
    else:
        predicted_wind = latest_wind_kw
    predicted_renewable_kw = predicted_solar + predicted_wind

    loads = session.exec(select(Load).where(Load.station_id == station_id)).all()
    load_states: list[LoadState] = []
    for ld in loads:
        latest_reading = session.exec(select(LoadReading).where(LoadReading.load_id == ld.id).order_by(LoadReading.timestamp.desc())).first()
        load_states.append(
            LoadState(
                name=ld.name,
                priority=int(ld.priority),
                power_kw=float(latest_reading.power_kw) if latest_reading else 0.0,
                is_deferrable=ld.is_deferrable,
            )
        )

    state = StationState(
        demand_kw=float(latest_cons["demand_kw"]),
        predicted_demand_kw=predicted_demand_kw,
        solar_kw=latest_solar_kw,
        wind_kw=latest_wind_kw,
        predicted_renewable_kw=predicted_renewable_kw,
        battery_soc_pct=float(latest_battery.soc_pct) if latest_battery else 50.0,
        battery_capacity_kwh=battery.capacity_kwh,
        battery_min_soc_pct=battery.min_soc_pct,
        battery_max_soc_pct=battery.max_soc_pct,
        battery_max_charge_kw=battery.max_charge_rate_kw,
        battery_max_discharge_kw=battery.max_discharge_rate_kw,
        generator_available=True,
        generator_capacity_kw=generator.rated_capacity_kw,
        generator_output_kw=float(latest_gen.output_kw) if latest_gen else 0.0,
        fuel_pct=float(latest_gen.fuel_level_pct) if latest_gen else 100.0,
        co2_kg_per_l=generator.co2_kg_per_l_diesel,
        fuel_l_per_kwh=generator.fuel_consumption_l_per_kwh,
        loads=load_states,
    )

    return StationSnapshot(station=station, battery=battery, generator=generator, state=state, latest_weather=latest_weather, history=df_cons)


def get_default_station_id(session: Session) -> int:
    station = session.exec(select(Station)).first()
    if station is None:
        raise ValueError("No station found; run `python -m app.services.seed` first.")
    return station.id  # type: ignore[return-value]
