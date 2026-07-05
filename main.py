# main.py
from environment.map import Map
from uavs.uav import UAV
from tasks.task_generator import TaskGenerator
from tasks.priority_engine import rank_tasks
from offloading.mec_offload import MECServer, decide_offload
from visualization.sim_viz import SimVisualizer
from weatherr.weather_engine import WeatherSystem
from configs.config import (
    NUM_UAVS, TOTAL_SIM_TIME, TIMESTEP,
    MAP_WIDTH, MAP_HEIGHT, VIZ_SPEED,
    CHARGING_RATE, MAX_BATTERY, WEATHER_SPEEDUP,
    CHARGING_STATION_CAPACITY
)
import numpy as np

# ── Init world ────────────────────────────────────────────────────────────────
world = Map()
uavs = [UAV(i, [np.random.uniform(0, MAP_WIDTH),
              np.random.uniform(0, MAP_HEIGHT), 50])
        for i in range(NUM_UAVS)]

mec_servers = [MECServer(i, cs["position"])
               for i, cs in enumerate(world.charging_stations)]

gen = TaskGenerator()
weather = WeatherSystem()          # loads data/historical_storm.csv
viz = SimVisualizer(world, uavs, mec_servers)

all_tasks = []
sim_time = 0.0


def choose_station(uav, stations, uavs, capacity):
    """Pick the nearest charging station that isn't over capacity.
    If every station is full, fall back to the least-crowded one."""
    pos2d = uav.position[:2]
    candidates = []
    for cs in stations:
        occupants = sum(
            1 for other in uavs
            if other is not uav
            and other.is_charging
            and other.target_station is cs
        )
        dist = np.linalg.norm(np.array(cs["position"]) - pos2d)
        candidates.append((cs, dist, occupants))

    free = [c for c in candidates if c[2] < capacity]
    pool = free if free else candidates          # all full → take least-bad option
    best = min(pool, key=lambda c: (c[2], c[1]))  # prefer free, then nearest
    return best[0], best[1]


# ── Simulation loop ───────────────────────────────────────────────────────────
while viz.running and sim_time < TOTAL_SIM_TIME:

    # 1. Weather tick — compress the full historical storm timeline into
    #    the simulation window so severity actually changes over the run
    weather.tick(TIMESTEP * WEATHER_SPEEDUP)
    weather.update_regions(world)

    # Debug: uncomment to confirm weather is actually advancing
    # if int(sim_time * 10) % 20 == 0:
    #     print(f"t={weather.sim_time:.0f}s  rain={weather.current_precipitation:.2f}mm  wind={weather.current_wind_speed:.2f}kph")

    # 2. Generate new tasks
    new_tasks = gen.generate_tasks(sim_time, TIMESTEP)
    for t in new_tasks:
        world.register_task_to_region(t)
    all_tasks.extend(new_tasks)

    # 3. Assign pending tasks to the nearest FREE, HEALTHY UAV
    #    (UAVs mid-charge-cycle are skipped even once their SOC has
    #    climbed back above the WARNING threshold — they stay off-duty
    #    until they've charged all the way to MAX_BATTERY)
    pending = [t for t in all_tasks if t.status == "PENDING"]
    for task in pending:
        best_uav, best_dist = None, float("inf")
        for uav in uavs:
            if uav.is_charging:
                continue
            if uav.current_task is not None:
                continue
            dist = np.linalg.norm(
                np.array([task.location[0], task.location[1]]) - uav.position[:2])
            if dist < best_dist:
                best_dist, best_uav = dist, uav
        if best_uav:
            task.status = "ASSIGNED"
            task.assigned_uav = best_uav.id
            best_uav.current_task = task

    # 4. Move UAVs — charge to full if low battery, otherwise work the task
    #    (this is its own top-level step, not nested inside Step 3)
    for uav in uavs:
        # Start a charging cycle the moment battery drops critical-low
        if uav.battery_status in ("WARNING", "CRITICAL", "EMERGENCY") and not uav.is_charging:
            uav.is_charging = True
            if uav.current_task is not None:
                uav.current_task.status = "PENDING"
                uav.current_task.assigned_uav = None
                uav.current_task = None

        if uav.is_charging:
            if uav.target_station is None:
                uav.target_station, _ = choose_station(
                    uav, world.charging_stations, uavs, CHARGING_STATION_CAPACITY)

            station = uav.target_station
            dist = np.linalg.norm(np.array(station["position"]) - uav.position[:2])

            if dist > 20:
                uav.flight_mode = "EMERGENCY_DESCENT"
                target = [station["position"][0], station["position"][1], 50]
                uav.move_towards(target, TIMESTEP)
            else:
                uav.flight_mode = "HOVER"
                uav.battery_soc = min(MAX_BATTERY, uav.battery_soc + CHARGING_RATE * TIMESTEP)
                uav.update_battery_state()

                # Only released once charged all the way to 100%
                if uav.battery_soc >= MAX_BATTERY:
                    uav.is_charging = False
                    uav.target_station = None
                    uav.flight_mode = "CRUISE"

        else:
            if uav.current_task and uav.current_task.status == "ASSIGNED":
                target = [uav.current_task.location[0],
                          uav.current_task.location[1], 50]
                uav.move_towards(target, TIMESTEP)

                dist = np.linalg.norm(np.array(target[:2]) - uav.position[:2])
                if dist < 20:
                    uav.current_task.status = "DONE"
                    region = world.get_region_of_position(
                        uav.current_task.location[0],
                        uav.current_task.location[1])
                    region.remove_task(uav.current_task)
                    uav.current_task = None

        # Drain battery — weather-aware (bad weather in the UAV's region
        # increases drain, per battery_engine.update_soc's weather_factor)
        weather_factor = 1.0
        if uav.current_region is not None:
            weather_factor = 1.0 - uav.current_region.weather_severity
        uav.drain_battery(TIMESTEP, weather_factor)

    # 5. Update world state (uav counts, congestion, current_region refs)
    world.tick(uavs)

    # 6. Render
    viz.render(all_tasks, sim_time)
    viz.tick(fps=60)
    sim_time += TIMESTEP * VIZ_SPEED

viz.close()
print("Simulation ended.")