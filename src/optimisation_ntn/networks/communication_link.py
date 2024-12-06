from typing import List

import numpy as np

from ..nodes.base_node import BaseNode
from ..nodes.base_station import BaseStation
from ..nodes.haps import HAPS
from ..nodes.user_device import UserDevice
from ..utils.earth import Earth
from .request import Request


class CommunicationLink:
    def __init__(
        self,
        node_a: BaseNode,
        node_b: BaseNode,
        signal_power: float,
        carrier_frequency: float,
        total_bandwidth: float,
        debug: bool = False,
    ):
        self.node_a = node_a
        self.node_b = node_b
        self.signal_power = signal_power
        self.carrier_frequency = carrier_frequency
        self.total_bandwidth = total_bandwidth
        self.transmission_queue: List[Request] = []  # FIFO queue
        self.request_progress = 0.0
        self.debug = debug
        self.completed_requests = []

        # Identify compatible antennas for communication
        self.antenna_a, self.antenna_b = self.find_compatible_antennas()
        self.node_a.add_destination(self.node_b)

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
        # Assumes node_b is the receiver
        spectral_noise_density = self.linear_scale_dbm(
            self.node_b.spectral_noise_density
        )

        return spectral_noise_density * self.adjusted_bandwidth

    def linear_scale_db(self, gain: float) -> float:
        """Linear scale the Gain in dB to apply in SNR."""
        return 10 ** (gain / 10)

    def linear_scale_dbm(self, power: float) -> float:
        """Linear scale the dBm to apply in SNR."""
        return 10 ** ((power - 30) / 10)

    def calculate_free_space_path_loss(self) -> float:
        """Calculates Free Space Path Loss for (user-haps, haps-base station, haps-leo)."""
        return Earth.speed_of_light / (
            4 * np.pi * self.link_length * self.carrier_frequency
        )

    def calculate_gain(self) -> float:
        """Calculates Gain of the channel user - base station."""
        if isinstance(self.node_a, UserDevice) and isinstance(self.node_b, BaseStation):
            """Linear Scale the path loss link of 40 dB. 40 dB selon études"""
            path_loss = self.linear_scale_db(40)

            return (
                path_loss
                * (np.abs(self.node_a.attenuation_coefficient) ** 2)
                / self.link_length**self.node_a.path_loss_exponent
            )
            """Calculates Gain of the current channel that is different from user - bs."""
        else:
            path_loss = self.calculate_free_space_path_loss()
            tx_antenna = self.linear_scale_db(self.antenna_a.gain)
            rx_antenna = self.linear_scale_db(self.antenna_b.gain)

            return tx_antenna * rx_antenna * path_loss

    def calculate_snr(self) -> float:
        """Calculates SNR (Signal to Noise Ratio) of the current channel."""
        gain = self.calculate_gain()
        power = self.linear_scale_dbm(self.signal_power)

        return power * gain / self.noise_power

    def calculate_capacity(self) -> float:
        """Calculates link capacity based on Shannon's formula using adjusted bandwidth."""
        snr = self.calculate_snr()
        return self.adjusted_bandwidth * np.log2(1 + snr)

    def calculate_transmission_delay(self, request: Request) -> float:
        """Estimates the network delay for the link."""
        return request.size / self.calculate_capacity()

    def add_to_queue(self, request: Request):
        """Adds a request to the transmission queue and resets progress tracking."""
        self.transmission_queue.append(request)
        self.request_progress = 0  # Initialize progress for the new request

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

    def tick(self, time: float):
        """Processes requests in the queue."""
        self.completed_requests.clear()  # Clear previous completed requests

        if self.transmission_queue:
            current_request = self.transmission_queue[0]
            capacity = self.calculate_capacity()
            transmission_delay = self.calculate_transmission_delay(current_request)
            bits_transmitted = capacity * time
            if isinstance(
                self.node_a, HAPS
            ):  # Only HAPS->LEO transmission energy need to be taken into account
                self.node_a.energy_consumed += self.node_a.transmission_energy() * time

            if self.debug:
                print(f"Capacity: {capacity} \n")
                print(f"Request size: {current_request.size} \n")
                print(f"Transmission time: {transmission_delay} \n")
            self.request_progress += bits_transmitted

            self.debug_print(
                f"Link {self.node_a} -> {self.node_b}: Transmitting request {current_request.id} "
                f"({self.request_progress:.1f}/{current_request.size} bits)"
            )

            # Only complete transmission at the end of a tick if enough bits were transmitted
            if self.request_progress >= current_request.size:
                self.debug_print(
                    f"Request {current_request.id} completed transmission from {self.node_a} to {self.node_b}"
                )
                self.completed_requests.append(current_request)
                self.transmission_queue.pop(0)
                self.request_progress = 0.0
