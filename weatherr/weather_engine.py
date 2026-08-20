# weatherr/weather_engine.py — full file
"""Phase 6 (Real-World) — Historical Weather Playback Engine
Replaces Perlin noise with real historical timestamped weather profiles.
"""
import os
import numpy as np
from configs.config import WEATHER_SPEEDUP

class WeatherSystem:
    def __init__(self, csv_path="data/historical_storm.csv"):
        self.sim_time = 0.0
        self.current_precipitation = 0.0  # mm
        self.current_wind_speed = 0.0     # kph

        if os.path.exists(csv_path):
            self.data = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
        else:
            print(f"Warning: {csv_path} not found. Falling back to default clear weather.")
            self.data = np.array([[0.0, 0.0, 0.0]])

    def tick(self, dt):
        """Advance simulation time and look up the closest historical
        data point — scaled by WEATHER_SPEEDUP.

        historical_storm.csv is hourly-resolution over a multi-day storm
        (STORM_DURATION_S ~342000s), but the sim only runs for
        TOTAL_SIM_TIME (~500s). Without scaling, sim_time never gets more
        than a few hundred seconds into a ~95-hour dataset, so the very
        first row is always the closest match and weather looks frozen
        for the entire run — WEATHER_SPEEDUP maps sim-time to storm-time
        so the whole historical record plays out inside one simulation.
        """
        self.sim_time += dt
        storm_time = self.sim_time * WEATHER_SPEEDUP

        timestamps = self.data[:, 0]
        closest_idx = (np.abs(timestamps - storm_time)).argmin()

        self.current_precipitation = self.data[closest_idx, 1]
        self.current_wind_speed = self.data[closest_idx, 2]

    def get_intensity_at(self, x, y):
        rain_severity = np.clip(self.current_precipitation / 15.0, 0.0, 1.0)
        wind_severity = np.clip(self.current_wind_speed / 70.0, 0.0, 1.0)
        combined_severity = max(rain_severity, wind_severity)
        return float(combined_severity)

    def update_regions(self, world):
        for region in world.regions:
            cx, cy = region.get_center()
            region.weather_severity = self.get_intensity_at(cx, cy)

    def __repr__(self):
        return (f"RealWorldWeather | t={self.sim_time:.1f}s | "
                f"Rain: {self.current_precipitation:.1f}mm | "
                f"Wind: {self.current_wind_speed:.1f}kph | "
                f"Normalized Severity: {self.get_intensity_at(0,0):.2f}")