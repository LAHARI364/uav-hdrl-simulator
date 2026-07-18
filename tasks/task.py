

class Task:
    def __init__(
        self,
        task_id,
        location,
        cpu_cycles,
        deadline,
        priority,
        data_size,
        task_type,
        arrival_time,
    ):
        self.task_id = task_id
        self.location = location            # [x, y]
        self.cpu_cycles = cpu_cycles
        self.deadline = deadline            # seconds from arrival until task fails
        self.priority = priority            # 'low' / 'medium' / 'high' / 'emergency'
        self.data_size = data_size          # MB
        self.task_type = task_type          # 'normal' or 'emergency'
        self.status = "PENDING"             # PENDING -> ASSIGNED -> DONE / FAILED
        self.assigned_uav = None
        self.arrival_time = arrival_time
        self.region_id = None               # set by map.register_task_to_region
        self.numeric_priority = 0.0         # set by priority_engine
