"""
Stage 7 / Phase 14 — Static obstacle avoidance + no-fly zones. NEW FILE.

Two related but distinct constraints, both circular keep-out zones:

  * STATIC_OBSTACLES — physical obstacles (towers, terrain, buildings).
    UAVs get a soft repulsion, same as UAV-UAV collision avoidance: a
    nudge proportional to how deep they've penetrated the safety margin,
    not a hard wall.

  * NO_FLY_ZONES — regulatory/restricted airspace. On top of the same
    soft repulsion, any UAV still inside a zone after that nudge (e.g. a
    fast UAV crosses the whole margin in one tick) gets hard-clamped back
    to the boundary. Zero tolerance for being inside, unlike obstacles.

Direct position correction, like collision.py, for the same reason:
move_towards() recomputes velocity from scratch every tick, so a
velocity-based nudge would be overwritten before it did anything.

Call once per tick, after apply_collision_avoidance() and before swarm
load balancing.
"""

import numpy as np
from configs.config import (
    STATIC_OBSTACLES, OBSTACLE_SAFE_DISTANCE, OBSTACLE_REPULSION_GAIN,
    NO_FLY_ZONES, NO_FLY_ZONE_MARGIN,
)


def _soft_repel(uav, center, keep_out_radius, gain, dt):
    """Nudge `uav` away from a fixed circular zone if inside keep_out_radius."""
    center = np.asarray(center, dtype=float)
    delta = uav.position[:2] - center
    dist = np.linalg.norm(delta)
    if dist < 1e-6:
        delta = np.random.uniform(-1, 1, size=2)
        dist = np.linalg.norm(delta) + 1e-6
    if dist < keep_out_radius:
        penetration = (keep_out_radius - dist) / keep_out_radius
        shift = (delta / dist) * (gain * penetration * dt)
        uav.position[:2] += shift


def apply_obstacle_avoidance(uavs, dt):
    """Soft repulsion away from static physical obstacles."""
    for uav in uavs:
        if uav.battery_status == "DEAD":
            continue  # grounded, not flying — obstacles don't apply
        for obs in STATIC_OBSTACLES:
            keep_out = obs["radius"] + OBSTACLE_SAFE_DISTANCE
            _soft_repel(uav, obs["center"], keep_out, OBSTACLE_REPULSION_GAIN, dt)


def apply_no_fly_zones(uavs, dt):
    """Soft repulsion near the boundary, PLUS a hard clamp so no UAV can
    ever end a tick with its position inside a no-fly zone."""
    for uav in uavs:
        if uav.battery_status == "DEAD":
            continue
        for zone in NO_FLY_ZONES:
            keep_out = zone["radius"] + NO_FLY_ZONE_MARGIN
            _soft_repel(uav, zone["center"], keep_out, OBSTACLE_REPULSION_GAIN, dt)

            # Hard exclusion — this is what makes NFZs different from
            # ordinary obstacles: zero tolerance for being inside.
            # uavs/airspace.py — inside apply_no_fly_zones, replace the hard-exclusion block:
            center = np.asarray(zone["center"], dtype=float)
            delta = uav.position[:2] - center
            dist = np.linalg.norm(delta)
            if dist < zone["radius"]:
                if dist < 1e-6:
                    delta = np.random.uniform(-1, 1, size=2)
                    dist = np.linalg.norm(delta) + 1e-6
                uav.position[:2] = center + (delta / dist) * (zone["radius"] + 1e-3)


def is_in_no_fly_zone(x, y):
    """Utility for other modules (task_generator, charging-station
    placement, assignment_engine) to check a candidate point before using
    it. Not wired in anywhere yet — see the note at the end."""
    for zone in NO_FLY_ZONES:
        cx, cy = zone["center"]
        if (x - cx) ** 2 + (y - cy) ** 2 < zone["radius"] ** 2:
            return True
    return False