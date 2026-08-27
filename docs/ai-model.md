# AI / ML Methodology

All models live in `backend/app/services/forecasting.py` (demand + renewable forecasting) and `backend/app/services/anomaly_detection.py` (anomaly detection). Both operate on pandas DataFrames and are unit-tested independently of the database (`backend/tests/test_forecasting.py`, `backend/tests/test_anomaly_detection.py`).

## Demand & renewable forecasting

**Problem framing**: direct multi-step forecasting. For each horizon *h* ∈ {1, 6, 24} hours, a separate model predicts the target signal *h* hours ahead of a feature row at time *t*, using only information knowable at *t*:

- Calendar features of the **target** timestamp *t+h* (hour, month, day-of-week, weekend flag, sin/cos-encoded hour & month) — these are known in advance regardless of horizon.
- Lag features of the signal itself as of *t*: `lag_1` (most recent value), `lag_24` (same hour yesterday), `lag_168` (same hour last week), plus a 6-hour rolling mean/std.
- The latest available weather reading as of *t* (temperature for demand; cloud cover, wind speed, irradiance for renewables) as a near-term-conditions proxy.

This is a standard, cheap, explainable approach appropriate for a resource-constrained prototype. A production system would condition on an actual weather *forecast* rather than the latest weather *observation*.

**Models**: `RandomForestRegressor` (n_estimators=200, max_depth=10) for demand; `GradientBoostingRegressor` (n_estimators=200, max_depth=3) for solar/wind. Both from scikit-learn, chosen for being robust to noisy tabular features without extensive tuning — appropriate given the dataset size (~1,440 hourly rows) and time budget.

**Evaluation**: time-ordered 80/20 train/test split (never shuffled, since shuffling a time series leaks future information into training). Reported per-horizon: MAE (kW), RMSE (kW), R². These numbers are surfaced directly in the `/forecast/demand` and `/forecast/renewable` API responses and shown in the **AI Forecasting** page — nothing is cherry-picked or hidden.

**Confidence score** shown in the UI is `clip(0.5 + R²/2, 0.05, 0.98)` — a simple, monotonic mapping from R² to a 0–1 range that's easier to read at a glance than a raw R² (which can be negative).

**Honest limitations**:
- Demand R² on the seeded demo data is typically 0.42–0.48. The synthetic demand series intentionally includes random equipment spikes (`app/services/synthetic_data.py`), which are close to irreducible noise for a calendar+lag model — this is a realistic ceiling, not a bug.
- Wind R² can be low or even negative at the 6h/24h horizons on some seeded runs. Wind is a mean-reverting random walk in the synthetic generator with only mild seasonal bias, so a model with no live weather forecast has little genuine signal to work with at longer horizons — again, reported as-is.
- Solar R² is typically much higher (0.6–0.8) because solar has a strong, learnable seasonal/diurnal structure in the synthetic data.

## Energy condition classification

`classify_energy_condition()` combines a demand forecast, a renewable forecast, and the battery's currently available energy (`(SOC − min_reserve) × capacity`) into **SURPLUS** / **BALANCED** / **DEFICIT** for a stated horizon:

- **SURPLUS** if forecast renewables exceed forecast demand by more than a small margin.
- **DEFICIT** if the forecast shortfall over the horizon exceeds what the battery can supply without breaching its reserve floor.
- **BALANCED** otherwise (battery can cover the gap).

This is deterministic arithmetic on top of the ML forecasts, not a separate model — kept explainable by design.

## Anomaly detection

Two techniques are used, matched to what each signal actually needs (see module docstring in `anomaly_detection.py`):

1. **IsolationForest** (unsupervised, multivariate: `[value, hour_sin, hour_cos]`) for signals whose "normal" range is diurnal, not a fixed threshold — station-wide **consumption** and **battery discharge rate**. The "expected" value reported alongside a flagged point is the median of that signal for the same hour-of-day, so the explanation reads naturally ("31% higher than the ~62 kW typically expected at this time of day").
   - Battery discharge is bimodal (zero while charging, positive while discharging), so the isolation-forest pass only considers actual discharge events (`discharge_kw > 0.5`) — otherwise it flags every ordinary discharge as "anomalous" for merely being non-zero against a mostly-zero baseline. This was found and fixed during integration testing (see `app/routers/anomaly.py`).
2. **Deterministic checks** for signals with a known physical expectation:
   - **Generator fuel efficiency**: actual L/kWh vs. the generator's rated L/kWh; flags when actual exceeds rated by more than a tolerance (default 15%).
   - **Sensor plausibility**: NaN or out-of-physical-range values (e.g. SOC outside [0, 100]) are flagged as sensor faults, independent of any statistical model — this doubles as the "reject invalid sensor values" safety requirement.

Every finding — from either technique — always reports `observed_value`, `expected_value`, `deviation_pct`, and a plain-English `explanation`, per the project's explainability requirement.
