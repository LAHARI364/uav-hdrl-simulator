import numpy as np
from configs.config import MAP_WIDTH, MAP_HEIGHT, GRID_DIVISIONS, REGION_WORKLOAD, NUM_CHARGING_STATIONS, CHARGING_STATION_REGIONS

class SubRegion:
    def __init__(self, region_id, x_start, y_start, width, height, workload):
        self.region_id = region_id
        self.x_start = x_start
        self.y_start = y_start
        self.width = width
        self.height = height
        self.workload = workload        # LOW, MEDIUM, HIGH, CRITICAL
        self.task_density = 0.0
        self.congestion = 0.0
        self.uav_count = 0

    def get_center(self):
        return (self.x_start + self.width/2, self.y_start + self.height/2)

    def __repr__(self):
        return f"Region({self.region_id}) | Workload: {self.workload} | Center: {self.get_center()}"


class Map:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.divisions = GRID_DIVISIONS
        self.regions = []
        self.charging_stations = []
        self._create_regions()
        self._place_charging_stations()

    def _create_regions(self):
        region_w = self.width / self.divisions
        region_h = self.height / self.divisions
        region_id = 0
        for row in range(self.divisions):
            for col in range(self.divisions):
                x = col * region_w
                y = row * region_h
                workload = REGION_WORKLOAD[region_id]
                self.regions.append(SubRegion(region_id, x, y, region_w, region_h, workload))
                region_id += 1

    def _place_charging_stations(self):
        for region_id in CHARGING_STATION_REGIONS:
            center = self.regions[region_id].get_center()
            self.charging_stations.append({
                "region_id": region_id,
                "position": center
            })

    def get_region_of_position(self, x, y):
        region_w = self.width / self.divisions
        region_h = self.height / self.divisions
        col = int(x // region_w)
        row = int(y // region_h)
        col = min(col, self.divisions - 1)
        row = min(row, self.divisions - 1)
        return self.regions[row * self.divisions + col]

    def __repr__(self):
        return f"Map({self.width}x{self.height}) | {len(self.regions)} regions | {len(self.charging_stations)} charging stations"