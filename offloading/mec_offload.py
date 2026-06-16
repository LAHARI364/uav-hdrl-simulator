"""
Phase 10 — MEC Offloading Engine

Models task offloading latency:
    T_total = T_upload + T_queue + T_compute + T_download

Decides whether local UAV execution or MEC offloading is faster.
"""

import numpy as np
from configs.config import (
    MEC_CPU_FREQUENCY, MEC_QUEUE_DELAY, DOWNLOAD_RATE_MBPS
)
from communication.comm_engine import CommLink, can_communicate


class MECServer:
    """Represents a ground-based MEC server co-located with a charging station."""

    def __init__(self, server_id, position, cpu_freq=MEC_CPU_FREQUENCY):
        self.server_id  = server_id
        self.position   = position          # [x, y]  (altitude = 0)
        self.cpu_freq   = cpu_freq          # Hz
        self.task_queue = []                # tasks currently offloaded here
        self.busy_until = 0.0              # simulation time when server is free

    def queue_length(self):
        return len(self.task_queue)

    def estimated_queue_delay(self, current_time):
        """How long a new task would have to wait if submitted right now."""
        wait = max(self.busy_until - current_time, 0.0)
        return wait + MEC_QUEUE_DELAY      # base overhead + backlog

    def compute_time(self, cpu_cycles):
        """T_compute = cpu_cycles / server_cpu_frequency"""
        return cpu_cycles / self.cpu_freq

    def __repr__(self):
        return (f"MECServer({self.server_id}) | "
                f"Queue: {self.queue_length()} tasks | "
                f"CPU: {self.cpu_freq/1e9:.1f} GHz")


def offload_latency(task, uav, mec_server, current_time, weather_factor=1.0):
    """
    Compute total offloading latency for a task from a UAV to a MEC server.

    Parameters
    ----------
    task          : Task
    uav           : UAV
    mec_server    : MECServer
    current_time  : float
    weather_factor: float [0,1]

    Returns
    -------
    dict with all latency components and total, or None if out of range.
    """
    # Build a comm link: UAV → MEC
    mec_node = {"position": mec_server.position}
    link     = CommLink(uav, mec_node).update(weather_factor)

    if not link.active:
        return None   # Cannot reach this MEC server

    # ── T_upload = data_size / upload_rate ───────────────────────────────────
    upload_rate = link.data_rate          # MB/s  (Shannon limited)
    if upload_rate <= 0:
        return None
    t_upload    = task.data_size / upload_rate

    # ── T_queue  = estimated wait at MEC ─────────────────────────────────────
    t_queue     = mec_server.estimated_queue_delay(current_time)

    # ── T_compute = cpu_cycles / mec_cpu ─────────────────────────────────────
    t_compute   = mec_server.compute_time(task.cpu_cycles)

    # ── T_download = result_size / download_rate ──────────────────────────────
    # Assume result payload is 10% of input data
    result_size = task.data_size * 0.1
    t_download  = result_size / DOWNLOAD_RATE_MBPS

    t_total = t_upload + t_queue + t_compute + t_download

    return {
        "mec_server_id": mec_server.server_id,
        "t_upload":   t_upload,
        "t_queue":    t_queue,
        "t_compute":  t_compute,
        "t_download": t_download,
        "t_total":    t_total,
        "data_rate":  link.data_rate,
        "distance_m": link.distance,
    }


def local_execution_time(task, uav):
    """
    Time to execute the task locally on the UAV's CPU.
    UAV CPU is modelled simply as cpu_capacity * 1 GHz.
    """
    uav_cpu_hz = uav.cpu_capacity * 1e9   # cpu_capacity in GHz → Hz
    return task.cpu_cycles / uav_cpu_hz


def decide_offload(task, uav, mec_servers, current_time, weather_factor=1.0):
    """
    Compare local execution vs all reachable MEC servers.
    Returns the best decision as a dict.

    decision dict keys:
        "strategy"   : "LOCAL" | "MEC"
        "mec_server" : MECServer | None
        "latency"    : float (seconds)
        "details"    : full breakdown dict | None
    """
    t_local  = local_execution_time(task, uav)
    best     = {"strategy": "LOCAL", "mec_server": None,
                "latency": t_local, "details": None}

    for server in mec_servers:
        result = offload_latency(task, uav, server, current_time, weather_factor)
        if result and result["t_total"] < best["latency"]:
            best = {
                "strategy":   "MEC",
                "mec_server": server,
                "latency":    result["t_total"],
                "details":    result,
            }

    return best
