import numpy as np
from configs.config import (
    MAX_BATTERY, MAX_SPEED, BATTERY_WARNING, BATTERY_CRITICAL,
    BATTERY_EMERGENCY, BATTERY_FULL, BATTERY_NORMAL, UAV_CPU_GHZ
)
from power.battery_engine import update_soc


class UAV:
    def __init__(self, uav_id, position):
        self.id = uav_id
        self.position = np.array(position, dtype=float)
        self.velocity = np.zeros(3)
        self.acceleration = np.zeros(3)
        self.max_speed = MAX_SPEED

        # battery
        self.battery_soc = 100.0        # State of Charge in percentage
        self.battery_health = 1.0       # Degradation factor (1.0 = new, 0.0 = unusable)
        self.battery_status = "FULL"    # FSM STATE
        self.last_power_breakdown = {}  # set after each drain_battery() call (Phase 5)
        self.is_charging = False    # True from the moment it heads to a station
        self.target_station = None  # locked-in station while charging

        # capability
        self.cpu_capacity = UAV_CPU_GHZ            # GHz
        self.cpu_utilization = 0.0         # fraction [0,1] of cpu_capacity in use (Phase 5)
        self.communication_range = 500.0   # meters
        self.is_communicating = False      # True while an active CommLink is open (Phase 5)
        self.flight_mode = "CRUISE"  # CRUISE, ECO, HOVER, HIGH_SPEED, EMERGENCY_DESCENT

        # tasks
        self.task_queue = []
        self.current_task = None
        self.current_region = None

    def update_position(self, dt):
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

    def move_towards(self, target, dt):
        target = np.array(target, dtype=float)
        direction = target - self.position
        distance = np.linalg.norm(direction)
        if distance < 1.0:
            return
        direction /= distance
        speed = self._get_speed_by_mood()
        self.velocity = direction * speed
        self.update_position(dt)

    def _get_speed_by_mood(self):
        modes = {
            "CRUISE": MAX_SPEED,
            "ECO": MAX_SPEED * 0.5,
            "HOVER": 0.0,
            "HIGH_SPEED": MAX_SPEED * 1.5,
            "EMERGENCY_DESCENT": MAX_SPEED * 0.3
        }
        return modes.get(self.flight_mode, MAX_SPEED)

    def drain_battery(self, dt, weather_factor=1.0):
        new_soc, breakdown = update_soc(self, dt, weather_factor)
        self.last_power_breakdown = breakdown
        self.update_battery_state()
        return new_soc, breakdown

    def update_battery_state(self):
        soc = self.battery_soc
        if soc >= BATTERY_FULL:
            self.battery_status = "FULL"
        elif soc >= BATTERY_NORMAL:
            self.battery_status = "NORMAL"
        elif soc >= BATTERY_WARNING:
            self.battery_status = "WARNING"
        elif soc >= BATTERY_CRITICAL:
            self.battery_status = "CRITICAL"
        else:
            self.battery_status = "EMERGENCY"

    def __repr__(self):
        return (f"UAV({self.id}) | Pos: {self.position} | "
                f"SOC: {self.battery_soc:.1f}% | State: {self.battery_status} | "
                f"Mode: {self.flight_mode}")
    