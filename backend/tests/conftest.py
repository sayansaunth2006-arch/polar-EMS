from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.security import hash_password
from app.database import get_session
from app.main import app
from app.models.battery import Battery, BatteryReading
from app.models.energy import EnergyConsumption, EnergyReading, EnergySource, EnergySourceType
from app.models.generator import Generator, GeneratorReading, GeneratorStatus
from app.models.load import Load, LoadPriority, LoadReading
from app.models.simulation import SimulationScenario
from app.models.station import Station
from app.models.user import User, UserRole
from app.models.weather import WeatherData
from app.services.station_state import invalidate_model_cache


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="seeded_station")
def seeded_station_fixture(session: Session):
    """A small, fast synthetic dataset (10 days hourly) for API/integration tests."""
    from app.services.synthetic_data import StationProfile, SyntheticStationSimulator

    station = Station(name="Test Station", location="Test", latitude=-70.0, longitude=10.0)
    session.add(station)
    session.commit()
    session.refresh(station)

    for email, role, pw in [
        ("operator@test.demo", UserRole.OPERATOR, "operator123"),
        ("admin@test.demo", UserRole.ADMIN, "admin123"),
        ("scientist@test.demo", UserRole.SCIENTIST, "scientist123"),
    ]:
        session.add(User(email=email, full_name=email, hashed_password=hash_password(pw), role=role, station_id=station.id))
    session.commit()

    profile = StationProfile()
    solar = EnergySource(station_id=station.id, name="Solar", source_type=EnergySourceType.SOLAR, rated_capacity_kw=profile.solar_capacity_kw)
    wind = EnergySource(station_id=station.id, name="Wind", source_type=EnergySourceType.WIND, rated_capacity_kw=profile.wind_capacity_kw)
    session.add(solar)
    session.add(wind)
    battery = Battery(
        station_id=station.id, name="Test Battery", capacity_kwh=profile.battery_capacity_kwh,
        max_charge_rate_kw=profile.battery_max_charge_kw, max_discharge_rate_kw=profile.battery_max_discharge_kw,
        min_soc_pct=profile.battery_min_soc_pct, max_soc_pct=profile.battery_max_soc_pct,
    )
    generator = Generator(
        station_id=station.id, name="Test Generator", rated_capacity_kw=profile.generator_capacity_kw,
        fuel_tank_capacity_l=profile.generator_tank_l, fuel_consumption_l_per_kwh=profile.generator_fuel_l_per_kwh,
    )
    session.add(battery)
    session.add(generator)
    load1 = Load(station_id=station.id, name="Life Support", category="life_support", priority=LoadPriority.CRITICAL, rated_power_kw=20, is_deferrable=False)
    load2 = Load(station_id=station.id, name="Charging", category="charging", priority=LoadPriority.DEFERRABLE, rated_power_kw=8, is_deferrable=True)
    session.add(load1)
    session.add(load2)

    session.add(SimulationScenario(key="solar_drop", name="Solar Drop", description="test", modifiers_json=json.dumps({"solar_multiplier": 0.1})))
    session.add(SimulationScenario(key="generator_unavailable", name="Generator Unavailable", description="test", modifiers_json=json.dumps({"generator_available": False})))
    session.commit()
    session.refresh(solar)
    session.refresh(wind)
    session.refresh(battery)
    session.refresh(generator)
    session.refresh(load1)
    session.refresh(load2)

    sim = SyntheticStationSimulator(profile, seed=7)
    start = datetime.now(timezone.utc) - timedelta(hours=24 * 10)
    df = sim.generate(start.replace(tzinfo=None), 24 * 10)

    for _, row in df.iterrows():
        ts = row["timestamp"].to_pydatetime()
        session.add(EnergyConsumption(station_id=station.id, timestamp=ts, demand_kw=row["demand_kw"], temperature_celsius=row["temperature_c"]))
        session.add(EnergyReading(station_id=station.id, source_id=solar.id, timestamp=ts, power_kw=row["solar_kw"]))
        session.add(EnergyReading(station_id=station.id, source_id=wind.id, timestamp=ts, power_kw=row["wind_kw"]))
        session.add(
            BatteryReading(
                battery_id=battery.id, timestamp=ts, soc_pct=row["battery_soc_pct"],
                voltage_v=50.0, current_a=1.0, temperature_celsius=5.0, power_kw=row["battery_power_kw"],
            )
        )
        gen_status = GeneratorStatus.RUNNING if row["generator_output_kw"] > 1 else GeneratorStatus.STANDBY
        session.add(
            GeneratorReading(
                generator_id=generator.id, timestamp=ts, status=gen_status, output_kw=row["generator_output_kw"],
                fuel_level_pct=row["generator_fuel_pct"], fuel_consumed_l=row["generator_output_kw"] * profile.generator_fuel_l_per_kwh,
            )
        )
        session.add(
            WeatherData(
                station_id=station.id, timestamp=ts, temperature_celsius=row["temperature_c"], wind_speed_mps=row["wind_speed_mps"],
                solar_irradiance_w_m2=row["solar_irradiance_w_m2"], cloud_cover_pct=row["cloud_cover_pct"], visibility_km=10.0,
                condition=SyntheticStationSimulator.weather_condition(row),
            )
        )
        session.add(LoadReading(load_id=load1.id, timestamp=ts, power_kw=row["demand_kw"] * 0.4))
        session.add(LoadReading(load_id=load2.id, timestamp=ts, power_kw=row["demand_kw"] * 0.1))
    session.commit()

    invalidate_model_cache()
    return station


@pytest.fixture(name="client")
def client_fixture(session: Session, seeded_station):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="operator_token")
def operator_token_fixture(client: TestClient) -> str:
    r = client.post("/auth/login", json={"email": "operator@test.demo", "password": "operator123"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(name="admin_token")
def admin_token_fixture(client: TestClient) -> str:
    r = client.post("/auth/login", json={"email": "admin@test.demo", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture(name="scientist_token")
def scientist_token_fixture(client: TestClient) -> str:
    r = client.post("/auth/login", json={"email": "scientist@test.demo", "password": "scientist123"})
    assert r.status_code == 200
    return r.json()["access_token"]
