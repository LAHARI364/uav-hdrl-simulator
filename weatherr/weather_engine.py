"""Phase 6 (Real-World) — Historical Weather Playback Engine
Replaces Perlin noise with real historical timestamped weather profiles.
"""
import os
import numpy as np

class WeatherSystem:
    def __init__(self, csv_path="data/historical_storm.csv"):
        self.sim_time = 0.0
        self.current_precipitation = 0.0  # mm
        self.current_wind_speed = 0.0     # kph
        
        # Load historical data safely
        if os.path.exists(csv_path):
            # Load columns: timestamp, precipitation, wind_speed
            self.data = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
        else:
            print(f"Warning: {csv_path} not found. Falling back to default clear weather.")
            self.data = np.array([[0.0, 0.0, 0.0]])

    def tick(self, dt):
        """Advance simulation time and look up closest historical data point."""
        self.sim_time += dt
        
        # Find the row in our historical data closest to the current sim_time
        timestamps = self.data[:, 0]
        closest_idx = (np.abs(timestamps - self.sim_time)).argmin()
        
        # Extract real values
        self.current_precipitation = self.data[closest_idx, 1]
        self.current_wind_speed = self.data[closest_idx, 2]

    def get_intensity_at(self, x, y):
        """
        Converts real metrics to a normalized [0, 1] intensity score.
        15mm/hr rain or 70kph wind = max severity (1.0)
        """
        rain_severity = np.clip(self.current_precipitation / 15.0, 0.0, 1.0)
        wind_severity = np.clip(self.current_wind_speed / 70.0, 0.0, 1.0)
        
        # Take the maximum severity threat
        combined_severity = max(rain_severity, wind_severity)
        return float(combined_severity)

    def update_regions(self, world):
        """Write real-world mapped severity into each SubRegion."""
        for region in world.regions:
            cx, cy = region.get_center()
            region.weather_severity = self.get_intensity_at(cx, cy)

    def __repr__(self):
        return (f"RealWorldWeather | t={self.sim_time:.1f}s | "
                f"Rain: {self.current_precipitation:.1f}mm | "
                f"Wind: {self.current_wind_speed:.1f}kph | "
                f"Normalized Severity: {self.get_intensity_at(0,0):.2f}")