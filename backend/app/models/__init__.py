"""SQLModel entity registry — import every model module so
SQLModel.metadata sees all tables before create_all() runs."""

from app.models.user import User  # noqa: F401
from app.models.station import Station  # noqa: F401
from app.models.energy import EnergySource, EnergyReading, EnergyConsumption  # noqa: F401
from app.models.battery import Battery, BatteryReading  # noqa: F401
from app.models.generator import Generator, GeneratorReading  # noqa: F401
from app.models.load import Load, LoadReading  # noqa: F401
from app.models.weather import WeatherData  # noqa: F401
from app.models.ai import Prediction, OptimizationResult, Anomaly  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.simulation import SimulationScenario, SimulationRun  # noqa: F401
from app.models.report import Report  # noqa: F401
