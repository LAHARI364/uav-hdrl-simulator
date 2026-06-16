class Task:
    def __init__(self, task_id, location, cpu_cycles, deadline, priority, data_size, task_type="NORMAL"):
        self.task_id = task_id
        self.location = location       # [x, y]
        self.cpu_cycles = cpu_cycles   # computation needed
        self.deadline = deadline       # (seconds)
        self.priority = priority       # 1 (low) to 10 (high)
        self.data_size = data_size     # MB
        self.task_type = task_type     # NORMAL, EMERGENCY
        self.status = "PENDING"        # PENDING, ASSIGNED, DONE, FAILED
        self.assigned_uav = None
        self.arrival_time = 0.0
        self.wait_time = 0.0
        self.region_id = None          # filled in by Map.register_task_to_region()
        self.numeric_priority = 0.0   # filled in by priority_engine

    def __repr__(self):
        return f"Task({self.task_id}) | Priority: {self.priority} | Status: {self.status} | Type: {self.task_type}"