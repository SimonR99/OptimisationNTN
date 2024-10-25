from typing import Union

import numpy as np

from ..nodes.base_node import BaseNode


class CommunicationLink:
    def __init__(
        self,
        node_a: Union[BaseNode, None],
        node_b: Union[BaseNode, None],
        bandwidth: float,
        signal_power: float,
        noise_power: float,
    ):
        self.bandwidth = bandwidth
        self.signal_power = signal_power
        self.noise_power = noise_power
        self.capacity = self.calculate_capacity()
        self.path_loss = None  # TODO : Add path loss calcul base on node type

    def calculate_capacity(self):
        snr = self.signal_power / self.noise_power
        capacity = self.bandwidth * np.log2(1 + snr)
        return capacity
