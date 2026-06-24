# # from environment.map import Map
# # from uavs.uav import UAV
# # from tasks.task_generator import TaskGenerator
# # from tasks.priority_engine import rank_tasks
# # from communication.comm_engine import CommLink, can_communicate
# # from offloading.mec_offload import MECServer, decide_offload
# # import numpy as np

# # # ── World ─────────────────────────────────────────────────────────────────────
# # world = Map()
# # print(world)

# # # ── UAVs ─────────────────────────────────────────────────────────────────────
# # uavs = [UAV(i, position=[np.random.uniform(0, 10000),
# #                           np.random.uniform(0, 10000), 50])
# #         for i in range(3)]
# # for u in uavs:
# #     print(u)

# # # ── MEC Servers (one per charging station) ───────────────────────────────────
# # mec_servers = [
# #     MECServer(i, cs["position"])
# #     for i, cs in enumerate(world.charging_stations)
# # ]
# # for m in mec_servers:
# #     print(m)

# # # ── Generate tasks ────────────────────────────────────────────────────────────
# # gen   = TaskGenerator()
# # tasks = gen.generate_tasks(current_time=0.0, dt=1.0)
# # print(f"\nNumber of tasks: {len(tasks)}")

# # # Register tasks to their subregions (Stage 3 integration)
# # for t in tasks:
# #     world.register_task_to_region(t)

# # # ── Tick world (update UAV counts + congestion) ───────────────────────────────
# # world.tick(uavs)

# # print("\n── Region state after tick ──")
# # for r in world.regions:
# #     print(r)

# # # ── Dynamic Priority Ranking (Phase 9) ───────────────────────────────────────
# # uav0 = uavs[0]
# # ranked = rank_tasks(tasks, uav0, current_time=0.0, world=world)
# # print(f"\n── Tasks ranked for UAV-0 (top 5) ──")
# # for t in ranked[:5]:
# #     print(f"  {t} | numeric_priority={t.numeric_priority:.3f}")

# # # ── Communication Link Demo (Phase 7) ─────────────────────────────────────────
# # print("\n── CommLink: UAV-0 → UAV-1 ──")
# # link = CommLink(uavs[0], uavs[1]).update(weather_factor=1.0)
# # print(link)

# # # ── MEC Offloading Decision Demo (Phase 10) ──────────────────────────────────
# # if ranked:
# #     top_task = ranked[0]
# #     decision = decide_offload(top_task, uav0, mec_servers, current_time=0.0)
# #     print(f"\n── Offload decision for top task ({top_task.task_id}) ──")
# #     print(f"  Strategy : {decision['strategy']}")
# #     print(f"  Latency  : {decision['latency']:.4f}s")
# #     if decision["details"]:
# #         d = decision["details"]
# #         print(f"  MEC #{decision['mec_server'].server_id} | "
# #               f"upload={d['t_upload']:.3f}s | "
# #               f"queue={d['t_queue']:.3f}s | "
# #               f"compute={d['t_compute']:.3f}s | "
# #               f"download={d['t_download']:.3f}s")

# # print("\nAll Stage 3 + Phase 7/9/10 checks passed ✓")
# from environment.map import Map
# from uavs.uav import UAV
# from tasks.task_generator import TaskGenerator
# from tasks.priority_engine import rank_tasks
# from communication.comm_engine import CommLink
# from offloading.mec_offload import MECServer, decide_offload
# from weatherr.weather_engine import WeatherSystem
# import numpy as np

# # ── World ─────────────────────────────────────────────────────────────────────
# world = Map()
# print(world)

# # ── UAVs ─────────────────────────────────────────────────────────────────────
# uavs = [UAV(i, position=[np.random.uniform(0, 10000),
#                           np.random.uniform(0, 10000), 50])
#         for i in range(3)]
# for u in uavs:
#     print(u)

# # ── MEC Servers (one per charging station) ───────────────────────────────────
# mec_servers = [MECServer(i, cs["position"]) for i, cs in enumerate(world.charging_stations)]
# for m in mec_servers:
#     print(m)

# # ── Weather System (Phase 6 Data-Driven) ──────────────────────────────────────
# weather = WeatherSystem()
# # Advance the weather timeline slightly to show rain/wind changes
# for _ in range(5):
#     weather.tick(dt=1.0)
# weather.update_regions(world)

# print(f"\n── Weather state ── {weather}")
# for r in world.regions[:4]:
#     print(f"  Region {r.region_id} | weather_severity={r.weather_severity:.3f}")

# # ── Generate tasks ────────────────────────────────────────────────────────────
# gen   = TaskGenerator()
# tasks = gen.generate_tasks(current_time=0.0, dt=1.0)
# print(f"\nNumber of tasks: {len(tasks)}")
# for t in tasks:
#     world.register_task_to_region(t)
# world.tick(uavs)

# print("\n── Region state after tick ──")
# for r in world.regions:
#     print(r)

# # ── Dynamic Priority Ranking (Phase 9) ───────────────────────────────────────
# uav0 = uavs[0]
# ranked = rank_tasks(tasks, uav0, current_time=5.0, world=world)
# print("\n── Tasks ranked for UAV-0 (top 5) ──")
# for t in ranked[:5]:
#     print(f"  {t} | numeric_priority={t.numeric_priority:.3f}")

