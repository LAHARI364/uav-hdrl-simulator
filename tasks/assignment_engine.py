"""
Phase 8 — Task Assignment Engine (Slide 8 cost function). NEW FILE.

Cost = w1*Distance + w2*Delay + w3*Energy + w4*Weather + w5*Congestion - w6*Priority
(lower cost wins.)

This is where battery now lives: Energy is the % of a CANDIDATE UAV's own
remaining battery that flying to + computing THIS task would burn, so a
low-battery UAV is naturally penalized more for the same task, without
priority needing to know which UAV is involved.

`ranked_tasks` should already be priority-sorted (see
tasks.priority_engine.rank_tasks) so that when several tasks compete for
the same best UAV, the higher-priority task gets first pick. This is what
actually wires the priority score into WHO gets assigned — previously
rank_tasks was computed but never consulted by the assignment step at all.
"""

from configs.config import (
    ASSIGNMENT_WEIGHTS, MAX_ASSIGN_DISTANCE, MAX_SPEED,
    BATTERY_CAPACITY_WH, HOVER_BASE_POWER_W, DRAG_LINEAR_COEFF,
    DRAG_CUBIC_COEFF, CPU_POWER_PER_GHZ_W,
)

INELIGIBLE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")


def _eligible(uav):
    return uav.current_task is None and uav.battery_status not in INELIGIBLE_STATUSES


def _estimate_task_energy_wh(task, uav, distance):
    """
    Rough energy cost (Wh) of flying to + computing this task for a given
    candidate UAV, using the same physical constants as
    power/battery_engine.py. Purely a hypothetical estimate for scoring —
    does not mutate any UAV state.
    """
    travel_time = distance / max(MAX_SPEED, 1e-6)
    p_move = DRAG_LINEAR_COEFF * MAX_SPEED + DRAG_CUBIC_COEFF * MAX_SPEED ** 3

    compute_time = task.cpu_cycles / (uav.cpu_capacity * 1e9)
    p_hover = HOVER_BASE_POWER_W
    p_cpu = CPU_POWER_PER_GHZ_W * uav.cpu_capacity  # assume full utilization while computing

    energy_ws = p_move * travel_time + (p_hover + p_cpu) * compute_time
    return energy_ws / 3600.0  # W*s -> Wh


def compute_cost(task, uav, world, current_time):
    distance = uav.distance_to([task.location[0], task.location[1]])
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
    cost = (
        w["distance"] * distance_score +
        w["delay"] * delay_score +
        w["energy"] * energy_score +
        w["weather"] * weather_score +
        w["congestion"] * congestion_score -
        w["priority"] * priority_score
    )
    return cost


def assign_tasks(ranked_tasks, candidate_uavs, world, current_time):
    """
    Greedily assigns priority-sorted tasks to the lowest-cost free UAV.
    Each UAV takes at most one task per call (removed from the pool once
    assigned). Mutates task.status / task.assigned_uav / uav.current_task
    in place; returns nothing.
    """
    available = [u for u in candidate_uavs if _eligible(u)]

    for task in ranked_tasks:
        if not available:
            break
        best_uav, best_cost = None, float("inf")
        for uav in available:
            cost = compute_cost(task, uav, world, current_time)
            if cost < best_cost:
                best_cost, best_uav = cost, uav
        if best_uav is not None:
            task.status = "ASSIGNED"
            task.assigned_uav = best_uav.id
            best_uav.current_task = task
            available.remove(best_uav)
