"""Synthetic polar research-station data generator.

Produces a physically-plausible (but entirely synthetic) time series for a
polar research station: seasonal solar/wind availability, extreme-cold-driven
heating demand, and a simple rule-based battery/generator dispatch used only
to seed realistic-looking historical data. This is NOT measured data and is
labeled `is_synthetic=True` everywhere it is stored.

Design notes on the physical patterns modeled:
  * Solar irradiance follows a polar-day/polar-night seasonal envelope
    (near-zero around the winter solstice, near-continuous around the
    summer solstice) multiplied by a diurnal bump and cloud attenuation.
  * Wind speed is a mean-reverting random walk with a mild winter bias
    (more frequent storm systems).
  * Temperature follows a seasonal sinusoid (deep negative in polar winter)
    plus diurnal variation and noise.
  * Demand = base hotel load + heating load (driven by how far the
    temperature is below a comfort threshold) + daytime research/occupancy
    load + occasional equipment spikes.
  * Battery/generator dispatch is a simple greedy rule: renewables cover
    load first, battery covers the residual within its power/SOC limits,
    and the generator covers whatever is left, refueling periodically.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


@dataclass
class StationProfile:
    """Static station configuration used to shape the synthetic series."""

    solar_capacity_kw: float = 120.0
    wind_capacity_kw: float = 80.0
    battery_capacity_kwh: float = 400.0
    battery_max_charge_kw: float = 100.0
    battery_max_discharge_kw: float = 100.0
    battery_min_soc_pct: float = 15.0
    battery_max_soc_pct: float = 100.0
    generator_capacity_kw: float = 250.0
    generator_tank_l: float = 20000.0
    generator_fuel_l_per_kwh: float = 0.32
    base_load_kw: float = 45.0
    heating_coefficient_kw_per_degree: float = 1.6
    comfort_temp_c: float = 18.0
    winter_solstice_doy: int = 172  # ~June 21 (Northern-hemisphere-style day-of-year index)
    summer_solstice_doy: int = 355  # ~Dec 21 (Antarctic-station summer)


def _seasonal_daylight_fraction(day_of_year: int, summer_solstice_doy: int) -> float:
    """0 at the depth of polar night, 1 at the height of the midnight-sun summer."""

    angle = 2 * math.pi * (day_of_year - summer_solstice_doy) / 365.25
    raw = math.cos(angle)  # 1 at summer solstice, -1 at winter solstice
    return float(np.clip((raw + 1) / 2, 0.0, 1.0))


def _wind_power_curve(wind_speed_mps: np.ndarray, rated_kw: float) -> np.ndarray:
    """Simplified turbine power curve: cubic ramp, rated plateau, cutout."""

    cut_in, rated_speed, cutout = 3.5, 12.0, 25.0
    power = np.zeros_like(wind_speed_mps)
    ramp = (wind_speed_mps >= cut_in) & (wind_speed_mps < rated_speed)
    power[ramp] = rated_kw * ((wind_speed_mps[ramp] - cut_in) / (rated_speed - cut_in)) ** 3
    plateau = (wind_speed_mps >= rated_speed) & (wind_speed_mps < cutout)
    power[plateau] = rated_kw
    return np.clip(power, 0, rated_kw)


class SyntheticStationSimulator:
    def __init__(self, profile: StationProfile | None = None, seed: int = 42) -> None:
        self.profile = profile or StationProfile()
        self.rng = np.random.default_rng(seed)

    def generate(self, start: datetime, hours: int) -> pd.DataFrame:
        """Generate `hours` of hourly synthetic station data starting at `start`."""

        p = self.profile
        timestamps = pd.date_range(start=start, periods=hours, freq="h")
        n = len(timestamps)
        doy = np.array([t.timetuple().tm_yday for t in timestamps])
        hour_of_day = np.array([t.hour + t.minute / 60 for t in timestamps])

        daylight_frac = np.array([_seasonal_daylight_fraction(d, p.summer_solstice_doy) for d in doy])

        # --- Temperature: seasonal sinusoid + diurnal + noise ---
        seasonal_temp = -35 + 30 * np.array(
            [math.cos(2 * math.pi * (d - p.summer_solstice_doy) / 365.25) * -1 + 1 for d in doy]
        ) / 2
        diurnal_temp = 3 * np.sin(2 * math.pi * (hour_of_day - 14) / 24)
        temp_noise = self.rng.normal(0, 1.5, n)
        temperature = seasonal_temp + diurnal_temp + temp_noise

        # --- Cloud cover: AR(1) mean-reverting process in [0, 1] ---
        cloud = np.zeros(n)
        cloud[0] = self.rng.uniform(0.2, 0.6)
        for i in range(1, n):
            cloud[i] = np.clip(0.85 * cloud[i - 1] + 0.15 * self.rng.uniform(0, 1) + self.rng.normal(0, 0.03), 0, 1)

        # --- Solar irradiance (W/m^2): seasonal envelope * diurnal bump * cloud attenuation ---
        # At high daylight_frac (polar summer / "midnight sun") the sun never fully sets, so
        # night hours still get a low-angle baseline rather than dropping to zero; at low
        # daylight_frac (polar night) irradiance stays near zero even at local noon.
        diurnal_bump = np.clip(np.sin(2 * math.pi * (hour_of_day - 6) / 24), 0, 1)
        effective_factor = daylight_frac * (0.25 + 0.75 * diurnal_bump)
        clear_sky_irradiance = 900 * effective_factor
        irradiance = clear_sky_irradiance * (1 - 0.75 * cloud)
        irradiance = np.clip(irradiance + self.rng.normal(0, 10, n), 0, 1000)

        # --- Wind speed: mean-reverting random walk with winter bias ---
        winter_bias = (1 - daylight_frac) * 2.0
        wind = np.zeros(n)
        wind[0] = 6.0
        for i in range(1, n):
            target = 6.5 + winter_bias[i]
            wind[i] = np.clip(wind[i - 1] + 0.25 * (target - wind[i - 1]) + self.rng.normal(0, 1.1), 0, 30)

        # --- Renewable generation ---
        performance_ratio = 0.78
        solar_kw = np.clip(irradiance / 1000 * p.solar_capacity_kw * performance_ratio, 0, p.solar_capacity_kw)
        wind_kw = _wind_power_curve(wind, p.wind_capacity_kw)

        # --- Demand: base + heating + occupancy/research diurnal + noise + occasional spikes ---
        heating_kw = np.clip(p.comfort_temp_c - temperature, 0, None) * p.heating_coefficient_kw_per_degree / 10
        occupancy = 0.5 + 0.5 * np.clip(np.sin(2 * math.pi * (hour_of_day - 7) / 24), 0, None)
        research_kw = 25 * occupancy
        spikes = (self.rng.uniform(0, 1, n) > 0.97) * self.rng.uniform(10, 40, n)
        demand_noise = self.rng.normal(0, 3, n)
        demand_kw = np.clip(p.base_load_kw + heating_kw + research_kw + spikes + demand_noise, 20, None)

        # --- Simple greedy dispatch simulation for battery/generator/fuel ---
        soc = np.zeros(n)
        battery_power = np.zeros(n)  # + charge, - discharge
        generator_output = np.zeros(n)
        fuel_level_pct = np.zeros(n)
        soc_val = 65.0
        fuel_val = 92.0
        for i in range(n):
            renewable = solar_kw[i] + wind_kw[i]
            residual = demand_kw[i] - renewable

            if residual <= 0:
                # surplus renewables -> charge battery
                charge = min(-residual, p.battery_max_charge_kw)
                max_room_kwh = (p.battery_max_soc_pct - soc_val) / 100 * p.battery_capacity_kwh
                charge = min(charge, max(max_room_kwh, 0))
                soc_val = np.clip(soc_val + charge / p.battery_capacity_kwh * 100, 0, p.battery_max_soc_pct)
                battery_power[i] = charge
                generator_output[i] = 0.0
            else:
                available_kwh = max((soc_val - p.battery_min_soc_pct) / 100 * p.battery_capacity_kwh, 0)
                discharge = min(residual, p.battery_max_discharge_kw, available_kwh)
                soc_val = np.clip(soc_val - discharge / p.battery_capacity_kwh * 100, p.battery_min_soc_pct, 100)
                battery_power[i] = -discharge
                remaining = residual - discharge
                if remaining > 1e-6:
                    generator_output[i] = min(remaining, p.generator_capacity_kw)
                else:
                    generator_output[i] = 0.0

            soc[i] = soc_val

            fuel_used_l = generator_output[i] * p.generator_fuel_l_per_kwh
            fuel_val -= (fuel_used_l / p.generator_tank_l) * 100
            if fuel_val < 15:
                fuel_val = 96.0  # periodic resupply/refuel event
            fuel_level_pct[i] = fuel_val

        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "temperature_c": temperature,
                "wind_speed_mps": wind,
                "solar_irradiance_w_m2": irradiance,
                "cloud_cover_pct": cloud * 100,
                "daylight_fraction": daylight_frac,
                "demand_kw": demand_kw,
                "solar_kw": solar_kw,
                "wind_kw": wind_kw,
                "battery_soc_pct": soc,
                "battery_power_kw": battery_power,
                "generator_output_kw": generator_output,
                "generator_fuel_pct": fuel_level_pct,
            }
        )
        return df

    @staticmethod
    def weather_condition(row: pd.Series) -> str:
        if row["daylight_fraction"] < 0.05:
            return "polar_night"
        if row["cloud_cover_pct"] > 85 and row["wind_speed_mps"] > 15:
            return "blizzard"
        if row["cloud_cover_pct"] > 70:
            return "overcast"
        if row["cloud_cover_pct"] > 35:
            return "partly_cloudy"
        return "clear"
