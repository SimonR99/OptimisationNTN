from typing import List

import numpy as np

from ..nodes.base_node import BaseNode
from ..utils.earth import Earth
from .request import Request, RequestStatus


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
        self.transmission_queue: List[Request] = []  # FIFO queue
        self.request_progress = 0  # Track bits transmitted for the current request

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
    def adjusted_bandwidth(self) -> float:
        """Adjusts bandwidth based on the number of active links with the same type."""
        active_count = self.node_b.get_active_count(type(self.node_a))
        return self.total_bandwidth / max(1, active_count)

    @property
    def noise_power(self) -> float:
        """Calculates noise power based on the receiver's spectral noise density."""
        spectral_noise_density = (
            self.node_b.spectral_noise_density
        )  # Assumes node_b is the receiver
        return spectral_noise_density * self.adjusted_bandwidth

    def calculate_correction_factor(self) -> float:
        """Calculates the Receiver Antenna Height Correction Factor."""
        return(
            1.1 * np.log10(self.carrier_frequency) - 0.7 * self.antenna_b.height
            - (1.56 * np.log10(self.carrier_frequency) - 0.8)
        )
    
    def calculate_path_loss(self) -> float:
        """Calculates Path Loss NLOS (HATA Model) of the channel user-base station."""
        correction_factor = self.calculate_correction_factor
        return(
            69.55 + 26.16 * np.log10(self.carrier_frequency) - 13.82 * np.log10(self.antenna_a.height) - 
            correction_factor + 44.9 - 6.55 * np.log10(self.antenna_a.height) * np.log10(self.link_length)
        )

    def calculate_gain_base(self) -> float:
        """Calculates Gain of the channel user-base station."""
        path_loss = self.calculate_path_loss
        return (
            path_loss * np.abs(1) /self.link_length
        )
    
    def calculate_snr_base(self) -> float:
        """Calculates SNR (Signal to Noise Ration) of the channel user-base station."""
        return((self.signal_power * self.calculate_gain_base) / self.noise_power)

    def calculate_fspl(self) -> float:
        """Calculates Free-Space Path Loss (FSPL) for the link."""
        return (
            4 * np.pi * self.link_length * self.carrier_frequency / Earth.speed_of_light
        ) ** 2

    def calculate_snr_leo(self) -> float:
        """Calculates the Signal-to-Noise Ratio (SNR) for the link."""
        fspl = self.calculate_fspl()
        # Use gains from compatible antennas
        return (self.signal_power * self.antenna_a.gain * self.antenna_b.gain) / (
            fspl * self.noise_power
        )

    def calculate_capacity(self) -> float:
        """Calculates the link capacity based on Shannon's formula using adjusted bandwidth."""
        snr = self.calculate_snr_leo()
        # Reduce multiplier to make transmission more visible
        return self.adjusted_bandwidth * np.log2(1 + snr) * 100  # Reduced from 10000 to 100

    def add_to_queue(self, request: Request):
        """Adds a request to the transmission queue and resets progress tracking."""
        self.transmission_queue.append(request)
        self.request_progress = 0  # Initialize progress for the new request

    def tick(self, time: float):
        """Processes requests in the queue."""
        if self.transmission_queue:
            current_request = self.transmission_queue[0]
            capacity = self.calculate_capacity()
            bits_transmitted = capacity * time
            self.request_progress += bits_transmitted

            print(
                f"Link {self.node_a} -> {self.node_b}: Transmitting request {current_request.id} "
                f"({self.request_progress:.1f}/{current_request.size} bits)"
            )

            if self.request_progress >= current_request.size:
                print(
                    f"Request {current_request.id} completed transmission from {self.node_a} to {self.node_b}"
                )

                # Update request's current node and status
                current_request.current_node = self.node_b
                if self.node_b == current_request.target_node:
                    # Directly add to processing queue without intermediate state
                    self.node_b.add_request_to_process(current_request)
                else:
                    # Move to next node in path
                    current_request.path_index += 1
                    print(f"Request {current_request.id} moving to next node in path (index: {current_request.path_index})")

                self.transmission_queue.pop(0)
                self.request_progress = 0
