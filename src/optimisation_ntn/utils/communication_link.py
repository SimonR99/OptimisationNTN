from typing import Union

import numpy as np

from optimisation_ntn.nodes.base_node import BaseNode


class CommunicationLink:
    def __init__(
        self,
        node_a: Union[BaseNode, None],
        node_b: Union[BaseNode, None],
        bandwidth: float,
        signal_power: float,
        noise_power: float,
    ):
        self.node_a = node_a
        self.node_b = node_b
        self.bandwidth = bandwidth
        self.signal_power = signal_power
        self.noise_power = noise_power
        self.capacity = self.calculate_capacity()
        self.path_loss = None  # TODO : Add path loss calcul base on node type

    @property
    def link_length(self):
        if self.node_a is None or self.node_b is None:
            return None
        return np.sqrt(
            (self.node_a.position.x - self.node_b.position.x) ** 2
            + (self.node_a.position.y - self.node_b.position.y) ** 2
        )

    def calculate_capacity(self):
        snr = self.signal_power / self.noise_power
        capacity = self.bandwidth * np.log2(1 + snr)
        return capacity
