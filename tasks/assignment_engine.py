"""
Phase 8 — Task Assignment Engine (Slide 8 cost function).

Cost = w1*Distance + w2*Delay + w3*Energy + w4*Weather + w5*Congestion - w6*Priority
(lower cost wins.)

Feasibility fix: a UAV is now only a candidate for a task if it can
physically arrive AND finish computing before the deadline. Previously
delay_score only *penalized* long travel times but never disqualified a
UAV, so UAVs were accepting tasks they could not possibly complete —
they'd fail mid-flight instead of never being assigned at all.

If NO UAV can make the deadline, the task is offloaded straight to the
nearest reachable MEC server instead of being assigned to a doomed UAV.
"""

from configs.config import (
    ASSIGNMENT_WEIGHTS, MAX_ASSIGN_DISTANCE, MAX_SPEED,
    BATTERY_CAPACITY_WH, HOVER_BASE_POWER_W, DRAG_LINEAR_COEFF,
    DRAG_CUBIC_COEFF, CPU_POWER_PER_GHZ_W, COMM_RANGE,
)

INELIGIBLE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")


def _eligible(uav):
    return uav.current_task is None and uav.battery_status not in INELIGIBLE_STATUSES


def _estimate_task_energy_wh(task, uav, distance):
    travel_time = distance / max(MAX_SPEED, 1e-6)
    p_move = DRAG_LINEAR_COEFF * MAX_SPEED + DRAG_CUBIC_COEFF * MAX_SPEED ** 3
    compute_time = task.cpu_cycles / (uav.cpu_capacity * 1e9)
    p_hover = HOVER_BASE_POWER_W
    p_cpu = CPU_POWER_PER_GHZ_W * uav.cpu_capacity
    energy_ws = p_move * travel_time + (p_hover + p_cpu) * compute_time
    return energy_ws / 3600.0


def _time_needed(task, uav, distance):
    """Travel time + local compute time for this UAV to finish this task."""
    travel_time = distance / max(MAX_SPEED, 1e-6)
    compute_time = task.cpu_cycles / (uav.cpu_capacity * 1e9)
    return travel_time + compute_time


def _is_feasible(task, uav, distance, current_time):
    if task.deadline <= 0:
        return True
    time_remaining = task.deadline - (current_time - task.arrival_time)
    return _time_needed(task, uav, distance) <= time_remaining


def compute_cost(task, uav, world, current_time, distance):
    region = (world.regions[task.region_id] if task.region_id is not None
              else world.get_region_of_position(task.location[0], task.location[1]))

    distance_score = min(distance / MAX_ASSIGN_DISTANCE, 1.0)

    travel_time = distance / max(MAX_SPEED, 1e-6)
    delay_score = min(travel_time / task.deadline, 1.0) if task.deadline > 0 else 0.0

    energy_wh = _estimate_task_energy_wh(task, uav, distance)
    remaining_wh = (uav.battery_soc / 100.0) * BATTERY_CAPACITY_WH
    energy_score = 1.0 if remaining_wh <= 1e-6 else min(energy_wh / remaining_wh, 1.0)

    weather_score = region.weather_severity if region else 0.0
    congestion_score = region.congestion if region else 0.0
    priority_score = getattr(task, "numeric_priority", 0.0)

    w = ASSIGNMENT_WEIGHTS
    return (
        w["distance"] * distance_score +
        w["delay"] * delay_score +
        w["energy"] * energy_score +
        w["weather"] * weather_score +
        w["congestion"] * congestion_score -
        w["priority"] * priority_score
    )


def _nearest_reachable_mec(task, mec_servers):
    """Nearest MEC server within comm range of the task's location, or None."""
    if not mec_servers:
        return None
    best, best_dist = None, float("inf")
    for server in mec_servers:
        dx = server.position[0] - task.location[0]
        dy = server.position[1] - task.location[1]
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist <= COMM_RANGE and dist < best_dist:
            best, best_dist = server, dist
    return best


def assign_tasks(ranked_tasks, candidate_uavs, world, current_time, mec_servers=None):
    """
    Greedily assigns priority-sorted tasks to the lowest-cost free UAV
    that can actually make the deadline. If no UAV is feasible, offloads
    straight to the nearest reachable MEC server (task -> ASSIGNED,
    assigned_uav stays None, handled/completed by MEC logic elsewhere).
    If neither a UAV nor an MEC server can take it, the task is left
    PENDING and will fail naturally at deadline expiry.
    """
    available = [u for u in candidate_uavs if _eligible(u)]

    for task in ranked_tasks:
        best_uav, best_cost = None, float("inf")
        for uav in available:
            distance = uav.distance_to([task.location[0], task.location[1]])
            if not _is_feasible(task, uav, distance, current_time):
                continue
            cost = compute_cost(task, uav, world, current_time, distance)
            if cost < best_cost:
                best_cost, best_uav = cost, uav

        if best_uav is not None:
            task.status = "ASSIGNED"
            task.assigned_uav = best_uav.id
            best_uav.current_task = task
            available.remove(best_uav)
            continue

        # No UAV can make the deadline — try MEC offload directly.
        server = _nearest_reachable_mec(task, mec_servers) if mec_servers else None
        if server is not None:
            task.status = "ASSIGNED"
            task.assigned_uav = None
            task.assigned_mec = server.server_id