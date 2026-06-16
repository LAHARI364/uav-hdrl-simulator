# import numpy as np
# from configs.config import MAP_WIDTH, MAP_HEIGHT, GRID_DIVISIONS, REGION_WORKLOAD, NUM_CHARGING_STATIONS, CHARGING_STATION_REGIONS

# class SubRegion:
#     def __init__(self, region_id, x_start, y_start, width, height, workload):
#         self.region_id = region_id
#         self.x_start = x_start
#         self.y_start = y_start
#         self.width = width
#         self.height = height
#         self.workload = workload        # LOW, MEDIUM, HIGH
#         self.task_density = 0.0
#         self.congestion = 0.0
#         self.uav_count = 0

#     def get_center(self):
#         return (self.x_start + self.width/2, self.y_start + self.height/2)

#     def __repr__(self):
#         return f"Region({self.region_id}) | Workload: {self.workload} | Center: {self.get_center()}"


# class Map:
#     def __init__(self):
#         self.width = MAP_WIDTH
#         self.height = MAP_HEIGHT
#         self.divisions = GRID_DIVISIONS
#         self.regions = []
#         self.charging_stations = []
#         self._create_regions()
#         self._place_charging_stations()

#     def _create_regions(self):
#         region_w = self.width / self.divisions
#         region_h = self.height / self.divisions
#         region_id = 0
#         for row in range(self.divisions):
#             for col in range(self.divisions):
#                 x = col * region_w
#                 y = row * region_h
#                 workload = REGION_WORKLOAD[region_id]
#                 self.regions.append(SubRegion(region_id, x, y, region_w, region_h, workload))
#                 region_id += 1

#     def _place_charging_stations(self):
#         for region_id in CHARGING_STATION_REGIONS:
#             center = self.regions[region_id].get_center()
#             self.charging_stations.append({
#                 "region_id": region_id,
#                 "position": center
#             })

#     def get_region_of_position(self, x, y):
#         region_w = self.width / self.divisions
#         region_h = self.height / self.divisions
#         col = int(x // region_w)
#         row = int(y // region_h)
#         col = min(col, self.divisions - 1)
#         row = min(row, self.divisions - 1)
#         return self.regions[row * self.divisions + col]

#     def __repr__(self):
#         return f"Map({self.width}x{self.height}) | {len(self.regions)} regions | {len(self.charging_stations)} charging stations"
import numpy as np
from configs.config import (
    MAP_WIDTH, MAP_HEIGHT, GRID_DIVISIONS,
    REGION_WORKLOAD, NUM_CHARGING_STATIONS,
    CHARGING_STATION_REGIONS, CONGESTION_DECAY,
    MAX_TASKS_PER_REGION
)

class SubRegion:
    def __init__(self, region_id, x_start, y_start, width, height, workload):
        self.region_id   = region_id
        self.x_start     = x_start
        self.y_start     = y_start
        self.width       = width
        self.height      = height
        self.workload    = workload   # "LOW", "MEDIUM", "HIGH"

        # ── Dynamic state ──────────────────────────────────────────
        self.task_density  = 0.0     # normalised [0, 1]
        self.congestion    = 0.0     # normalised [0, 1]
        self.uav_count     = 0
        self.active_tasks  = []      # list of Task objects in this region
        self.weather_severity = 0.0  # filled in by weather engine later

    def register_task(self, task):
        """Call when a task is spawned in this region."""
        if task not in self.active_tasks:
            self.active_tasks.append(task)
        self._refresh_density()

    def remove_task(self, task):
        """Call when a task is DONE or FAILED."""
        if task in self.active_tasks:
            self.active_tasks.remove(task)
        self._refresh_density()

    def _refresh_density(self):
        self.task_density = min(len(self.active_tasks) / MAX_TASKS_PER_REGION, 1.0)

    def update_congestion(self):
        """
        Congestion = blend of task density and UAV crowding, 
        with exponential decay each timestep.
        """
        uav_pressure = min(self.uav_count / 5.0, 1.0)   # normalise over 5 UAVs
        target = 0.6 * self.task_density + 0.4 * uav_pressure
        # Smooth decay towards target
        self.congestion = self.congestion * CONGESTION_DECAY + target * (1 - CONGESTION_DECAY)
        self.congestion = np.clip(self.congestion, 0.0, 1.0)

    def contains(self, x, y):
        return (self.x_start <= x < self.x_start + self.width and
                self.y_start <= y < self.y_start + self.height)

    def get_center(self):
        return (self.x_start + self.width / 2, self.y_start + self.height / 2)

    def __repr__(self):
        return (f"Region({self.region_id}) | Workload: {self.workload} "
                f"| Tasks: {len(self.active_tasks)} "
                f"| Congestion: {self.congestion:.2f} "
                f"| UAVs: {self.uav_count}")


class Map:
    def __init__(self):
        self.width     = MAP_WIDTH
        self.height    = MAP_HEIGHT
        self.divisions = GRID_DIVISIONS
        self.regions   = []
        self.charging_stations = []
        self._create_regions()
        self._place_charging_stations()

    def _create_regions(self):
        region_w  = self.width  / self.divisions
        region_h  = self.height / self.divisions
        region_id = 0
        for row in range(self.divisions):
            for col in range(self.divisions):
                x        = col * region_w
                y        = row * region_h
                workload = REGION_WORKLOAD[region_id]
                self.regions.append(
                    SubRegion(region_id, x, y, region_w, region_h, workload)
                )
                region_id += 1

    def _place_charging_stations(self):
        for region_id in CHARGING_STATION_REGIONS:
            center = self.regions[region_id].get_center()
            self.charging_stations.append({
                "region_id": region_id,
                "position":  center
            })

    def get_region_of_position(self, x, y):
        region_w = self.width  / self.divisions
        region_h = self.height / self.divisions
        col = int(x // region_w)
        row = int(y // region_h)
        col = min(col, self.divisions - 1)
        row = min(row, self.divisions - 1)
        return self.regions[row * self.divisions + col]

    def register_task_to_region(self, task):
        """Register a newly spawned task to its owning subregion."""
        x, y   = task.location
        region = self.get_region_of_position(x, y)
        region.register_task(task)
        task.region_id = region.region_id   # back-reference on task

    def update_uav_counts(self, uavs):
        """Re-count UAVs per region each timestep."""
        for r in self.regions:
            r.uav_count = 0
        for uav in uavs:
            x, y   = uav.position[0], uav.position[1]
            region = self.get_region_of_position(x, y)
            region.uav_count     += 1
            uav.current_region    = region

    def tick(self, uavs):
        """Call once per simulation timestep."""
        self.update_uav_counts(uavs)
        for r in self.regions:
            r.update_congestion()

    def get_congestion_map(self):
        """Returns a 4×4 numpy array of congestion values."""
        grid = np.zeros((self.divisions, self.divisions))
        for r in self.regions:
            row = r.region_id // self.divisions
            col = r.region_id  % self.divisions
            grid[row, col] = r.congestion
        return grid

    def __repr__(self):
        return (f"Map({self.width}x{self.height}) | "
                f"{len(self.regions)} regions | "
                f"{len(self.charging_stations)} charging stations")