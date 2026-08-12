"""
Stage 7 / Phase 12 — Swarm Load Balancing. NEW FILE (main branch only —
"idle vs busy" swarm dynamics don't exist with a single UAV, so this
isn't ported to the single-UAV branch).

Rule-based version of "healthy UAVs help overloaded regions": any UAV
that is currently idle (no current_task) and healthy (not
WARNING/CRITICAL/EMERGENCY/DEAD) drifts toward the most congested region
on the map, so it's already in position when new tasks spawn there
instead of sitting idle somewhere irrelevant.

Note: full per-UAV task-queue migration ("UAV3 -> UAV7", per the slides)
would need uav.task_queue to actually hold multiple queued tasks per
UAV, which the current sim structure doesn't do (each UAV works one
current_task at a time; unassigned tasks live in the global pending
pool and are re-auctioned every tick by assignment_engine). This patrol
behavior is the practical Stage-7 rule-based equivalent; true task
migration between UAV queues is a natural extension once task_queue is
actually populated.

Call once per tick, after collision avoidance.
"""

from configs.config import CONGESTION_HOTSPOT_THRESHOLD, LOAD_BALANCE_PATROL_MODE

IDLE_INELIGIBLE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")


def patrol_idle_uavs(uavs, world, dt):
    if not world.regions:
        return
    hotspot = max(world.regions, key=lambda r: r.congestion)
    if hotspot.congestion < CONGESTION_HOTSPOT_THRESHOLD:
        return

    target_x, target_y = hotspot.get_center()
    for uav in uavs:
        if uav.current_task is not None:
            continue
        if uav.battery_status in IDLE_INELIGIBLE_STATUSES:
            continue
        uav.flight_mode = LOAD_BALANCE_PATROL_MODE
        uav.move_towards([target_x, target_y, 50], dt)
