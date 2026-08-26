# main.py
"""
UAV HDRL Simulator — Stage 7 rule-based simulator (pre-DRL).

Order each tick: weather -> generate tasks -> priority ranking ->
cost-based assignment -> failure management (planned/emergency landing,
charging) -> movement + local/MEC compute -> collision avoidance ->
swarm load balancing (idle-UAV patrol) -> battery drain -> world/
congestion update -> render.
"""

import numpy as np

from environment.map import Map
from uavs.uav import UAV
from tasks.task_generator import TaskGenerator
from tasks.priority_engine import rank_tasks
from tasks.assignment_engine import assign_tasks
from tasks.load_balancer import patrol_idle_uavs
from tasks.scheduler import schedule_uav_tasks
from uavs.collision import apply_collision_avoidance
from uavs.failure_management import manage_failures
from offloading.mec_offload import MECServer, decide_offload
from weatherr.weather_engine import WeatherSystem
from visualization.sim_viz import SimVisualizer
from uavs.airspace import apply_obstacle_avoidance, apply_no_fly_zones
from configs.config import (
    NUM_UAVS, TOTAL_SIM_TIME, TIMESTEP,
    MAP_WIDTH, MAP_HEIGHT, VIZ_SPEED,
)

FAILURE_STATUSES = ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")

# ── Init world ────────────────────────────────────────────────────────────
world = Map()

uavs = [UAV(i, [np.random.uniform(0, MAP_WIDTH),
              np.random.uniform(0, MAP_HEIGHT), 50])
        for i in range(NUM_UAVS)]

mec_servers = [MECServer(i, cs["position"])
               for i, cs in enumerate(world.charging_stations)]

gen = TaskGenerator(world)
weather = WeatherSystem("data/historical_storm.csv")
viz = SimVisualizer(world, uavs, mec_servers)

all_tasks = []
sim_time = 0.0
mec_offload_count = 0
local_compute_count = 0

# ── Simulation loop ──────────────────────────────────────────────────────
while viz.running and sim_time < TOTAL_SIM_TIME:

    # 1. Weather
    weather.tick(TIMESTEP)
    weather.update_regions(world)

    # 2. Generate tasks
    new_tasks = gen.generate_tasks(sim_time, TIMESTEP)
    for t in new_tasks:
        world.register_task_to_region(t)
    all_tasks.extend(new_tasks)

    # 3. Priority ranking + cost-based assignment (fixes: priority was
    #    computed but never consulted by assignment before this)
    pending = [t for t in all_tasks if t.status == "PENDING"]
    ranked = rank_tasks(pending, sim_time, world)
    free_uavs = [u for u in uavs if len(u.task_queue) < 3
                 and u.battery_status not in FAILURE_STATUSES
                 and not u.is_charging]
    assign_tasks(ranked, free_uavs, world, sim_time, mec_servers)
    schedule_uav_tasks(uavs)
    active_task_ids = [u.current_task.task_id for u in uavs if u.current_task is not None]
    dupes = set(x for x in active_task_ids if active_task_ids.count(x) > 1)
    if dupes:
        for tid in dupes:
            owners = [u.id for u in uavs if u.current_task is not None and u.current_task.task_id == tid]
            print(f"[DUPLICATE] Task {tid} is current_task for UAVs {owners}")    
    if int(sim_time * 10) % 50 == 0:
        from tasks.assignment_engine import debug_print_uav_view
        debug_print_uav_view(uavs, ranked, world, sim_time)    
    print(f"Tick {sim_time:.1f}s: {len(new_tasks)} new tasks, "
          f"{len(pending)} pending, {len(free_uavs)} free UAVs")
    # 4. Failure management: planned + emergency landing, drops tasks
    #    back to the pool, navigates to / charges at a station.
    manage_failures(uavs, world, all_tasks, TIMESTEP)

    # 5. Move UAVs toward assigned tasks + local/MEC compute
    for uav in uavs:
        if uav.battery_status in FAILURE_STATUSES:
            continue  # handled by manage_failures this tick
        task = uav.current_task
        if task is None:
            continue

        if uav.compute_timer > 0:
            uav.compute_timer -= TIMESTEP
            uav.flight_mode = "HOVER"
            if uav.compute_timer <= 0:
                task.status = "DONE"
                region = world.get_region_of_position(task.location[0], task.location[1])
                if region:
                    region.remove_task(task)
                if task in uav.task_queue:
                    uav.task_queue.remove(task)
                uav.current_task = None

        else:
            target = [task.location[0], task.location[1], 50]
            uav.flight_mode = "CRUISE"
            uav.move_towards(target, TIMESTEP)
            if uav.distance_to(target) < 20:
                weather_factor = 1.0 - (uav.current_region.weather_severity
                                         if uav.current_region else 0.0)
                decision = decide_offload(task, uav, mec_servers, sim_time, weather_factor=weather_factor)
                uav.compute_timer = decision["latency"]
                if decision["strategy"] == "MEC":
                    mec_offload_count += 1
                else:
                    local_compute_count += 1
    # Deadline expiry -> FAILED (covers pending AND in-flight tasks)
    for t in all_tasks:
        if t.status in ("PENDING", "ASSIGNED") and sim_time - t.arrival_time > t.deadline:
            t.fail_reason = "NEVER_ASSIGNED" if t.status == "PENDING" else "MISSED_DEADLINE_INFLIGHT"
            t.status = "FAILED"
            if t.assigned_uav is not None:
                owner = next((u for u in uavs if u.id == t.assigned_uav), None)
                if owner:
                    if t in owner.task_queue:
                        owner.task_queue.remove(t)
                    if owner.current_task is t:
                        owner.current_task = None
                        owner.compute_timer = 0.0

    # 6. Collision avoidance
    # main.py — Step 6, right after the existing collision-avoidance call:
    # 6. Collision avoidance (UAV-UAV, then static obstacles + no-fly zones)
    apply_collision_avoidance(uavs, TIMESTEP)
    apply_obstacle_avoidance(uavs, TIMESTEP)
    apply_no_fly_zones(uavs, TIMESTEP)

    # 7. Swarm load balancing — idle, healthy UAVs patrol toward hotspots
    patrol_idle_uavs(uavs, world, TIMESTEP)

    # 8. Battery drain (every UAV, every tick)
    for uav in uavs:
        if uav.is_charging or uav.battery_status == "DEAD":
            continue  # no aerodynamic/CPU drain while grounded+charging, or already dead
        weather_factor = 1.0 - (uav.current_region.weather_severity
                             if uav.current_region else 0.0)
        uav.drain_battery(TIMESTEP, weather_factor)

    # 9. World update
    world.tick(uavs)

    # 10. Render
    viz.render(all_tasks, sim_time)
    viz.tick(fps=60)
    sim_time += TIMESTEP * VIZ_SPEED

viz.close()
print("Simulation ended.")

done = sum(1 for t in all_tasks if t.status == "DONE")
failed = sum(1 for t in all_tasks if t.status == "FAILED")
in_progress = sum(1 for t in all_tasks if t.status in ("PENDING", "ASSIGNED"))
print(f"Done={done}  Failed={failed}  Pending/InProgress={in_progress}  Total={len(all_tasks)}")
print(f"MEC Offloads: {mec_offload_count}, Local Computes: {local_compute_count}")
from collections import Counter
fail_reasons = Counter(getattr(t, "fail_reason", "UNKNOWN") for t in all_tasks if t.status == "FAILED")
print("Failure breakdown:", dict(fail_reasons))