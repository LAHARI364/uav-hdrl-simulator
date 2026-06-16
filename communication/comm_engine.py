"""
Phase 7 — Communication Engine
Computes 3-D distance, SNR, and Shannon data rate between two UAVs
(or a UAV and a ground MEC node).
"""

import numpy as np
from configs.config import (
    BANDWIDTH_HZ, TRANSMIT_POWER_W,
    NOISE_POWER_W, PATH_LOSS_EXPONENT, COMM_RANGE
)


def compute_distance(pos_a, pos_b):
    """
    3-D Euclidean distance.
    pos_a, pos_b: array-like [x, y, z]
    
    d = sqrt((x1-x2)^2 + (y1-y2)^2 + (z1-z2)^2)
    """
    a = np.array(pos_a, dtype=float)
    b = np.array(pos_b, dtype=float)
    return float(np.linalg.norm(a - b))


def compute_snr(distance_m, weather_factor=1.0):
    """
    Signal-to-Noise Ratio using a simplified path-loss model.

    SNR = P_tx / (noise * distance^path_loss_exponent)
    
    weather_factor : float [0,1] — 1.0 = clear sky, <1.0 = degraded by storm
    """
    if distance_m < 1.0:
        distance_m = 1.0  # avoid division by zero

    path_loss  = (distance_m ** PATH_LOSS_EXPONENT)
    received_p = (TRANSMIT_POWER_W * weather_factor) / path_loss
    snr        = received_p / NOISE_POWER_W
    return float(snr)


def compute_data_rate(snr):
    """
    Shannon capacity: R = B * log2(1 + SNR)   [bits/s]
    Returns rate in MB/s for convenience.
    """
    if snr <= 0:
        return 0.0
    rate_bps  = BANDWIDTH_HZ * np.log2(1.0 + snr)
    rate_mbps = rate_bps / (8 * 1e6)   # convert bits/s → MB/s
    return float(rate_mbps)


def can_communicate(pos_a, pos_b):
    """Returns True if two nodes are within COMM_RANGE."""
    return compute_distance(pos_a, pos_b) <= COMM_RANGE


class CommLink:
    """
    Represents a live communication link between two nodes.
    A 'node' is anything with a .position attribute (UAV, MEC server dict).
    """

    def __init__(self, node_a, node_b):
        self.node_a = node_a
        self.node_b = node_b

    def _get_pos(self, node):
        if isinstance(node, dict):
            pos = node["position"]
            # MEC ground nodes → altitude 0
            return [pos[0], pos[1], 0.0]
        return node.position   # UAV

    def update(self, weather_factor=1.0):
        """
        Recompute link quality for this timestep.
        Call once per tick for active links.
        """
        pos_a = self._get_pos(self.node_a)
        pos_b = self._get_pos(self.node_b)

        self.distance   = compute_distance(pos_a, pos_b)
        self.active     = self.distance <= COMM_RANGE
        self.snr        = compute_snr(self.distance, weather_factor) if self.active else 0.0
        self.data_rate  = compute_data_rate(self.snr)   # MB/s
        return self

    def __repr__(self):
        status = "ACTIVE" if self.active else "OUT_OF_RANGE"
        return (f"CommLink [{status}] | "
                f"dist={self.distance:.1f}m | "
                f"SNR={self.snr:.2f} | "
                f"Rate={self.data_rate:.3f} MB/s")