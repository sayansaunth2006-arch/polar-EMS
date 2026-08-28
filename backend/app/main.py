"""POLAR-EMS FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database import init_db
from app.routers import (
    alerts,
    analytics,
    anomaly,
    auth,
    battery,
    energy,
    forecast,
    generator,
    loads,
    optimization,
    reports,
    simulation,
    stations,
    weather,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("polar_ems")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("POLAR-EMS backend started (env=%s, db=%s)", settings.environment, settings.database_url.split("://")[0])
    yield


app = FastAPI(
    title="POLAR-EMS API",
    description="AI-Driven Smart Energy Management System for Polar Research Stations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(energy.router)
app.include_router(battery.router)
app.include_router(generator.router)
app.include_router(loads.router)
app.include_router(weather.router)
app.include_router(forecast.router)
app.include_router(anomaly.router)
app.include_router(optimization.router)
app.include_router(alerts.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(reports.router)
