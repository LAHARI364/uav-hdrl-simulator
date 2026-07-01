

import numpy as np
from configs.config import (
    BATTERY_CAPACITY_WH, HOVER_BASE_POWER_W, DRAG_LINEAR_COEFF,
    DRAG_CUBIC_COEFF, CPU_POWER_PER_GHZ_W, COMM_BASE_POWER_W,
    VOLTAGE_SAG_COEFF, FLIGHT_MODE_POWER_PROFILE
)



def _profile(mode):
    return FLIGHT_MODE_POWER_PROFILE.get(mode, FLIGHT_MODE_POWER_PROFILE["CRUISE"])


def compute_power_hover(mode):
    return HOVER_BASE_POWER_W * _profile(mode)["hover_coeff"]


def compute_power_movement(speed, mode):
    """Non-linear: linear drag term + cubic drag term."""
    base = DRAG_LINEAR_COEFF * speed + DRAG_CUBIC_COEFF * (speed ** 3)
    return base * _profile(mode)["movement_coeff"]


def compute_power_cpu(uav, mode):
    utilisation = getattr(uav, "cpu_utilization", 0.0)
    return CPU_POWER_PER_GHZ_W * uav.cpu_capacity * utilisation * _profile(mode)["cpu_coeff"]


def compute_power_communication(uav, mode):
    active = 1.0 if getattr(uav, "is_communicating", False) else 0.0
    return COMM_BASE_POWER_W * active * _profile(mode)["comm_coeff"]


def compute_total_power(uav):
    speed = np.linalg.norm(uav.velocity)
    mode  = uav.flight_mode

    p_hover = compute_power_hover(mode)
    p_move  = compute_power_movement(speed, mode)
    p_cpu   = compute_power_cpu(uav, mode)
    p_comm  = compute_power_communication(uav, mode)

    total = p_hover + p_move + p_cpu + p_comm
    return total, {"hover": p_hover, "movement": p_move, "cpu": p_cpu, "comm": p_comm}


def discharge_efficiency(soc_percent, battery_health):
    """
    Non-linear voltage sag: as SOC drops, internal resistance rises,
    so the battery needs to push more effective power to deliver the
    same usable power. Degraded health (battery_health < 1.0) compounds this.
    """
    sag = VOLTAGE_SAG_COEFF * (1.0 - soc_percent / 100.0)
    efficiency = (1.0 - sag) * battery_health
    return max(efficiency, 0.05)   # floor to avoid division blow-up


def update_soc(uav, dt, weather_factor=1.0):
    
    power_consumed, breakdown = compute_total_power(uav)
    power_consumed  = power_consumed * (1.0 + (1.0 - weather_factor) * 0.3)
    efficiency       = discharge_efficiency(uav.battery_soc, uav.battery_health)
    effective_power  = power_consumed / efficiency

    energy_wh   = effective_power * dt / 3600.0           # W·s → Wh
    capacity_wh = BATTERY_CAPACITY_WH * uav.battery_health
    delta_soc   = (energy_wh / capacity_wh) * 100.0

    uav.battery_soc = max(0.0, uav.battery_soc - delta_soc)
    return uav.battery_soc, breakdown