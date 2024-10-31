from typing import List

import numpy as np

from optimisation_ntn.utils.earth import Earth

from ..nodes.base_node import BaseNode
from ..request import Request


class CommunicationLink:
    def __init__(
        self,
        node_a: BaseNode,
        node_b: BaseNode,
        total_bandwidth: float,
        signal_power: float,
        carrier_frequency: float,
    ):
        self.node_a = node_a
        self.node_b = node_b
        self.total_bandwidth = total_bandwidth
        self.signal_power = signal_power
        self.carrier_frequency = carrier_frequency
        self.transmission_queue: list[Request] = []  # FIFO queue

        # Identify compatible antennas for communication
        self.antenna_a, self.antenna_b = self.find_compatible_antennas()

        if not self.antenna_a or not self.antenna_b:
            raise ValueError(
                f"No compatible antennas found between {node_a} and {node_b}"
            )

    def find_compatible_antennas(self):
        """Finds and returns a pair of compatible antennas between the two nodes."""
        for antenna_a in self.node_a.antennas:
            antenna_b = self.node_b.get_compatible_antenna(antenna_a)
            if antenna_b:
                return antenna_a, antenna_b
        return None, None

    @property
    def link_length(self) -> float:
        """Calculates the distance between node_a and node_b."""
        return np.sqrt(
            (self.node_a.position.x - self.node_b.position.x) ** 2
            + (self.node_a.position.y - self.node_b.position.y) ** 2
        )

    @property
    def noise_power(self) -> float:
        """Calculates noise power based on the receiver's spectral noise density."""
        spectral_noise_density = (
            self.node_b.spectral_noise_density
        )  # Assumes node_b is the receiver
        return spectral_noise_density * self.adjusted_bandwidth

    @property
    def adjusted_bandwidth(self) -> float:
        """Adjusts bandwidth based on the number of active links with the same type."""
        active_count = self.node_b.get_active_count(type(self.node_a))
        return self.total_bandwidth / max(1, active_count)

    def calculate_fspl(self) -> float:
        """Calculates Free-Space Path Loss (FSPL) for the link."""
        return (
            4 * np.pi * self.link_length * self.carrier_frequency / Earth.speed_of_light
        ) ** 2

    def calculate_snr(self) -> float:
        """Calculates the Signal-to-Noise Ratio (SNR) for the link."""
        fspl = self.calculate_fspl()
        # Use gains from compatible antennas
        return (self.signal_power * self.antenna_a.gain * self.antenna_b.gain) / (
            fspl * self.noise_power
        )

    def calculate_capacity(self) -> float:
        """Calculates the link capacity based on Shannon's formula using adjusted bandwidth."""
        snr = self.calculate_snr()
        return self.adjusted_bandwidth * np.log2(1 + snr)

    def add_to_queue(self, request: Request):
        """Adds a request to the transmission queue."""
        self.transmission_queue.append(request)

    def tick(self, time: float):
        """Processes requests in the queue, simulating packet delivery."""
        if self.transmission_queue:
            current_request = self.transmission_queue[
                0
            ]  # Get the first request in queue
            # Process the request (data_size is in bits for time calculation)
            capacity = self.calculate_capacity()
            transmission_time = current_request.data_size / capacity
            if time >= transmission_time:
                print(
                    f"Delivered {current_request} from {self.node_a} to {self.node_b}"
                )
                self.transmission_queue.pop(0)  # Remove the request after completion
                if not self.transmission_queue:
                    self.node_b.remove_active_link(
                        type(self.node_a)
                    )  # Decrement active link count
            else:
                print(
                    f"Processing {current_request} from {self.node_a} to {self.node_b}"
                )
