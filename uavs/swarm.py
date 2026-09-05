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
def redistribute_queue(uav, neighbor_map, world, current_time, uavs, verbose=True):
    """
    Used when a UAV enters EMERGENCY: attempt to hand EVERY task in its
    queue (including its current active task) to a feasible, healthy
    neighbor. Any task that has no feasible neighbor falls back to the
    global PENDING pool, same as before.

    Returns the list of tasks that could NOT be placed with a neighbor
    (so the caller can release them to the pool).
    """
    from tasks.assignment_engine import _is_feasible, compute_cost, MAX_QUEUE_PER_UAV

    uav_by_id = {u.id: u for u in uavs}
    tasks_to_place = list(uav.task_queue)  # current_task + all waiting
    unplaced = []

    for task in tasks_to_place:
        candidate_ids = neighbor_map.get(uav.id, [])
        candidates = [uav_by_id[cid] for cid in candidate_ids
                      if len(uav_by_id[cid].task_queue) < MAX_QUEUE_PER_UAV
                      and uav_by_id[cid].battery_status not in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")]

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
            if verbose:
                print(f"[SWARM MIGRATION] t={current_time:.1f}s | Task {task.task_id} "
                      f"({task.priority}) went from UAV {uav.id} -> UAV {best_uav.id} (emergency redistribution)")
        else:
            unplaced.append(task)

    return unplaced
def resolve_queue_for_failing_uav(uav, neighbor_map, world, current_time, uavs, verbose=True):
    """
    Applied to any UAV in WARNING/CRITICAL/EMERGENCY. For every task in
    its queue (active + waiting):
      1. Check if the UAV itself can still finish it after charging
         (charge_time + travel_time + compute_time <= time_remaining).
         If yes, leave it in the queue — the UAV will resume it later.
      2. If not, try to hand it to a feasible, healthy neighbor.
      3. If no neighbor works, release it to the global PENDING pool.
    """
    from configs.config import CHARGING_RATE, CHARGING_RELEASE_SOC, MAX_SPEED
    from tasks.assignment_engine import _is_feasible, compute_cost, MAX_QUEUE_PER_UAV

    uav_by_id = {u.id: u for u in uavs}
    tasks_to_check = list(uav.task_queue)  # active + waiting

    charge_needed = max(CHARGING_RELEASE_SOC - uav.battery_soc, 0.0)
    charge_time = charge_needed / CHARGING_RATE if CHARGING_RATE > 0 else float("inf")

    for task in tasks_to_check:
        time_remaining = task.deadline - (current_time - task.arrival_time)
        distance = uav.distance_to([task.location[0], task.location[1]])
        travel_time = distance / max(MAX_SPEED, 1e-6)
        compute_time = task.cpu_cycles / (uav.cpu_capacity * 1e9)
        self_time_needed = charge_time + travel_time + compute_time

        if self_time_needed <= time_remaining:
            if task is uav.current_task:
                uav.current_task = None
            continue  # leave in queue — UAV will do it after charging

        candidate_ids = neighbor_map.get(uav.id, []) if neighbor_map else []
        candidates = [uav_by_id[cid] for cid in candidate_ids
                      if len(uav_by_id[cid].task_queue) < MAX_QUEUE_PER_UAV
                      and uav_by_id[cid].battery_status not in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")]
        best_uav, best_cost = None, float("inf")
        for cand in candidates:
            d = cand.distance_to([task.location[0], task.location[1]])
            if not _is_feasible(task, cand, d, current_time):
                continue
            cost = compute_cost(task, cand, world, current_time, d)
            if cost < best_cost:
                best_cost, best_uav = cost, cand

        uav.task_queue.remove(task)
        if task is uav.current_task:
            uav.current_task = None

        if best_uav is not None:
            task.assigned_uav = best_uav.id
            best_uav.task_queue.append(task)
            if verbose:
                print(f"[SWARM] t={current_time:.1f}s Task {task.task_id} ({task.priority}) "
                      f"-> UAV {best_uav.id} (from UAV {uav.id}, self-infeasible)")
        else:
            task.status = "PENDING"
            task.assigned_uav = None
            if verbose:
                print(f"[SWARM] t={current_time:.1f}s Task {task.task_id} ({task.priority}) "
                      f"released to pool (from UAV {uav.id}, no feasible neighbor)")

    uav.compute_timer = 0.0