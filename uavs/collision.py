"""
Stage 7 / Phase 11 — Collision Avoidance. NEW FILE (main branch only —
meaningless on the single-UAV branch since there's only one UAV to
collide with, so it isn't ported there).

Simple pairwise repulsion: any two UAVs closer than
COLLISION_SAFE_DISTANCE get nudged apart, proportional to how deep the
violation is. Implemented as a direct position correction (not a
velocity change) because move_towards() recalculates velocity fresh
every tick from scratch — a velocity-based nudge would just get
overwritten on the next tick before it did anything.

Call once per tick, after task-driven movement, before world.tick().
"""

import numpy as np
from configs.config import COLLISION_SAFE_DISTANCE, COLLISION_REPULSION_GAIN


FAILURE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY")

def apply_collision_avoidance(uavs, dt):
    n = len(uavs)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = uavs[i], uavs[j]
            if a.battery_status == "DEAD" or b.battery_status == "DEAD":
                continue

            # Don't repel two UAVs both converging on a charging station —
            # they need to cluster there, not dodge each other.
            if a.is_charging and b.is_charging:
                continue

            delta = a.position[:2] - b.position[:2]
            dist = np.linalg.norm(delta)
            if dist < 1e-6:
                delta = np.random.uniform(-1, 1, size=2)
                dist = np.linalg.norm(delta) + 1e-6

            if dist < COLLISION_SAFE_DISTANCE:
                penetration = (COLLISION_SAFE_DISTANCE - dist) / COLLISION_SAFE_DISTANCE
                shift = (delta / dist) * (COLLISION_REPULSION_GAIN * penetration * dt)
                a.position[:2] += shift
                b.position[:2] -= shift