import math
import random

from ..nodes.base_station import BaseStation
from ..nodes.haps import HAPS
from ..nodes.leo import LEO
from ..nodes.user_device import UserDevice
from .communication_link import CommunicationLink


class Network:
    def __init__(self):
        self.nodes = []
        self.communication_links = []

    def __str__(self) -> str:
        """String representation of the network showing node counts."""
        return (
            f"Network Configuration:\n"
            f"  HAPS: {self.count_haps()}\n"
            f"  Users: {self.count_users()}\n"
            f"  Total nodes: {len(self.nodes)}\n"
            f"  Communication links: {len(self.communication_links)}"
        )

    def count_base_stations(self) -> int:
        """Count number of base stations in network."""
        return len([n for n in self.nodes if isinstance(n, BaseStation)])

    def count_haps(self) -> int:
        """Count number of HAPS in network."""
        return len([n for n in self.nodes if isinstance(n, HAPS)])

    def count_leos(self) -> int:
        """Count number of LEO satellites in network."""
        return len([n for n in self.nodes if isinstance(n, LEO)])

    def count_users(self) -> int:
        """Count number of user devices in network."""
        return len([n for n in self.nodes if isinstance(n, UserDevice)])

    def add_node(self, node):
        self.nodes.append(node)
        self._update_communication_links()

    def _update_communication_links(self):
        """Update all communication links in the network"""
        self.communication_links.clear()
        # Get nodes by type
        haps_nodes = [node for node in self.nodes if isinstance(node, HAPS)]
        user_nodes = [node for node in self.nodes if isinstance(node, UserDevice)]
        base_stations = [node for node in self.nodes if isinstance(node, BaseStation)]
        # Connect each user to all HAPS and closest base station
        for user in user_nodes:
            # Connect to all HAPS
            for haps in haps_nodes:
                link = CommunicationLink(
                    user, haps, total_bandwidth=1, signal_power=1, carrier_frequency=1
                )
                self.communication_links.append(link)

            # Connect to closest base station
            if base_stations:
                closest_bs = None
                min_distance = float("inf")

                for bs in base_stations:
                    dx = user.position.x - bs.position.x
                    dy = user.position.y - bs.position.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < min_distance:
                        min_distance = distance
                        closest_bs = bs

                if closest_bs:
                    link = CommunicationLink(
                        user,
                        closest_bs,
                        total_bandwidth=1,
                        signal_power=1,
                        carrier_frequency=1,
                    )
                    self.communication_links.append(link)

        # Connect each base station to all HAPS
        for bs in base_stations:
            for haps in haps_nodes:
                link = CommunicationLink(
                    bs,
                    haps,
                    total_bandwidth=2,  # Higher bandwidth for BS-HAPS links
                    signal_power=2,  # Higher power for BS-HAPS links
                    carrier_frequency=1,
                )
                self.communication_links.append(link)

    def tick(self, time: float = 0.1):
        """Update network state"""
        for node in self.nodes:
            node.tick(time)
        for link in self.communication_links:
            link.tick(time)
