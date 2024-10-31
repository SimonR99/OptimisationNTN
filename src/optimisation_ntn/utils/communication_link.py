from typing import Union
from urllib.request import Request

import numpy as np

from optimisation_ntn.nodes.leo import LEO

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
        self.node_a = node_a
        self.node_b = node_b
        self.bandwidth = bandwidth
        self.signal_power = signal_power
        self.noise_power = noise_power
        self.capacity = self.calculate_capacity()

        # Leo to Haps link
        if isinstance(node_a, LEO) or node_b is isinstance(node_b, LEO):
            self.path_loss = 1
        else:  # Other link
            self.path_loss = 2

        self.transmission_queue: list[Request] = []  # FIFO queue

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

    def add_to_queue(self, request: Request):
        self.transmission_queue.append(request)

    def tick(self, time: float):
        pass  # TODO : Deliver one packet at the time, when shannon is done for a packet, deliver the next one
