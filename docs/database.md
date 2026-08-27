# Database

PostgreSQL, accessed via SQLModel (SQLAlchemy 2 core + Pydantic). Falls back to a local SQLite file automatically when `DATABASE_URL` is unset, so the API can be evaluated with zero external setup — see `backend/app/database.py`.

## Why `create_all()` instead of Alembic migrations

This prototype uses `SQLModel.metadata.create_all(engine)` at startup rather than a migration tool. For a fast-moving hackathon build where the schema changed dozens of times during development, `create_all` is strictly simpler and faster to iterate with, at the cost of not supporting non-destructive schema evolution against data that must be preserved. Listed under README "Future work" as the first thing to add for a production deployment (Alembic is already compatible with SQLModel's declarative classes, so this is additive, not a rewrite).

## Schema (19 tables)

| Table | Purpose | Key relationships |
|---|---|---|
| `users` | Login accounts, role (operator/administrator/scientist) | `station_id → stations.id` |
| `stations` | A research station (name, location, lat/lon, `is_synthetic_demo` flag) | — |
| `energy_sources` | Solar/wind/battery/generator source definitions (rated capacity) | `station_id → stations.id` |
| `energy_readings` | Time-series generation power per source | `station_id`, `source_id → energy_sources.id` |
| `energy_consumption` | Time-series total station demand + temperature | `station_id → stations.id` |
| `batteries` | Battery bank config (capacity, charge/discharge limits, min/max SOC) | `station_id → stations.id` |
| `battery_readings` | Time-series SOC, voltage, current, temperature, power | `battery_id → batteries.id` |
| `generators` | Generator config (rated capacity, fuel tank, consumption rate, CO₂ factor) | `station_id → stations.id` |
| `generator_readings` | Time-series status, output, fuel level, fuel consumed | `generator_id → generators.id` |
| `loads` | Load definitions (name, category, priority 1–4, deferrable flag) | `station_id → stations.id` |
| `load_readings` | Time-series power per load | `load_id → loads.id` |
| `weather_data` | Time-series temperature, wind, irradiance, cloud cover, condition | `station_id → stations.id` |
| `predictions` | Persisted forecast records (type, horizon, predicted vs. actual, model name) | `station_id → stations.id` |
| `anomalies` | Detected anomaly findings (severity, observed/expected/deviation, explanation) | `station_id → stations.id` |
| `optimization_results` | Persisted optimization recommendations | `station_id → stations.id` |
| `alerts` | Threshold/forecast-driven alerts (severity, message, recommended action) | `station_id → stations.id` |
| `simulation_scenarios` | The 8 preset scenario definitions (modifiers as JSON) | — |
| `simulation_runs` | History of simulation activations (full recalculated result, as JSON) | `station_id → stations.id` |
| `reports` | Generated report snapshots (period + summary, as JSON) | `station_id → stations.id` |

## Conventions

- Every table has an integer `id` primary key and appropriate `station_id`/parent foreign keys.
- Every time-series table indexes its `timestamp` column (and `station_id`/parent id) for the range queries the API makes constantly (`WHERE timestamp >= since ORDER BY timestamp`).
- Synthetic vs. potential-future-real data is marked with an `is_synthetic` boolean on every reading table, and `is_synthetic_demo` on `stations` — this is what lets the frontend show "synthetic demo data" labels honestly without a separate data-provenance system.
- JSON-shaped data that doesn't need to be queried by field (scenario modifiers, simulation run results, report summaries) is stored as a serialized JSON string column rather than a native JSON column, to keep the schema fully portable between Postgres and the SQLite fallback used for fast test runs.
