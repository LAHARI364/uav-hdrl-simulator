

import numpy as np
from configs import config


class SubRegion:
   

    def __init__(self, region_id, x_start, y_start, width, height, workload):
        self.region_id = region_id
        self.x_start = x_start
        self.y_start = y_start
        self.width = width
        self.height = height
        self.workload = workload            # LOW / MEDIUM / HIGH / CRITICAL (static)
        self.task_density = 0.0             # float [0,1]
        self.congestion = 0.0               # float [0,1]
        self.uav_count = 0
        self.active_tasks = []
        self.weather_severity = 0.0

    def register_task(self, task):
        self.active_tasks.append(task)
        self._refresh_density()

    def remove_task(self, task):
        if task in self.active_tasks:
            self.active_tasks.remove(task)
        self._refresh_density()

    def _refresh_density(self):
        self.task_density = min(
            len(self.active_tasks) / config.MAX_TASKS_PER_REGION, 1.0
        )

    def update_congestion(self):
        uav_pressure = min(self.uav_count / max(config.NUM_UAVS, 1), 1.0)
        target = 0.6 * self.task_density + 0.4 * uav_pressure
        # blend toward target, with mild decay so congestion doesn't snap instantly
        self.congestion = 0.99 * self.congestion + 0.01 * target if self.congestion > target else target

    def contains(self, x, y):
        return (
            self.x_start <= x < self.x_start + self.width
            and self.y_start <= y < self.y_start + self.height
        )

    def get_center(self):
        return (
            self.x_start + self.width / 2.0,
            self.y_start + self.height / 2.0,
        )


class Map:


    def __init__(self):
        self.regions = []
        self.charging_stations = []
        self._create_regions()
        self._place_charging_stations()

    def _create_regions(self):
        divisions = config.GRID_DIVISIONS
        tile_w = config.MAP_WIDTH / divisions
        tile_h = config.MAP_HEIGHT / divisions

        # Workload pattern for a 2x2 grid: mix of levels so the demo shows
        # varied urgency even with only 4 regions.
        workload_pattern = ["HIGH", "MEDIUM", "MEDIUM", "LOW"]

        region_id = 0
        for row in range(divisions):
            for col in range(divisions):
                x_start = col * tile_w
                y_start = row * tile_h
                workload = workload_pattern[region_id % len(workload_pattern)]
                region = SubRegion(region_id, x_start, y_start, tile_w, tile_h, workload)
                self.regions.append(region)
                region_id += 1

        # Populate TASK_ARRIVAL_RATE (region_id -> lambda) from workload labels
        config.TASK_ARRIVAL_RATE = {
            r.region_id: config.WORKLOAD_TO_LAMBDA[r.workload] for r in self.regions
        }

    def _place_charging_stations(self):
        for i, region_id in enumerate(config.CHARGING_STATION_REGIONS):
            region = self.regions[region_id]
            cx, cy = region.get_center()
            self.charging_stations.append(
                {"station_id": i, "region_id": region_id, "position": np.array([cx, cy, 0.0])}
            )

    def get_region_of_position(self, x, y):
        for region in self.regions:
            if region.contains(x, y):
                return region
        # Fallback: clamp to nearest region (shouldn't normally happen)
        return min(
            self.regions,
            key=lambda r: (r.get_center()[0] - x) ** 2 + (r.get_center()[1] - y) ** 2,
        )

    def register_task_to_region(self, task):
        region = self.get_region_of_position(task.location[0], task.location[1])
        task.region_id = region.region_id
        region.register_task(task)

    def update_uav_counts(self, uavs):
        for region in self.regions:
            region.uav_count = 0
        for uav in uavs:
            region = self.get_region_of_position(uav.position[0], uav.position[1])
            region.uav_count += 1
            uav.current_region = region

    def tick(self, uavs):
        self.update_uav_counts(uavs)
        for region in self.regions:
            region.update_congestion()

    def get_congestion_map(self):
        d = config.GRID_DIVISIONS
        arr = np.zeros((d, d))
        for region in self.regions:
            row = region.region_id // d
            col = region.region_id % d
            arr[row, col] = region.congestion
        return arr