# # ── Communication Link Demo (Phase 7), now weather-aware ────────────────────
# weather_factor_uav0 = 1.0 - (uav0.current_region.weather_severity if uav0.current_region else 0.0)
# print("\n── CommLink: UAV-0 → UAV-1 ──")
# link = CommLink(uavs[0], uavs[1]).update(weather_factor=weather_factor_uav0)
# print(link)

# # ── MEC Offloading Decision Demo (Phase 10), now weather-aware ──────────────
# if ranked:
#     top_task = ranked[0]
#     decision = decide_offload(top_task, uav0, mec_servers, current_time=5.0,
#                                weather_factor=weather_factor_uav0)
#     print(f"\n── Offload decision for top task ({top_task.task_id}) ──")
#     print(f"  Strategy : {decision['strategy']}")
#     print(f"  Latency  : {decision['latency']:.4f}s")
#     if decision["details"]:
#         d = decision["details"]
#         print(f"  MEC #{decision['mec_server'].server_id} | "
#               f"upload={d['t_upload']:.3f}s | queue={d['t_queue']:.3f}s | "
#               f"compute={d['t_compute']:.3f}s | download={d['t_download']:.3f}s")

# # ── Non-Linear Battery Engine Demo (Phase 5) ─────────────────────────────────
# print("\n── Battery drain demo for UAV-0 over 60s in HIGH_SPEED mode ──")
# uav0.flight_mode = "HIGH_SPEED"
# uav0.cpu_utilization = 0.6
# uav0.is_communicating = True
# for step in range(1, 61):
#     soc, breakdown = uav0.drain_battery(dt=1.0)
#     if step % 10 == 0:
#         print(f"  t={step}s | SOC={soc:.2f}% | Status={uav0.battery_status} | "
#               f"hover={breakdown['hover']:.1f}W move={breakdown['movement']:.1f}W "
#               f"cpu={breakdown['cpu']:.1f}W comm={breakdown['comm']:.1f}W")

# print("\nAll Stage 3 + Phase 5/6/7/9/10 checks passed ✓")

# main.py
from environment.map import Map
from uavs.uav import UAV
from tasks.task_generator import TaskGenerator
from tasks.priority_engine import rank_tasks
from offloading.mec_offload import MECServer, decide_offload
from visualization.sim_viz import SimVisualizer
from configs.config import (
    NUM_UAVS, TOTAL_SIM_TIME, TIMESTEP,
    MAP_WIDTH, MAP_HEIGHT, VIZ_SPEED
)
import numpy as np

# ── Init world ────────────────────────────────────────────────────────────────
world = Map()
uavs  = [UAV(i, [np.random.uniform(0, MAP_WIDTH),
                  np.random.uniform(0, MAP_HEIGHT), 50])
          for i in range(NUM_UAVS)]
mec_servers = [MECServer(i, cs["position"])
               for i, cs in enumerate(world.charging_stations)]
gen  = TaskGenerator()
viz  = SimVisualizer(world, uavs, mec_servers)

all_tasks   = []
sim_time    = 0.0

# ── Simulation loop ───────────────────────────────────────────────────────────
while viz.running and sim_time < TOTAL_SIM_TIME:

    # 1. Generate new tasks
    new_tasks = gen.generate_tasks(sim_time, TIMESTEP)
    for t in new_tasks:
        world.register_task_to_region(t)
    all_tasks.extend(new_tasks)

    # 2. Assign pending tasks to nearest UAV
    pending = [t for t in all_tasks if t.status == "PENDING"]
    for task in pending:
        best_uav  = None
        best_dist = float("inf")
        for uav in uavs:
            if uav.battery_status == "EMERGENCY":
                continue
            dist = np.linalg.norm(
                np.array([task.location[0], task.location[1]]) - uav.position[:2])
            if dist < best_dist:
                best_dist = dist
                best_uav  = uav
        if best_uav:
            task.status          = "ASSIGNED"
            task.assigned_uav    = best_uav.id
            best_uav.current_task = task

    # 3. Move UAVs toward their assigned task
    for uav in uavs:
        if uav.current_task and uav.current_task.status == "ASSIGNED":
            target = [uav.current_task.location[0],
                      uav.current_task.location[1], 50]
            uav.move_towards(target, TIMESTEP)

            # Check if arrived
            dist = np.linalg.norm(
                np.array(target[:2]) - uav.position[:2])
            if dist < 20:
                uav.current_task.status = "DONE"
                region = world.get_region_of_position(
                    uav.current_task.location[0],
                    uav.current_task.location[1])
                region.remove_task(uav.current_task)
                uav.current_task = None

        # Drain battery
        uav.drain_battery(TIMESTEP)

    # 4. Update world state
    world.tick(uavs)

    # 5. Render
    viz.render(all_tasks, sim_time)
    viz.tick(fps=60)

    sim_time += TIMESTEP * VIZ_SPEED

viz.close()
print("Simulation ended.")