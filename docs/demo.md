# SIH Demo Script

A ~5-minute walkthrough exercising every major subsystem, in an order that tells a story (normal → stressed → recovered) rather than just clicking through pages.

## Setup (before judges arrive)

1. Backend running (`uvicorn app.main:app`), database seeded (`python -m app.services.seed`).
2. Frontend running (`npm run dev` or a deployed build).
3. Log out any existing session so you start from `/login`.

## Script

**1. Login (30s)**
Open the app → `/login`. Point out the three demo roles. Log in as **Station Administrator** (`admin@polar-ems.demo` / `admin123`).

**2. Dashboard — normal conditions (60s)**
- KPI row: total generation, demand, solar, wind, battery SOC, fuel, renewable share, temperature — all live from Postgres, not hardcoded.
- Energy Flow diagram: point out the source → bus → battery → load-tier structure and that the numbers update with the KPIs.
- Active Alerts / AI Recommendations panels: whatever the current live state produces — narrate one recommendation's reason/benefit text to show it's generated from the actual numbers, not a canned string.

**3. Energy Monitoring / AI Forecasting (45s)**
- Energy Monitoring: switch the time range (6H/24H/7D/30D) to show real historical data, not a static chart.
- AI Forecasting: show the 1h/6h/24h demand cards with MAE/RMSE/R² — emphasize these are real model outputs, and that the confidence number is derived from the model's own R², not made up.

**4. Simulation Mode — the centerpiece (90s)**
- Go to Simulation Mode. Explain the 8 scenarios exist because a judge will ask "what happens if…".
- Activate **Solar Generation Drop**. Watch the "Recalculated State" block update live (baseline → result arrows), new AI recommendations appear, and the battery/fuel status badges update.
- Point out the safety-constraints block if it appears (e.g. a modifier that would have pushed SOC out of range gets clamped) — this is the deterministic safety layer, separate from the recommendation engine.

**5. Generator Management — quantify the AI's value (30s)**
Show the Baseline vs. AI-Optimized comparison cards (fuel, CO₂, renewable utilization) — read the disclaimer aloud ("simulated/prototype estimate") to preempt the "is this real" question; it's honest by design.

**6. What-If Analysis — protect critical loads under stress (60s)**
Drop **Battery SOC** to ~12% and uncheck **Generator available**, then Run. Show:
- The engine does **not** recommend further battery discharge (it's below the safety floor).
- It instead recommends shedding deferrable/non-critical loads — and never suggests touching a critical load (Life Support, Medical Bay).
This is the strongest single demonstration of the safety-first design.

**7. Load Management (20s)**
Show the 4 priority tiers and, as admin, change one load's tier live via the dropdown — reinforces that Priority-1 loads are structurally protected, not just by convention.

**8. Analytics / Reports (30s)**
Switch Analytics to 7D, show the daily bar charts. Generate a report on the Reports page and hit Print to show the judge-friendly printable output.

**9. Close**
Anomaly Detection page: run a scan live, show a couple of explained findings (observed vs. expected vs. deviation) to round out the "AI across the whole stack" story.

## If something goes wrong live

- **Backend unreachable**: the topbar shows a red "Backend unreachable" indicator and every page renders a retry-able error state instead of crashing — point this out as intentional robustness rather than panicking.
- **A forecast/scenario looks unremarkable**: this is expected some of the time — the synthetic data has real randomness (see `docs/ai-model.md`), it isn't scripted to always look dramatic. Re-running the same scenario will reflect current live state, which changes over time as the demo data continues past "now".
