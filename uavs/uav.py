
import numpy as np
from configs import config
from power import battery_engine


class UAV:
    def __init__(self, uav_id, position):
        self.id = uav_id
        self.position = np.array(position, dtype=float)          # [x, y, z]
        self.velocity = np.zeros(3, dtype=float)
        self.acceleration = np.zeros(3, dtype=float)
        self.max_speed = config.MAX_SPEED

        self.battery_soc = config.MAX_BATTERY
        self.battery_health = 1.0
        self.battery_status = "FULL"

        self.cpu_capacity = config.UAV_CPU_GHZ
        self.cpu_utilization = 0.0
        self.is_communicating = False
        self.communication_range = config.COMM_RANGE

        self.flight_mode = "CRUISE"
        self.task_queue = []
        self.current_task = None
        self.current_region = None
        self.last_power_breakdown = {}
        self.compute_timer = 0.0

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------
    def update_position(self, dt):
        self.velocity += self.acceleration * dt
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = self.velocity / speed * self.max_speed
        self.position += self.velocity * dt

    def move_towards(self, target, dt):
        target = np.array(target, dtype=float)
        if target.shape[0] < 3:
            target = np.append(target, [0.0] * (3 - target.shape[0]))
        direction = target - self.position
        distance = np.linalg.norm(direction)
        if distance < 1e-6:
            self.velocity[:] = 0.0
            return
        direction_unit = direction / distance
        speed = self._get_speed_by_mode()
        self.velocity = direction_unit * speed
        self.update_position(dt)

    def _get_speed_by_mode(self):
        profile = config.FLIGHT_MODE_PROFILE.get(self.flight_mode, config.FLIGHT_MODE_PROFILE["CRUISE"])
        return profile["speed"]

    # ------------------------------------------------------------------
    # Battery
    # ------------------------------------------------------------------
    def drain_battery(self, dt, weather_factor=1.0):
        new_soc, breakdown = battery_engine.update_soc(self, dt, weather_factor)
        self.battery_soc = new_soc
        self.last_power_breakdown = breakdown
        self.update_battery_state()

    def update_battery_state(self):
        soc = self.battery_soc
        if soc <= config.BATTERY_EMERGENCY:
            self.battery_status = "EMERGENCY" if soc > 0 else "DEAD"
        elif soc <= config.BATTERY_CRITICAL:
            self.battery_status = "CRITICAL"
        elif soc <= config.BATTERY_WARNING:
            self.battery_status = "WARNING"
        elif soc <= config.BATTERY_NORMAL:
            self.battery_status = "NORMAL"
        else:
            self.battery_status = "FULL"

    def distance_to(self, point):
        point = np.array(point, dtype=float)
        if point.shape[0] < 3:
            point = np.append(point, [0.0] * (3 - point.shape[0]))
        return float(np.linalg.norm(self.position - point))
