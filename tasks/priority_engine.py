

from configs import config


def compute_priority(task, uav, current_time, region_congestion, weather_severity):
    time_remaining = task.deadline - (current_time - task.arrival_time)
    deadline_score = 1.0 - max(min(time_remaining / task.deadline, 1.0), 0.0)

    battery_score = 1.0 - (uav.battery_soc / 100.0) if uav is not None else 0.0
    weather_score = weather_severity
    queue_score = region_congestion
    importance_score = config.IMPORTANCE_BASE.get(task.priority, 0.2)

    w = config.PRIORITY_WEIGHTS
    score = (
        w["deadline"] * deadline_score
        + w["battery"] * battery_score
        + w["weather"] * weather_score
        + w["queue"] * queue_score
        + w["importance"] * importance_score
    )
    score = max(0.0, min(score, 1.0))
    task.numeric_priority = score
    return score


def rank_tasks(tasks, uav, current_time, world):
    for task in tasks:
        region = world.regions[task.region_id] if task.region_id is not None else None
        congestion = region.congestion if region else 0.0
        weather = region.weather_severity if region else 0.0
        compute_priority(task, uav, current_time, congestion, weather)
    return sorted(tasks, key=lambda t: t.numeric_priority, reverse=True)
