import numpy as np
from configs.config import MAX_BATTERY, MAX_SPEED, BATTERY_WARNING, BATTERY_CRITICAL, BATTERY_EMERGENCY, BATTERY_FULL, BATTERY_NORMAL
class UAV:
    def __init__(self, uav_id, position):
        self.id = uav_id
        self.position = np.array(position, dtype=float)
        self.velocity = np.zeros(3)
        self.acceleration = np.zeros(3)
        self.max_speed = MAX_SPEED
        
        #batter
        self.battery_soc = 100.0  # State of Charge in percentage
        self.battery_health = 1.0  # Degradation factor (1.0 = new, 0.0 = unusable)
        self.battery_status = "FULL"  # FSM STATE

        #capabilyty
        self.cpu_capacity = 1.0 #ghz
        self.communication_range = 500.0 #meters
        self.flight_mode = "CRUISE" # CRUISE, ECO, HOVER, EMERGENCY_DESCENT

        #TASKS
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
        modes={
            "CRUISE": MAX_SPEED,
            "ECO": MAX_SPEED * 0.5,
            "HOVER": 0.0,
            "EMERGENCY_DESCENT": MAX_SPEED * 0.3
        } 
        return modes.get(self.flight_mode, MAX_SPEED)
    
    def drain_battery(self, dt):
        drain_rates ={
            "CRUISE": 0.05,
            "ECO": 0.02,
            "HOVER": 0.01,
            "EMERGENCY_DESCENT": 0.03
        }
        rate = drain_rates.get(self.flight_mode, 0.05)
        self.battery_soc -= rate * dt
        self.battery_soc = max(0, self.battery_soc)  # Ensure battery soc doesn't go below 0
        self.update_battery_state()

    def update_battery_state(self):
        soc = self.battery_soc
        if soc >= 95:
            self.battery_status = "FULL"
        elif soc >= 50:
            self.battery_status = "NORMAL"
        elif soc >= 20:
            self.battery_status = "WARNING"
        elif soc >= 10:
            self.battery_status = "CRITICAL"
        else:
            self.battery_status = "EMERGENCY"

    def __repr__(self):
        return f"UAV({self.id}) | Pos: {self.position} | SOC: {self.battery_soc:.1f}% | State: {self.battery_status}"