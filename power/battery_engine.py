
import numpy as np
from configs import config


def compute_total_power(uav):
    profile = config.FLIGHT_MODE_PROFILE.get(uav.flight_mode, config.FLIGHT_MODE_PROFILE["CRUISE"])

    p_hover = config.HOVER_BASE_POWER_W * profile["hover_coeff"]

    speed = float(np.linalg.norm(uav.velocity))
    p_move = config.DRAG_LINEAR_COEFF * speed + config.DRAG_CUBIC_COEFF * (speed ** 3)

    p_cpu = (
        config.CPU_POWER_PER_GHZ_W
        * uav.cpu_capacity
        * uav.cpu_utilization
        * profile["cpu_coeff"]
    )

    p_comm = config.COMM_BASE_POWER_W * profile["comm_coeff"] if uav.is_communicating else 0.0

    total_power = p_hover + p_move + p_cpu + p_comm
    breakdown = {
        "hover": p_hover,
        "movement": p_move,
        "cpu": p_cpu,
        "comm": p_comm,
        "total": total_power,
    }
    return total_power, breakdown


def discharge_efficiency(soc, health):
    efficiency = 1.0 - config.VOLTAGE_SAG_COEFF * (1.0 - soc / 100.0) / max(health, 1e-6)
    return max(efficiency, 0.5)


def update_soc(uav, dt, weather_factor=1.0):
    total_power, breakdown = compute_total_power(uav)

    # Bad weather (weather_factor -> 0 means bad) increases drain by up to 30%.
    weather_penalty = 1.0 + 0.3 * (1.0 - weather_factor)
    effective_power = total_power * weather_penalty

    efficiency = discharge_efficiency(uav.battery_soc, uav.battery_health)
    effective_power = effective_power / efficiency

    # W * s -> Wh -> percentage of BATTERY_CAPACITY_WH
    energy_wh = effective_power * dt / 3600.0
    pct_drain = (energy_wh / config.BATTERY_CAPACITY_WH) * 100.0

    new_soc = max(uav.battery_soc - pct_drain, 0.0)
    breakdown["weather_penalty"] = weather_penalty
    breakdown["efficiency"] = efficiency
    breakdown["pct_drain"] = pct_drain
    return new_soc, breakdown
