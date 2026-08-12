"""
Phase 9 — Dynamic Priority Engine (revised).

Priority is now purely task-level: "how urgent is this task right now",
independent of which UAV might eventually pick it up. This fixes the
original ambiguity where a battery term inside compute_priority(task,
uav, ...) needed a UAV *before* one had been assigned — so the same task
could score differently depending on which UAV the caller happened to
pass in. Battery now lives entirely in the assignment cost function
(tasks/assignment_engine.py), scored per (task, candidate UAV) pair at
assignment time, which is where it actually belongs.

REPLACES the entire previous tasks/priority_engine.py.
"""

from configs.config import PRIORITY_WEIGHTS

IMPORTANCE_MAP = {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "emergency": 1.0,
}


def compute_priority(task, current_time, world):
    region = (world.regions[task.region_id] if task.region_id is not None
              else world.get_region_of_position(task.location[0], task.location[1]))

    time_elapsed = current_time - task.arrival_time
    time_remaining = max(task.deadline - time_elapsed, 0.0)
    deadline_score = (1.0 - (time_remaining / task.deadline)) if task.deadline > 0 else 1.0
    deadline_score = min(max(deadline_score, 0.0), 1.0)

    weather_score = region.weather_severity if region else 0.0
    queue_score = region.congestion if region else 0.0
    importance_score = IMPORTANCE_MAP.get(task.priority, 0.5)

    score = (
        PRIORITY_WEIGHTS["deadline"] * deadline_score +
        PRIORITY_WEIGHTS["weather"] * weather_score +
        PRIORITY_WEIGHTS["queue"] * queue_score +
        PRIORITY_WEIGHTS["importance"] * importance_score
    )
    score = min(max(score, 0.0), 1.0)

    task.numeric_priority = score
    return score


def rank_tasks(tasks, current_time, world):
    for t in tasks:
        compute_priority(t, current_time, world)
    return sorted(tasks, key=lambda t: t.numeric_priority, reverse=True)