from environment.map import Map
from uavs.uav import UAV
from tasks.task_generator import TaskGenerator
import numpy as np

# Map
world = Map()
print(world)
for r in world.regions[:4]:
    print(r)

# UAVs
uavs = [UAV(i, position=[np.random.uniform(0, 10000),
                          np.random.uniform(0, 10000), 50]) for i in range(3)]
for u in uavs:
    print(u)

# Tasks
gen = TaskGenerator()
tasks = gen.generate_tasks(current_time=0.0, dt=1.0)
print("Number of tasks:", len(tasks))
for t in tasks:
    print(t)
