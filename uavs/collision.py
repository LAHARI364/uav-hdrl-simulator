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

            if a.battery_status in FAILURE_STATUSES and b.battery_status in FAILURE_STATUSES:
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

                # Hard clamp — if the soft push wasn't enough to keep them
                # apart (fast UAVs closing distance faster than the nudge
                # can counter), forcibly separate to exactly the safe distance.
                new_delta = a.position[:2] - b.position[:2]
                new_dist = np.linalg.norm(new_delta)
                if new_dist < COLLISION_SAFE_DISTANCE:
                    if new_dist < 1e-6:
                        new_delta = np.random.uniform(-1, 1, size=2)
                        new_dist = np.linalg.norm(new_delta) + 1e-6
                    correction = (COLLISION_SAFE_DISTANCE - new_dist) / 2.0
                    unit = new_delta / new_dist
                    a.position[:2] += unit * correction
                    b.position[:2] -= unit * correction