# Optimization Methodology

`backend/app/services/optimization.py` is a **deterministic, explainable rules engine** — not a trained model or black-box optimizer. This is a deliberate design choice, not a shortcut: energy dispatch for a station with life-support and medical loads needs recommendations a human operator (or a hackathon judge) can audit line-by-line, and a rules engine is far easier to safety-review than an opaque policy network in the time available for this prototype.

## Inputs

A `StationState` dataclass: current + predicted demand, current solar/wind output + predicted renewable total, battery SOC/capacity/limits, generator availability/capacity/output, fuel level, and the current load list (name, priority tier, power, deferrable flag). Built once per request by `services/station_state.py` from the latest DB readings + the forecasting service, so the optimizer always sees a consistent snapshot.

## Objectives, in priority order

Implemented as an ordered decision tree in `generate_recommendations()`:

1. **Protect critical loads** — never appears as a shed target; only deferrable/non-critical loads are ever recommended for shedding, and only when battery + generator genuinely cannot cover the shortfall.
2. **Maximize renewable utilization** — a renewable surplus (net generation − demand > threshold) recommends charging the battery instead of curtailing the excess.
3. **Minimize diesel consumption** — a shortfall is covered by battery discharge first, generator only for what battery can't cover.
4. **Minimize unnecessary battery cycling** — the engine only recommends discharge when there's an actual shortfall to cover, and only charge when there's an actual surplus (a small dead-zone, ±1 kW, avoids chattering when demand ≈ generation).
5. **Maintain battery reserve** — discharge is only recommended while battery status is `NORMAL`; at `WARNING`/`CRITICAL` the engine instead recommends generator start or load shedding, and separately flags "avoid further battery discharge".
6. **Reduce CO₂ emissions** — a direct consequence of (2) and (3); also reported explicitly via the baseline-vs-optimized CO₂ comparison.
7. **Maintain energy reliability** — fuel-level warnings surface even without an immediate deficit, so operators get advance notice before a real emergency.

## Explainability contract

Every `Recommendation` carries four fields, always populated from the actual numbers that triggered it (not templated placeholders):

```python
Recommendation(
    action_type=ActionType.START_GENERATOR,
    recommendation="Start generator to cover the remaining 38 kW deficit.",
    reason="Battery reserve is insufficient or already near its minimum safety "
           "threshold; predicted 24h demand of 62 kW cannot be met by "
           "renewables + battery alone.",
    expected_benefit="Maintains reliable supply to all load tiers, including critical loads.",
    priority=RecommendationPriority.HIGH,
)
```

The frontend's Optimization page renders `recommendation` / `reason` / `expected_benefit` verbatim, and every card is explicitly labeled `kind: "ai_recommendation"` in the API response — distinct from a "control command" (see below).

## Safety layer (the AI cannot override this)

`services/safety.py` is deliberately independent of the optimization engine — it doesn't call it and isn't called by it in a way that lets the optimizer bypass it. `apply_safety_constraints()` clamps any `StationState` (including one produced by a what-if/simulation modifier) to hard limits *before* recommendations are generated from it:

- Battery SOC clamped to `[min_soc_pct, max_soc_pct]` — a modifier that sets SOC to -50% or 150% is clamped to the real floor/ceiling first.
- Generator output clamped to `rated_capacity_kw`.
- Sensor values outside a plausible range, or missing, are rejected rather than trusted (`validate_sensor_value`).
- `should_use_deterministic_fallback(confidence)` flags when a forecast's confidence is too low to drive dispatch decisions, so a bad prediction degrades to conservative behavior instead of an aggressive one.

The API distinguishes an **AI RECOMMENDATION** (advisory text, `kind: "ai_recommendation"`) from an **ACTUAL CONTROL COMMAND** conceptually throughout the codebase — hardware actuation is out of scope for this prototype (see README limitations), but the boundary where real control would be wired in is exactly `apply_safety_constraints()`.

## Baseline vs. AI-optimized comparison

`compare_baseline_vs_optimized()` computes two dispatch strategies against the *same* current state:

- **Baseline**: generator covers 100% of whatever demand renewables don't (`max(demand − renewable, 0)`), no forecast- or battery-aware behavior.
- **Optimized**: battery covers as much of the shortfall as it safely can (bounded by max discharge rate and available energy above the reserve floor) before the generator engages.

The difference in fuel (`fuel_l_per_kwh × generator_kw × hours`) and CO₂ (`fuel_l × co2_kg_per_l`) is reported as an **estimate**, always labeled as a simulation/prototype figure — see README "Honesty notes". When the battery is already at its reserve floor (available energy = 0), baseline and optimized correctly converge to the same number — this is expected physics, not a bug (observed during integration testing on the Generator Management page).

## Simulation & what-if

`services/simulation.py` applies a dict of modifiers (`temperature_delta_c`, `demand_multiplier`, `solar_multiplier`, `wind_multiplier`, `battery_soc_override_pct`, `generator_available`, `fuel_override_pct`, `active_loads`) to a copy of the current `StationState`, then re-runs the exact same `apply_safety_constraints()` → `generate_recommendations()` → `compare_baseline_vs_optimized()` pipeline used for the live dashboard. Simulation Mode's 8 preset scenarios (Extreme Cold Wave, Solar Generation Drop, High Wind Availability, Battery Low SOC, Sudden Demand Increase, Generator Unavailable, Low Fuel Availability, Equipment Failure) are just named modifier presets stored in the `simulation_scenarios` table — the recalculation logic is identical to What-If Analysis, which takes the same modifiers directly from user-controlled sliders.
