"""
Phase 9b — Task Scheduling Engine.

Separate from Assignment (who gets a task) and distinct from it per the
design docs: a UAV can hold several ASSIGNED tasks in task_queue at
once, and this picks which one it's actively executing right now —
highest current priority, re-evaluated every tick (not FIFO).

Preemption rule: only swap the active task while the UAV is still
travelling (compute_timer == 0). Once it starts computing (hovering,
compute_timer > 0) it finishes that one first — avoids wasting
in-progress compute work every time a new higher-priority task arrives.
"""

def schedule_uav_tasks(uavs):
    for uav in uavs:
        if not uav.task_queue:
            uav.current_task = None
            continue

        if uav.compute_timer > 0:
            continue  # busy computing — keep current_task as-is

        uav.task_queue.sort(key=lambda t: getattr(t, "numeric_priority", 0.0), reverse=True)
        uav.current_task = uav.task_queue[0]