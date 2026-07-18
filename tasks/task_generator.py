
import random
import numpy as np
from configs import config
from tasks.task import Task


class TaskGenerator:
    def __init__(self, world_map):
        self.world_map = world_map
        self._next_task_id = 0

        # Build region_probs weighted by workload (for reference / future use,
        # e.g. by an HDRL agent). Actual spawning uses per-region Poisson lambda.
        weights = {
            r.region_id: config.WORKLOAD_WEIGHTS[r.workload] for r in world_map.regions
        }
        total_weight = sum(weights.values())
        self.region_probs = {rid: w / total_weight for rid, w in weights.items()}

        # Pre-schedule emergency event times across the sim.
        self.emergency_times = sorted(
            random.uniform(5.0, config.TOTAL_SIM_TIME - 5.0)
            for _ in range(config.NUM_EMERGENCY_EVENTS)
        )
        self._fired_emergencies = set()

    def generate_tasks(self, current_time, dt):
        new_tasks = []

        for region in self.world_map.regions:
            lam = config.TASK_ARRIVAL_RATE.get(region.region_id, 0.0)
            num_tasks = np.random.poisson(lam * dt)
            for _ in range(num_tasks):
                new_tasks.append(self._create_task(current_time, region.region_id, "normal"))

        # Fire any pre-scheduled emergency events whose time has arrived.
        for idx, t_emergency in enumerate(self.emergency_times):
            if idx in self._fired_emergencies:
                continue
            if current_time >= t_emergency:
                new_tasks.append(self._create_task(current_time, None, "emergency"))
                self._fired_emergencies.add(idx)

        return new_tasks

    def _create_task(self, current_time, region_id, task_type):
        if task_type == "emergency":
            x = random.uniform(0, config.MAP_WIDTH)
            y = random.uniform(0, config.MAP_HEIGHT)
            cpu_cycles = random.uniform(*config.EMERGENCY_CPU_CYCLES_RANGE)
            deadline = random.uniform(*config.EMERGENCY_DEADLINE_RANGE)
            data_size = random.uniform(*config.EMERGENCY_DATA_SIZE_RANGE)
            priority = "emergency"
        else:
            region = self.world_map.regions[region_id]
            x = random.uniform(region.x_start, region.x_start + region.width)
            y = random.uniform(region.y_start, region.y_start + region.height)
            cpu_cycles = random.uniform(*config.NORMAL_CPU_CYCLES_RANGE)
            deadline = random.uniform(*config.NORMAL_DEADLINE_RANGE)
            data_size = random.uniform(*config.NORMAL_DATA_SIZE_RANGE)
            priority = self._sample_priority()

        task = Task(
            task_id=self._next_task_id,
            location=[x, y],
            cpu_cycles=cpu_cycles,
            deadline=deadline,
            priority=priority,
            data_size=data_size,
            task_type=task_type,
            arrival_time=current_time,
        )
        self._next_task_id += 1
        return task

    def _sample_priority(self):
        roll = random.random()
        cumulative = 0.0
        for label, prob in config.PRIORITY_DISTRIBUTION.items():
            cumulative += prob
            if roll <= cumulative:
                return label
        return "low"
