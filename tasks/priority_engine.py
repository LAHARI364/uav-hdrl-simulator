"""
Phase 9 — Dynamic Priority Engine
Converts per-task context into a numeric priority score [0, 1].

Formula:
    Priority = w1*deadline_score + w2*battery_score + w3*weather_score
             + w4*queue_score   + w5*importance_score
"""

import numpy as np
from configs.config import (
    W1_DEADLINE, W2_BATTERY, W3_WEATHER,
    W4_QUEUE, W5_IMPORTANCE
)

# Map the original string labels to a base importance value
_IMPORTANCE_MAP = {
    "low":       0.2,
    "medium":    0.5,
    "high":      0.8,
    "emergency": 1.0,
}


def compute_priority(task, uav, current_time, region_congestion=0.0, weather_severity=0.0):
    """
    Parameters
    ----------
    task              : Task object
    uav               : UAV assigned/considering this task
    current_time      : float — simulation time in seconds
    region_congestion : float [0,1] — from SubRegion.congestion
    weather_severity  : float [0,1] — from SubRegion.weather_severity (Phase 6)

    Returns
    -------
    float — final priority score in [0, 1]. Higher = more urgent.
    """

    # ── w1  Deadline urgency ──────────────────────────────────────────────────
    time_remaining  = max(task.deadline - (current_time - task.arrival_time), 0.0)
    deadline_score  = 1.0 - np.clip(time_remaining / task.deadline, 0.0, 1.0)
    # Approaches 1 as deadline nears

    # ── w2  Battery pressure ─────────────────────────────────────────────────
    # Low battery → this UAV should deprioritise far/heavy tasks
    battery_score = 1.0 - np.clip(uav.battery_soc / 100.0, 0.0, 1.0)
    # High value means the UAV is low on battery (pushes priority down for costly tasks)

    # ── w3  Weather severity ─────────────────────────────────────────────────
    weather_score = np.clip(weather_severity, 0.0, 1.0)
    # Severe weather increases urgency (tasks may become unreachable soon)

    # ── w4  Queue pressure (congestion in region) ────────────────────────────
    queue_score = np.clip(region_congestion, 0.0, 1.0)

    # ── w5  Base task importance ─────────────────────────────────────────────
    # Use the string label from TaskGenerator as the starting importance
    raw_priority   = task.priority if isinstance(task.priority, str) else "medium"
    importance_score = _IMPORTANCE_MAP.get(raw_priority, 0.5)

    # ── Weighted sum ─────────────────────────────────────────────────────────
    score = (W1_DEADLINE   * deadline_score
           + W2_BATTERY    * battery_score
           + W3_WEATHER    * weather_score
           + W4_QUEUE      * queue_score
           + W5_IMPORTANCE * importance_score)

    # Clamp to [0, 1]
    score = np.clip(score, 0.0, 1.0)

    # Write back onto the task so other modules can read it
    task.numeric_priority = score
    return score


def rank_tasks(tasks, uav, current_time, world=None):
    """
    Sort a list of Task objects by dynamic priority (highest first).

    Parameters
    ----------
    tasks        : list[Task]
    uav          : UAV
    current_time : float
    world        : Map (optional) — used to pull congestion & weather per region

    Returns
    -------
    list[Task] sorted descending by numeric_priority
    """
    for task in tasks:
        congestion = 0.0
        weather    = 0.0
        if world is not None and hasattr(task, "region_id"):
            region    = world.regions[task.region_id]
            congestion = region.congestion
            weather    = region.weather_severity
        compute_priority(task, uav, current_time, congestion, weather)

    return sorted(tasks, key=lambda t: t.numeric_priority, reverse=True)