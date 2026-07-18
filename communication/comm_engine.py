
import math
import numpy as np
from configs import config


def compute_distance(pos_a, pos_b):
    a = np.array(pos_a, dtype=float)
    b = np.array(pos_b, dtype=float)
    return float(np.linalg.norm(a - b))


def compute_snr(distance_m, weather_factor):
    distance_m = max(distance_m, 1.0)
    snr = (config.TX_POWER_W * weather_factor) / (config.NOISE_POWER_W * (distance_m ** 2.5))
    return max(snr, 1e-12)


def compute_data_rate(snr):
    # Shannon capacity: R = B * log2(1 + SNR), converted to MB/s
    bits_per_sec = config.BANDWIDTH_HZ * math.log2(1.0 + snr)
    mb_per_sec = bits_per_sec / (8 * 1e6)
    return max(mb_per_sec, 1e-6)


def can_communicate(pos_a, pos_b):
    return compute_distance(pos_a, pos_b) <= config.COMM_RANGE


class CommLink:
    def __init__(self, node_a, node_b):
        self.node_a = node_a
        self.node_b = node_b
        self.distance = None
        self.active = False
        self.snr = None
        self.data_rate = None

    def _pos(self, node):
        if isinstance(node, dict):
            return node["position"]
        return node.position

    def update(self, weather_factor=1.0):
        pos_a = self._pos(self.node_a)
        pos_b = self._pos(self.node_b)
        self.distance = compute_distance(pos_a, pos_b)
        self.active = self.distance <= config.COMM_RANGE
        if self.active:
            self.snr = compute_snr(self.distance, weather_factor)
            self.data_rate = compute_data_rate(self.snr)
        else:
            self.snr = 0.0
            self.data_rate = 0.0
        return self
