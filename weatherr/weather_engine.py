"""
weatherr/weather_engine.py
-----------------------------
Replays real historical weather data (if available) to give realistic
storm simulation. Falls back to a synthetic bell-curve storm profile
if the CSV isn't found, so the demo runs standalone without needing
the original data/historical_storm.csv file.
"""

import os
import math
import csv
from configs import config


class WeatherSystem:
    def __init__(self, csv_path="data/historical_storm.csv"):
        self.sim_time = 0.0
        self.current_precipitation = 0.0
        self.current_wind_speed = 0.0
        self.rows = []
        self.using_synthetic = False

        if csv_path and os.path.exists(csv_path):
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.rows.append(
                        {
                            "timestamp": row.get("timestamp"),
                            "precipitation": float(row.get("precipitation", 0.0)),
                            "wind_speed": float(row.get("wind_speed", 0.0)),
                        }
                    )
        if not self.rows:
            self.using_synthetic = True

    def tick(self, dt):
        self.sim_time += dt
        if self.using_synthetic:
            self._update_synthetic()
        else:
            self._update_from_csv()

    def _update_synthetic(self):
        # Bell-curve storm profile peaking at the midpoint of the sim.
        t = self.sim_time
        peak_time = config.TOTAL_SIM_TIME / 2.0
        spread = config.TOTAL_SIM_TIME / 5.0
        intensity = math.exp(-((t - peak_time) ** 2) / (2 * spread ** 2))
        self.current_precipitation = 15.0 * intensity   # up to ~15mm/hr at peak
        self.current_wind_speed = 70.0 * intensity       # up to ~70kph at peak

    def _update_from_csv(self):
        # Find the row closest to current sim_time (rows assumed hourly-indexed
        # by position; sim_time is compressed to loop across the dataset).
        idx = int((self.sim_time / max(config.TOTAL_SIM_TIME, 1e-6)) * (len(self.rows) - 1))
        idx = max(0, min(idx, len(self.rows) - 1))
        row = self.rows[idx]
        self.current_precipitation = row["precipitation"]
        self.current_wind_speed = row["wind_speed"]

    def get_intensity_at(self, x, y):
        rain_severity = min(self.current_precipitation / 15.0, 1.0)
        wind_severity = min(self.current_wind_speed / 70.0, 1.0)
        return max(rain_severity, wind_severity)

    def update_regions(self, world):
        for region in world.regions:
            cx, cy = region.get_center()
            region.weather_severity = self.get_intensity_at(cx, cy)
