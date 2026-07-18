
import random
import numpy as np

from configs import config
from environment.map import Map
from uavs.uav import UAV
from offloading.mec_offload import MECServer
from tasks.task_generator import TaskGenerator
from tasks.priority_engine import rank_tasks
from offloading.mec_offload import decide_offload
from weatherr.weather_engine import WeatherSystem
from visualization.sim_viz import SimVisualizer


def random_position(world):
    x = random.uniform(0, config.MAP_WIDTH)
    y = random.uniform(0, config.MAP_HEIGHT)
    return np.array([x, y, 0.0])


def main():
    world = Map()
    uavs = [UAV(i, random_position(world)) for i in range(config.NUM_UAVS)]
    mec_servers = [
        MECServer(i, cs["position"]) for i, cs in enumerate(world.charging_stations)
    ]
    gen = TaskGenerator(world)
    weather = WeatherSystem("data/historical_storm.csv")
    viz = SimVisualizer(world, uavs, mec_servers)

    all_tasks = []
    sim_time = 0.0

    while viz.running and sim_time < config.TOTAL_SIM_TIME:
        # Step 1 -- Weather tick
        weather.tick(config.TIMESTEP)
        weather.update_regions(world)

        # Step 2 -- Generate tasks
        new_tasks = gen.generate_tasks(sim_time, config.TIMESTEP)
        for t in new_tasks:
            world.register_task_to_region(t)
        all_tasks.extend(new_tasks)

        # Step 3 -- Assign tasks (nearest free, non-charging UAV)
        pending = [t for t in all_tasks if t.status == "PENDING"]
        if pending:
            ranked = rank_tasks(pending, uavs[0] if uavs else None, sim_time, world)
            for task in ranked:
                free_uavs = [
                    u
                    for u in uavs
                    if u.current_task is None
                    and u.battery_status not in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD")
                ]
                if not free_uavs:
                    break
                nearest = min(free_uavs, key=lambda u: u.distance_to(task.location))
                nearest.current_task = task
                task.status = "ASSIGNED"
                task.assigned_uav = nearest.id

        # Step 4 -- Move UAVs and compute
        for uav in uavs:
            if uav.battery_status in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD"):
                if uav.current_task is not None:
                    uav.current_task.status = "PENDING"
                    uav.current_task.assigned_uav = None
                    uav.current_task = None
                    uav.compute_timer = 0.0
                    uav.is_communicating = False
            elif uav.current_task is not None:
                task = uav.current_task
                distance = uav.distance_to(task.location)
                if distance > 20.0:
                    uav.flight_mode = "CRUISE"
                    uav.move_towards(task.location, config.TIMESTEP)
                else:
                    if uav.compute_timer <= 0.0 and uav.cpu_utilization == 0.0:
                        weather_factor = 1.0 - (uav.current_region.weather_severity if uav.current_region else 0.0)
                        decision = decide_offload(task, uav, mec_servers, sim_time, weather_factor)
                        uav.compute_timer = decision["latency"]
                        uav.flight_mode = "HOVER"
                        uav.cpu_utilization = 0.0 if decision["strategy"] == "MEC" else 0.8
                        uav.is_communicating = decision["strategy"] == "MEC"
                        if decision["strategy"] == "MEC" and decision["mec_server"] is not None:
                            server = decision["mec_server"]
                            server.busy_until = sim_time + decision["details"]["t_compute"]
                    else:
                        uav.compute_timer -= config.TIMESTEP
                        if uav.compute_timer <= 0.0:
                            task.status = "DONE"
                            if task.region_id is not None:
                                world.regions[task.region_id].remove_task(task)
                            uav.current_task = None
                            uav.cpu_utilization = 0.0
                            uav.is_communicating = False
                            uav.flight_mode = "CRUISE"

        # Step 5 -- Battery drain
        for uav in uavs:
            weather_factor = 1.0 - (uav.current_region.weather_severity if uav.current_region else 0.0)
            uav.drain_battery(config.TIMESTEP, weather_factor)

        # Step 6 -- Charging logic
        for uav in uavs:
            if uav.battery_status in ("WARNING", "CRITICAL", "EMERGENCY", "DEAD"):
                station = min(
                    world.charging_stations,
                    key=lambda cs: uav.distance_to(cs["position"]),
                )
                dist = uav.distance_to(station["position"])
                if dist > 20.0:
                    uav.flight_mode = "EMERGENCY_DESCENT"
                    uav.move_towards(station["position"], config.TIMESTEP)
                else:
                    uav.flight_mode = "HOVER"
                    uav.velocity[:] = 0.0
                    uav.battery_soc = min(
                        uav.battery_soc + config.CHARGING_RATE * config.TIMESTEP, 100.0
                    )
                    uav.update_battery_state()
                    if uav.battery_soc >= 80.0:
                        uav.flight_mode = "CRUISE"

        # Step 7 -- World + render
        world.tick(uavs)
        viz.render(all_tasks, sim_time)
        viz.tick(fps=60)
        sim_time += config.TIMESTEP * config.VIZ_SPEED

    # Final summary
    done = sum(1 for t in all_tasks if t.status == "DONE")
    print(f"\nSimulation ended at t={sim_time:.1f}s")
    print(f"Total tasks: {len(all_tasks)} | Done: {done} | Pending/Assigned: {len(all_tasks) - done}")


if __name__ == "__main__":
    main()
