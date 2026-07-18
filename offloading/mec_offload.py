
import numpy as np
from configs import config
from communication.comm_engine import CommLink


class MECServer:
    def __init__(self, server_id, position):
        self.server_id = server_id
        self.position = np.array(position, dtype=float)
        self.cpu_freq = config.MEC_CPU_FREQUENCY
        self.task_queue = []
        self.busy_until = 0.0

    def estimated_queue_delay(self, current_time):
        return max(self.busy_until - current_time, 0.0) + config.MEC_QUEUE_DELAY

    def compute_time(self, cpu_cycles):
        return cpu_cycles / (self.cpu_freq * 1e9)


def offload_latency(task, uav, mec_server, current_time, weather_factor):
    link = CommLink(uav, mec_server).update(weather_factor)
    if not link.active:
        return None

    t_upload = task.data_size / link.data_rate
    t_queue = mec_server.estimated_queue_delay(current_time)
    t_compute = task.cpu_cycles / (config.MEC_CPU_FREQUENCY * 1e9)
    t_download = (task.data_size * 0.1) / config.DOWNLOAD_RATE_MBPS
    t_total = t_upload + t_queue + t_compute + t_download

    return {
        "t_upload": t_upload,
        "t_queue": t_queue,
        "t_compute": t_compute,
        "t_download": t_download,
        "t_total": t_total,
    }


def local_execution_time(task, uav):
    return task.cpu_cycles / (uav.cpu_capacity * 1e9)


def decide_offload(task, uav, mec_servers, current_time, weather_factor):
    local_time = local_execution_time(task, uav)
    best = {"strategy": "LOCAL", "mec_server": None, "latency": local_time, "details": None}

    for server in mec_servers:
        result = offload_latency(task, uav, server, current_time, weather_factor)
        if result is None:
            continue
        if result["t_total"] < best["latency"]:
            best = {
                "strategy": "MEC",
                "mec_server": server,
                "latency": result["t_total"],
                "details": result,
            }

    return best
