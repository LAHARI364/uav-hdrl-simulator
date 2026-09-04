import numpy as np
from configs.config import CHARGING_RATE, CHARGING_RELEASE_SOC, SAFE_ZONE_MIN_UAV_SEPARATION

FAILURE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY")


def _release_task(uav):
    if uav.current_task is not None:
        uav.current_task.status = "PENDING"
        uav.current_task.assigned_uav = None
        if uav.current_task in uav.task_queue:
            uav.task_queue.remove(uav.current_task)
        uav.current_task = None
    uav.compute_timer = 0.0



def _nearest_charging_station(uav, world):
    stations = world.charging_stations
    if not stations:
        return None
    dists = [np.linalg.norm(np.array(cs["position"][:2]) - uav.position[:2]) for cs in stations]
    return stations[int(np.argmin(dists))]


def _safe_zone(uav, world, uavs):
    """Nearest charging station not already crowded with other UAVs."""
    stations = world.charging_stations
    if not stations:
        return None
    candidates = sorted(
        stations,
        key=lambda cs: np.linalg.norm(np.array(cs["position"][:2]) - uav.position[:2]))
    for cs in candidates:
        crowd = sum(
            1 for other in uavs
            if other is not uav and
            np.linalg.norm(other.position[:2] - np.array(cs["position"][:2])) < SAFE_ZONE_MIN_UAV_SEPARATION
        )
        if crowd == 0:
            return cs
    return candidates[0]


def manage_failures(uavs, world, all_tasks, dt,current_time, neighbor_map=None):
    from uavs.swarm import redistribute_queue

    for uav in uavs:
        if uav.battery_status == "DEAD":
            uav.velocity[:] = 0
            continue

        if uav.is_charging:
            uav.battery_soc = min(uav.battery_soc + CHARGING_RATE * dt, 100.0)
            if uav.battery_soc >= CHARGING_RELEASE_SOC:
                uav.flight_mode = "CRUISE"
                uav.is_charging = False
            continue

        if uav.battery_status == "EMERGENCY":
            # Try to hand off every queued task to a healthy neighbor first.
            if neighbor_map is not None:
                unplaced = redistribute_queue(uav, neighbor_map, world, current_time, uavs=uavs)
            else:
                unplaced = list(uav.task_queue)

            # Anything that couldn't be placed goes back to the global pool.
            for task in unplaced:
                task.status = "PENDING"
                task.assigned_uav = None
                if task in uav.task_queue:
                    uav.task_queue.remove(task)
            uav.current_task = None
            uav.compute_timer = 0.0

            station = _safe_zone(uav, world, uavs)
            uav.flight_mode = "EMERGENCY_DESCENT"
            if station:
                dist = np.linalg.norm(np.array(station["position"][:2]) - uav.position[:2])
                target = [station["position"][0], station["position"][1], uav.position[2]]
                uav.move_towards(target, dt)
                if dist < 20:
                    uav.is_charging = True
                    uav.battery_soc = min(uav.battery_soc + CHARGING_RATE * dt, 100.0)

        elif uav.battery_status in ("WARNING", "CRITICAL"):
            _release_task(uav)
            station = _nearest_charging_station(uav, world)
            if station:
                dist = np.linalg.norm(np.array(station["position"][:2]) - uav.position[:2])
                uav.flight_mode = "EMERGENCY_DESCENT" if uav.battery_status == "CRITICAL" else "ECO"
                if dist > 20:
                    target = [station["position"][0], station["position"][1], uav.position[2]]
                    uav.move_towards(target, dt)
                else:
                    uav.is_charging = True
                    uav.battery_soc = min(uav.battery_soc + CHARGING_RATE * dt, 100.0)