# Architecture

## Overview

POLAR-EMS is a conventional three-tier app: a Next.js frontend, a FastAPI backend, and PostgreSQL — plus an AI/decision layer inside the backend that the rest of the system consumes through plain REST endpoints (no separate ML service, no message queue; deliberately simple for a prototype at this scale).

```
┌─────────────────┐      HTTPS/JSON       ┌──────────────────────────────┐
│  Next.js (3000)  │ ───────────────────▶ │  FastAPI (8000)               │
│  16 dashboard    │ ◀─────────────────── │  ┌────────────────────────┐  │
│  pages, App      │      JWT bearer       │  │ routers/*  (REST)      │  │
│  Router          │                       │  └───────────┬────────────┘  │
└─────────────────┘                       │              │               │
                                            │  ┌───────────▼────────────┐  │
                                            │  │ services/               │  │
                                            │  │  synthetic_data.py      │  │
                                            │  │  forecasting.py (ML)    │  │
                                            │  │  anomaly_detection.py   │  │
                                            │  │  optimization.py        │  │
                                            │  │  safety.py              │  │
                                            │  │  simulation.py          │  │
                                            │  │  station_state.py       │  │
                                            │  └───────────┬────────────┘  │
                                            │  ┌───────────▼────────────┐  │
                                            │  │ models/ (SQLModel)      │  │
                                            │  └───────────┬────────────┘  │
                                            └──────────────┼───────────────┘
                                                            ▼
                                                  ┌────────────────────┐
                                                  │  PostgreSQL          │
                                                  └────────────────────┘
```

## Backend layering

- **`routers/`** — one file per domain (`energy`, `battery`, `generator`, `loads`, `weather`, `forecast`, `anomaly`, `optimization`, `alerts`, `simulation`, `analytics`, `reports`, `auth`, `stations`). Routers are thin: they fetch a DB session, call into `services/`, and shape the response. No business logic lives in a router.
- **`services/station_state.py`** is the composition root: it builds a single `StationState` snapshot (current demand/generation/battery/generator/loads + near-term forecasts) from the database, and every consumer (dashboard `/energy/current`, `/optimization/recommendations`, `/simulation/run/*`, `/simulation/what-if`) derives from that *same* snapshot logic — so the dashboard and the simulation engine never disagree about what "now" means.
- **`services/safety.py`** has zero dependency on any other service — it's pure, deterministic threshold logic (battery SOC clamp, generator capacity clamp, sensor-range validation) that every other service is expected to run its output through before anything is called a "control command".
- **`services/optimization.py`** and **`services/simulation.py`** are also pure functions of a `StationState` in, `Recommendation[]`/`SimulationOutcome` out — no DB access — which is what makes them straightforward to unit-test with hand-built edge-case states (see `tests/test_optimization.py`, `tests/test_simulation.py`).
- **`services/forecasting.py`** and **`services/anomaly_detection.py`** are pure functions of a pandas DataFrame in, typed results out — also unit-tested independently of the database and the API layer.
- **`models/`** is the only place SQLModel table classes live; `database.py` owns the engine/session and `SQLModel.metadata.create_all()` for table creation (see `docs/database.md` for why this project uses `create_all` instead of Alembic).

## Frontend layering

- **`lib/api.ts`** is the single source of truth for every backend call and every response type the frontend uses — no page calls `fetch()` directly. Errors are normalized into a typed `ApiError` so every page can render the same loading/error/empty states.
- **`hooks/useApiQuery.ts`** is a small generic data-fetching hook (loading/error/refetch/optional polling) used by all 15 authenticated pages, so pages don't each reimplement fetch-on-mount + error handling.
- **`components/ui/`** is a hand-built, Tailwind-styled component kit (Card, StatTile, StatusBadge, Button, States, Toaster) rather than a full shadcn install, to keep the dependency surface small for a prototype; the visual language matches shadcn's conventions (composable, unstyled-by-default primitives) so migrating later is straightforward.
- **`lib/store.ts`** holds auth session state (JWT + role) in a small Zustand store persisted to `localStorage`; `components/layout/AuthGuard.tsx` redirects to `/login` when there's no token.

## Why these specific choices

- **SQLModel over raw SQLAlchemy + separate Pydantic models**: one class defines both the DB table and the API-facing shape, which keeps a fast-moving prototype's models from drifting out of sync — at the cost of some flexibility a larger production system would want back (see `docs/database.md`).
- **A rule-based optimization engine instead of a trained model**: every recommendation must be explainable and safety-reviewable for a hackathon judge in real time; see `docs/optimization.md` for the full rationale.
- **In-process ML model cache instead of a model-serving service**: at this data volume (60 days hourly ≈ 1,440 rows) training takes ~1–3 seconds, which is fast enough to do once per process lifetime and reuse — a real deployment would move this to a scheduled retraining job (see README "Future work").
