import numpy as np


def shannon_capacity(bandwidth, signal_power, noise_power):
    snr = signal_power / noise_power
    capacity = bandwidth * np.log2(1 + snr)
    return capacity
