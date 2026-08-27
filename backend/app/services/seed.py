"""Seed the database with a demo station and weeks of synthetic history.

Run with: `python -m app.services.seed` (from backend/, venv active).
Idempotent-ish: clears prior demo data for the seeded station before reseeding.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, delete, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database import engine, init_db
from app.models.ai import Anomaly, OptimizationResult, Prediction
from app.models.alert import Alert
from app.models.battery import Battery, BatteryReading
from app.models.energy import EnergyConsumption, EnergyReading, EnergySource, EnergySourceType
from app.models.generator import Generator, GeneratorReading, GeneratorStatus
from app.models.load import Load, LoadPriority, LoadReading
from app.models.simulation import SimulationScenario
from app.models.station import Station
from app.models.user import User, UserRole
from app.models.weather import WeatherData
from app.services.synthetic_data import StationProfile, SyntheticStationSimulator

SEED_HOURS = 24 * 60  # 60 days of hourly history
DEMO_STATION_NAME = "Polar Research Station Alpha"

LOAD_DEFINITIONS = [
    # (name, category, priority, share_of_demand, deferrable)
    ("Life Support & Comms", "life_support", LoadPriority.CRITICAL, 0.18, False),
    ("Critical Heating", "heating", LoadPriority.CRITICAL, 0.22, False),
    ("Medical Bay", "medical", LoadPriority.CRITICAL, 0.05, False),
    ("Research Computing Cluster", "research", LoadPriority.IMPORTANT, 0.15, False),
    ("Laboratory Block A", "laboratory", LoadPriority.IMPORTANT, 0.12, False),
    ("Cold Storage / Refrigeration", "refrigeration", LoadPriority.IMPORTANT, 0.08, False),
    ("Scheduled EV/Equipment Charging", "charging", LoadPriority.DEFERRABLE, 0.08, True),
    ("Non-Urgent Experiments", "experiments", LoadPriority.DEFERRABLE, 0.06, True),
    ("Recreation Room", "recreation", LoadPriority.NON_CRITICAL, 0.04, False),
    ("Optional Lighting", "lighting", LoadPriority.NON_CRITICAL, 0.02, False),
]

SIMULATION_SCENARIOS = [
    {
        "key": "extreme_cold_wave",
        "name": "Extreme Cold Wave",
        "description": "Temperature drops sharply, spiking heating demand station-wide.",
        "modifiers": {"temperature_delta_c": -22, "demand_multiplier": 1.35},
    },
    {
        "key": "solar_drop",
        "name": "Solar Generation Drop",
        "description": "Heavy cloud cover / storm cuts solar generation drastically.",
        "modifiers": {"solar_multiplier": 0.15},
    },
    {
        "key": "high_wind",
        "name": "High Wind Availability",
        "description": "Sustained strong winds boost wind generation well above average.",
        "modifiers": {"wind_multiplier": 1.8},
    },
    {
        "key": "battery_low_soc",
        "name": "Battery Low SOC",
        "description": "Battery state of charge starts near the emergency reserve threshold.",
        "modifiers": {"battery_soc_override_pct": 18},
    },
    {
        "key": "demand_spike",
        "name": "Sudden Demand Increase",
        "description": "Unplanned research activity causes a sharp demand spike.",
        "modifiers": {"demand_multiplier": 1.6},
    },
    {
        "key": "generator_unavailable",
        "name": "Generator Unavailable",
        "description": "Primary diesel generator is offline for emergency repair.",
        "modifiers": {"generator_available": False},
    },
    {
        "key": "low_fuel",
        "name": "Low Fuel Availability",
        "description": "Diesel resupply is delayed; fuel reserves are critically low.",
        "modifiers": {"fuel_override_pct": 8},
    },
    {
        "key": "equipment_failure",
        "name": "Equipment Failure",
        "description": "A renewable inverter fault removes part of the solar array from service.",
        "modifiers": {"solar_multiplier": 0.5},
    },
]

DEMO_USERS = [
    ("operator@polar-ems.demo", "Station Energy Operator", UserRole.OPERATOR, "operator123"),
    ("admin@polar-ems.demo", "Station Administrator", UserRole.ADMIN, "admin123"),
    ("scientist@polar-ems.demo", "Research Scientist", UserRole.SCIENTIST, "scientist123"),
]


def _clear_demo_data(session: Session, station_id: int) -> None:
    battery_ids = session.exec(select(Battery.id).where(Battery.station_id == station_id)).all()
    generator_ids = session.exec(select(Generator.id).where(Generator.station_id == station_id)).all()
    load_ids = session.exec(select(Load.id).where(Load.station_id == station_id)).all()

    if battery_ids:
        session.exec(delete(BatteryReading).where(BatteryReading.battery_id.in_(battery_ids)))  # type: ignore[attr-defined]
    if generator_ids:
        session.exec(delete(GeneratorReading).where(GeneratorReading.generator_id.in_(generator_ids)))  # type: ignore[attr-defined]
    if load_ids:
        session.exec(delete(LoadReading).where(LoadReading.load_id.in_(load_ids)))  # type: ignore[attr-defined]

    for model in (
        EnergyReading,
        EnergyConsumption,
        WeatherData,
        Prediction,
        Anomaly,
        OptimizationResult,
        Alert,
    ):
        session.exec(delete(model).where(model.station_id == station_id))  # type: ignore[attr-defined]
    session.commit()


def seed() -> tuple[int, str]:
    init_db()
    with Session(engine) as session:
        station = session.exec(select(Station).where(Station.name == DEMO_STATION_NAME)).first()
        if station is None:
            station = Station(
                name=DEMO_STATION_NAME,
                location="Simulated Antarctic Plateau",
                latitude=-75.10,
                longitude=123.35,
                timezone="UTC",
                is_synthetic_demo=True,
            )
            session.add(station)
            session.commit()
            session.refresh(station)

        _clear_demo_data(session, station.id)  # type: ignore[arg-type]

        for email, name, role, password in DEMO_USERS:
            existing = session.exec(select(User).where(User.email == email)).first()
            if existing is None:
                session.add(
                    User(
                        email=email,
                        full_name=name,
                        hashed_password=hash_password(password),
                        role=role,
                        station_id=station.id,
                    )
                )
        session.commit()

        profile = StationProfile()
        solar_source = session.exec(
            select(EnergySource).where(EnergySource.station_id == station.id, EnergySource.source_type == EnergySourceType.SOLAR)
        ).first()
        if solar_source is None:
            solar_source = EnergySource(
                station_id=station.id, name="Solar Array", source_type=EnergySourceType.SOLAR, rated_capacity_kw=profile.solar_capacity_kw
            )
            session.add(solar_source)
        wind_source = session.exec(
            select(EnergySource).where(EnergySource.station_id == station.id, EnergySource.source_type == EnergySourceType.WIND)
        ).first()
        if wind_source is None:
            wind_source = EnergySource(
                station_id=station.id, name="Wind Turbine Array", source_type=EnergySourceType.WIND, rated_capacity_kw=profile.wind_capacity_kw
            )
            session.add(wind_source)
        session.commit()
        session.refresh(solar_source)
        session.refresh(wind_source)

        battery = session.exec(select(Battery).where(Battery.station_id == station.id)).first()
        if battery is None:
            battery = Battery(
                station_id=station.id,
                name="Main Battery Bank",
                capacity_kwh=profile.battery_capacity_kwh,
                max_charge_rate_kw=profile.battery_max_charge_kw,
                max_discharge_rate_kw=profile.battery_max_discharge_kw,
                min_soc_pct=profile.battery_min_soc_pct,
                max_soc_pct=profile.battery_max_soc_pct,
                cycle_count=412,
                health_pct=96.5,
            )
            session.add(battery)

        generator = session.exec(select(Generator).where(Generator.station_id == station.id)).first()
        if generator is None:
            generator = Generator(
                station_id=station.id,
                name="Diesel Generator Unit 1",
                rated_capacity_kw=profile.generator_capacity_kw,
                fuel_tank_capacity_l=profile.generator_tank_l,
                fuel_consumption_l_per_kwh=profile.generator_fuel_l_per_kwh,
                runtime_hours=3140.0,
            )
            session.add(generator)
        session.commit()
        session.refresh(battery)
        session.refresh(generator)

        existing_loads = session.exec(select(Load).where(Load.station_id == station.id)).all()
        load_ids: dict[str, int] = {ld.name: ld.id for ld in existing_loads}  # type: ignore[misc]
        if not existing_loads:
            for name, category, priority, _share, deferrable in LOAD_DEFINITIONS:
                ld = Load(
                    station_id=station.id,
                    name=name,
                    category=category,
                    priority=priority,
                    rated_power_kw=round(profile.base_load_kw * 2.2 * _share, 1),
                    is_deferrable=deferrable,
                )
                session.add(ld)
            session.commit()
            existing_loads = session.exec(select(Load).where(Load.station_id == station.id)).all()
            load_ids = {ld.name: ld.id for ld in existing_loads}  # type: ignore[misc]

        for scenario in SIMULATION_SCENARIOS:
            existing_scn = session.exec(select(SimulationScenario).where(SimulationScenario.key == scenario["key"])).first()
            if existing_scn is None:
                session.add(
                    SimulationScenario(
                        key=scenario["key"],
                        name=scenario["name"],
                        description=scenario["description"],
                        modifiers_json=json.dumps(scenario["modifiers"]),
                    )
                )
        session.commit()

        # --- Generate + bulk-insert synthetic history ---
        sim = SyntheticStationSimulator(profile)
        start = datetime.now(timezone.utc) - timedelta(hours=SEED_HOURS)
        df = sim.generate(start.replace(tzinfo=None), SEED_HOURS)

        batch: list = []

        def flush() -> None:
            nonlocal batch
            if batch:
                session.add_all(batch)
                session.commit()
                batch = []

        for _, row in df.iterrows():
            ts = row["timestamp"].to_pydatetime()

            batch.append(EnergyConsumption(station_id=station.id, timestamp=ts, demand_kw=row["demand_kw"], temperature_celsius=row["temperature_c"]))
            batch.append(EnergyReading(station_id=station.id, source_id=solar_source.id, timestamp=ts, power_kw=row["solar_kw"]))
            batch.append(EnergyReading(station_id=station.id, source_id=wind_source.id, timestamp=ts, power_kw=row["wind_kw"]))
            batch.append(
                BatteryReading(
                    battery_id=battery.id,
                    timestamp=ts,
                    soc_pct=row["battery_soc_pct"],
                    voltage_v=round(48 + row["battery_soc_pct"] * 0.08, 2),
                    current_a=round(row["battery_power_kw"] * 1000 / 48, 1),
                    temperature_celsius=round(5 + max(row["temperature_c"], -30) * 0.05, 1),
                    power_kw=row["battery_power_kw"],
                )
            )
            gen_status = GeneratorStatus.RUNNING if row["generator_output_kw"] > 1 else GeneratorStatus.STANDBY
            batch.append(
                GeneratorReading(
                    generator_id=generator.id,
                    timestamp=ts,
                    status=gen_status,
                    output_kw=row["generator_output_kw"],
                    fuel_level_pct=row["generator_fuel_pct"],
                    fuel_consumed_l=row["generator_output_kw"] * profile.generator_fuel_l_per_kwh,
                )
            )
            batch.append(
                WeatherData(
                    station_id=station.id,
                    timestamp=ts,
                    temperature_celsius=row["temperature_c"],
                    wind_speed_mps=row["wind_speed_mps"],
                    solar_irradiance_w_m2=row["solar_irradiance_w_m2"],
                    cloud_cover_pct=row["cloud_cover_pct"],
                    visibility_km=max(0.5, 15 - row["cloud_cover_pct"] / 10),
                    condition=SyntheticStationSimulator.weather_condition(row),
                )
            )

            remaining_share = 1.0
            for name, _cat, _prio, share, _defer in LOAD_DEFINITIONS:
                lid = load_ids[name]
                noisy_share = max(0.01, share * (1 + (hash((name, ts.hour)) % 21 - 10) / 100))
                power = row["demand_kw"] * noisy_share
                batch.append(LoadReading(load_id=lid, timestamp=ts, power_kw=round(power, 2)))

            if len(batch) > 2000:
                flush()

        flush()

        return station.id, station.name  # type: ignore[return-value]


if __name__ == "__main__":
    station_id, station_name = seed()
    print(f"Seeded station '{station_name}' (id={station_id}) with {SEED_HOURS} hours of synthetic history.")
