import numpy as np
from tasks.task import Task
from configs.config import (MAP_WIDTH, MAP_HEIGHT, TASK_ARRIVAL_RATE, PRIORITY_DISTRIBUTION, NUM_EMERGENCY_EVENTS, TOTAL_SIM_TIME)

class TaskGenerator:
    def __init__(self):
        self.task_counter = 0
        self.emergency_counter = 0
        self.max_emergencies = NUM_EMERGENCY_EVENTS
        # Pre-schedule emergency event times randomly
        self.emergency_times = sorted(
            np.random.uniform(0, TOTAL_SIM_TIME, NUM_EMERGENCY_EVENTS)
        )

    def generate_tasks(self, current_time, dt):
        new_tasks = []

        # Normal tasks via Poisson
        num_tasks = np.random.poisson(TASK_ARRIVAL_RATE * dt)
        for _ in range(num_tasks):
            task = self._create_task(current_time, task_type="normal")
            new_tasks.append(task)

        # Emergency tasks at pre-scheduled times
        for etime in self.emergency_times[:]:
            if abs(current_time - etime) < dt:
                task = self._create_task(current_time, task_type="emergency")
                new_tasks.append(task)
                self.emergency_times.remove(etime)

        return new_tasks

    def _create_task(self, current_time, task_type="normal"):
        self.task_counter += 1

        # Random location anywhere on map
        x = np.random.uniform(0, MAP_WIDTH)
        y = np.random.uniform(0, MAP_HEIGHT)

        if task_type == "emergency":
            priority = "emergency"
            deadline = np.random.uniform(5, 15)
            cpu_cycles = np.random.uniform(1e6, 5e6)
        else:
            priority = self._sample_priority()
            deadline = np.random.uniform(10, 60)
            cpu_cycles = np.random.uniform(1e5, 1e6)

        data_size = np.random.uniform(0.5, 5.0)  # MB

        task = Task(
            task_id=self.task_counter,
            location=[x, y],
            cpu_cycles=cpu_cycles,
            deadline=deadline,
            priority=priority,
            data_size=data_size,
            task_type=task_type
        )
        task.arrival_time = current_time
        return task

    def _sample_priority(self):
        r = np.random.random()
        if r < PRIORITY_DISTRIBUTION["low"]:
            return "low"
        elif r < PRIORITY_DISTRIBUTION["low"] + PRIORITY_DISTRIBUTION["medium"]:
            return "medium"
        else:
            return "high"