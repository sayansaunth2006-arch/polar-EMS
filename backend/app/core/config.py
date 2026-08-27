"""Central application configuration, loaded from environment variables.

All tunable thresholds referenced throughout the app (battery safety limits,
alert thresholds, optimization defaults) live here so they are never
hard-coded redundantly across services/routers.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "POLAR-EMS"
    environment: str = "development"

    # SQLite fallback keeps the API runnable with zero external setup when
    # DATABASE_URL is not configured (e.g. quick local evaluation).
    database_url: str = "sqlite:///./polar_ems.db"

    jwt_secret_key: str = "change-me-in-production-dev-only-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    cors_origins: str = "http://localhost:3000"

    weather_api_key: str = ""

    # --- Centralized safety / operating thresholds -----------------------
    battery_soc_min_reserve_pct: float = 15.0  # hard safety floor
    battery_soc_warning_pct: float = 20.0
    battery_soc_critical_pct: float = 10.0
    battery_soc_max_pct: float = 100.0
    battery_temp_max_celsius: float = 45.0
    battery_temp_min_celsius: float = -20.0

    generator_min_fuel_warning_pct: float = 25.0
    generator_min_fuel_critical_pct: float = 10.0

    forecast_confidence_low_threshold: float = 0.55

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
