# API Reference

Full interactive documentation (auto-generated from the FastAPI/Pydantic schemas) is available at **`/docs`** (Swagger UI) and **`/redoc`** on a running backend, plus the raw OpenAPI JSON at `/openapi.json`. This page is a human-readable index.

All endpoints except `/health` and `/auth/*` require a `Authorization: Bearer <token>` header, obtained from `/auth/login`. Role-gated endpoints (currently `PATCH /loads/{id}`) require the `administrator` role and return `403` otherwise.

| Domain | Endpoint | Method | Notes |
|---|---|---|---|
| System | `/health` | GET | No auth required |
| Auth | `/auth/login` | POST | JSON `{email, password}` → JWT |
| Auth | `/auth/token` | POST | OAuth2 form login (for the `/docs` Authorize button) |
| Auth | `/auth/me` | GET | Current user profile |
| Stations | `/stations/` | GET | List stations |
| Stations | `/stations/{id}` | GET | Station detail |
| Energy | `/energy/current` | GET | Live demand/generation/renewable-share snapshot |
| Energy | `/energy/history` | GET | `?hours=` time series for charts |
| Battery | `/battery/status` | GET | SOC, power, temperature, health, estimated runtime |
| Battery | `/battery/history` | GET | `?hours=` SOC/power time series |
| Generator | `/generator/status` | GET | Output, fuel, maintenance status |
| Generator | `/generator/history` | GET | `?hours=` output/fuel time series + period totals |
| Generator | `/generator/comparison` | GET | Baseline vs. AI-optimized fuel/CO₂ estimate |
| Loads | `/loads/` | GET | All loads with current power, grouped by priority in the UI |
| Loads | `/loads/{id}` | PATCH | **Admin only.** Change a load's priority tier |
| Weather | `/weather/current` | GET | Latest synthetic (or live, if configured) reading |
| Weather | `/weather/history` | GET | `?hours=` time series |
| Forecast | `/forecast/demand` | GET | 1h/6h/24h demand predictions + MAE/RMSE/R² |
| Forecast | `/forecast/renewable` | GET | Solar/wind predictions + energy condition classification |
| Anomaly | `/anomaly/scan` | POST | Runs detection over the last 14 days, persists new findings |
| Anomaly | `/anomaly/` | GET | `?resolved=` list findings |
| Anomaly | `/anomaly/{id}/resolve` | POST | Mark resolved |
| Optimization | `/optimization/recommendations` | GET | Current AI recommendations with reason/benefit/priority |
| Optimization | `/optimization/baseline-comparison` | GET | Same comparison as `/generator/comparison` |
| Alerts | `/alerts/generate` | POST | Evaluate thresholds + forecasts, create new alerts |
| Alerts | `/alerts/` | GET | `?resolved=` list alerts |
| Alerts | `/alerts/{id}/resolve` | POST | Mark resolved |
| Simulation | `/simulation/scenarios` | GET | List the 8 preset scenarios |
| Simulation | `/simulation/run/{key}` | POST | Apply a preset scenario, return recalculated state |
| Simulation | `/simulation/what-if` | POST | Apply arbitrary modifiers (JSON body), return recalculated state |
| Analytics | `/analytics/summary` | GET | `?range=24h\|7d\|30d\|custom&start=&end=` totals + daily breakdown |
| Reports | `/reports/generate` | GET | `?range=` generate + persist a report |
| Reports | `/reports/` | GET | List previously generated reports |

## Error shape

Errors follow FastAPI's default `{"detail": "message"}` shape with the appropriate status code (`401` unauthenticated/expired, `403` insufficient role, `404` not found, `422` validation error). The frontend's `ApiError` class (`frontend/src/lib/api.ts`) normalizes all of these into a single message shown in the UI's error states, plus a distinct message for network/timeout failures.

## Known simplification

Several composite endpoints (e.g. `/optimization/recommendations`, `/simulation/run/{key}`) return a plain `dict` rather than a dedicated Pydantic `response_model`, so their exact shape is documented here and in `frontend/src/lib/api.ts`'s TypeScript interfaces rather than fully reflected in the OpenAPI schema. `/auth/*` and simple GETs (`/stations/`, etc.) do use full Pydantic/SQLModel response types. Tightening every endpoint to an explicit response model is listed under README "Future work".
