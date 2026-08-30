"""
Swarm coordination — scoped version.

Adapted from the neighbor-discovery concept in Zhao et al. (2022),
"Distributed coordinated control scheme of UAV swarm based on
heterogeneous roles" — but only the neighbor-graph idea is used here.
Roles (leader/coordinator/follower), formation slots, and the S1-S6
transition logic from that paper are NOT implemented; this project's
UAVs serve independent tasks rather than holding a shared formation,
so that machinery doesn't apply. Task migration below is this
project's own extension, not from the paper.

Call once per tick, after assignment/scheduling, before movement.
"""

from configs.config import COMM_RANGE

MIGRATION_COOLDOWN = 2.0  # seconds — avoid a task ping-ponging every tick


def find_neighbors(uavs):
    """Returns {uav_id: [neighbor_uav_ids]} for UAVs within COMM_RANGE."""
    neighbors = {u.id: [] for u in uavs}
    n = len(uavs)
    for i in range(n):
        a = uavs[i]
        if a.battery_status == "DEAD":
            continue
        for j in range(i + 1, n):
            b = uavs[j]
            if b.battery_status == "DEAD":
                continue
            dist = a.distance_to(b.position)
            if dist <= COMM_RANGE:
                neighbors[a.id].append(b.id)
                neighbors[b.id].append(a.id)
    return neighbors


def migrate_overloaded_tasks(uavs, neighbor_map, world, current_time):
    """
    If a UAV's queue is full (or it's about to go into a failure state)
    and a neighbor has spare queue capacity, hand off the UAV's lowest-
    priority QUEUED (not yet active) task to that neighbor instead of
    letting it fail or wait unnecessarily.
    """
    from tasks.assignment_engine import _is_feasible, compute_cost, MAX_QUEUE_PER_UAV

    uav_by_id = {u.id: u for u in uavs}

    for uav in uavs:
        if uav.battery_status == "DEAD":
            continue
        if len(uav.task_queue) < MAX_QUEUE_PER_UAV and uav.battery_status not in ("WARNING", "CRITICAL", "EMERGENCY"):
            continue  # not overloaded, nothing to migrate

        waiting = [t for t in uav.task_queue if t is not uav.current_task]
        if not waiting:
            continue

        candidate_ids = neighbor_map.get(uav.id, [])
        candidates = [uav_by_id[cid] for cid in candidate_ids
                      if len(uav_by_id[cid].task_queue) < MAX_QUEUE_PER_UAV
                      and uav_by_id[cid].battery_status not in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")]
        if not candidates:
            continue

        task = min(waiting, key=lambda t: getattr(t, "numeric_priority", 0.0))

        best_uav, best_cost = None, float("inf")
        for cand in candidates:
            distance = cand.distance_to([task.location[0], task.location[1]])
            if not _is_feasible(task, cand, distance, current_time):
                continue
            cost = compute_cost(task, cand, world, current_time, distance)
            if cost < best_cost:
                best_cost, best_uav = cost, cand

        if best_uav is not None:
            uav.task_queue.remove(task)
            task.assigned_uav = best_uav.id
            best_uav.task_queue.append(task)


def migrate_overloaded_tasks(uavs, neighbor_map, world, current_time, verbose=True):
    from tasks.assignment_engine import _is_feasible, compute_cost, MAX_QUEUE_PER_UAV

    uav_by_id = {u.id: u for u in uavs}
    migrations = []

    for uav in uavs:
        if uav.battery_status == "DEAD":
            continue

        # Only migrate when a UAV is actually failing (about to drop
        # everything anyway) — NOT just because its queue is at the
        # normal operating cap. A full queue on a healthy UAV is normal,
        # not overload.
        if uav.battery_status not in ("WARNING", "CRITICAL", "EMERGENCY"):
            continue

        waiting = [t for t in uav.task_queue if t is not uav.current_task]
        if not waiting:
            continue

        last_migrated = getattr(uav, "_last_migration_time", -999)
        if current_time - last_migrated < MIGRATION_COOLDOWN:
            continue

        candidate_ids = neighbor_map.get(uav.id, [])
        candidates = [uav_by_id[cid] for cid in candidate_ids
                      if len(uav_by_id[cid].task_queue) < MAX_QUEUE_PER_UAV
                      and uav_by_id[cid].battery_status not in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")]
        if not candidates:
            continue

        task = min(waiting, key=lambda t: getattr(t, "numeric_priority", 0.0))

        best_uav, best_cost = None, float("inf")
        for cand in candidates:
            distance = cand.distance_to([task.location[0], task.location[1]])
            if not _is_feasible(task, cand, distance, current_time):
                continue
            cost = compute_cost(task, cand, world, current_time, distance)
            if cost < best_cost:
                best_cost, best_uav = cost, cand

        if best_uav is not None:
            uav.task_queue.remove(task)
            task.assigned_uav = best_uav.id
            best_uav.task_queue.append(task)
            uav._last_migration_time = current_time
            migrations.append((uav.id, best_uav.id, task.task_id, task.priority))

    if verbose and migrations:
        for from_id, to_id, task_id, priority in migrations:
            print(f"[SWARM MIGRATION] t={current_time:.1f}s | Task {task_id} "
                  f"({priority}) went from UAV {from_id} -> UAV {to_id}")

    return migrations