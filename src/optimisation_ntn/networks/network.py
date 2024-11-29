import math
from typing import List

from optimisation_ntn.networks.request import Request, RequestStatus
from optimisation_ntn.nodes.base_node import BaseNode

from ..nodes.base_station import BaseStation
from ..nodes.haps import HAPS
from ..nodes.leo import LEO
from ..nodes.user_device import UserDevice
from .communication_link import CommunicationLink


class Network:
    def __init__(self, debug: bool = False):
        self.nodes: List[BaseNode] = []
        self.communication_links: List[CommunicationLink] = []
        self.debug = debug

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

    def __str__(self) -> str:
        """String representation of the network showing node counts."""
        return (
            f"Network Configuration:\n"
            f"  Base Stations: {self.count_nodes_by_type(BaseStation)}\n"
            f"  HAPS: {self.count_nodes_by_type(HAPS)}\n"
            f"  LEO: {self.count_nodes_by_type(LEO)}\n"
            f"  Users: {self.count_nodes_by_type(UserDevice)}\n"
            f"  Total nodes: {len(self.nodes)}\n"
            f"  Communication links: {len(self.communication_links)}"
        )

    def count_nodes_by_type(self, node_type: type) -> int:
        """Count nodes of a specific type in network."""
        try:
            return len([n for n in self.nodes if isinstance(n, node_type)])
        except Exception:
            return 0

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
        leo_nodes = [node for node in self.nodes if isinstance(node, LEO)]

        self.debug_print("\nCreating communication links:")

        # Connect each user to all HAPS and closest base station (bidirectional)
        for user in user_nodes:
            # Connect to all HAPS (both directions)
            for haps in haps_nodes:
                # User -> HAPS
                link = CommunicationLink(
                    user,
                    haps,
                    total_bandwidth=1,
                    signal_power=1,
                    carrier_frequency=1,
                    debug=self.debug,
                )
                self.communication_links.append(link)
                self.debug_print(f"Created link: {user} -> {haps}")

            # Connect to closest base station (both directions)
            if base_stations:
                closest_bs = None
                min_distance = float("inf")

                for bs in base_stations:
                    distance = user.position.distance_to(bs.position)
                    self.debug_print(f"{bs}: {distance:.2f} m")

                    if distance < min_distance:
                        min_distance = distance
                        closest_bs = bs

                if closest_bs:
                    # User -> BS
                    link = CommunicationLink(
                        user,
                        closest_bs,
                        total_bandwidth=1,
                        signal_power=1,
                        carrier_frequency=1,
                        debug=self.debug,
                    )
                    self.communication_links.append(link)
                    self.debug_print(
                        f"Created link: {user} -> {closest_bs} (closest, distance: {min_distance:.2f})"
                    )

        # Connect each base station to all HAPS (bidirectional)
        for bs in base_stations:
            for haps in haps_nodes:
                # BS -> HAPS
                link = CommunicationLink(
                    bs,
                    haps,
                    total_bandwidth=2,  # Higher bandwidth for BS-HAPS links
                    signal_power=2,  # Higher power for BS-HAPS links
                    carrier_frequency=1,
                    debug=self.debug,
                )
                self.communication_links.append(link)
                self.debug_print(f"Created link: {bs} -> {haps}")
                # HAPS -> BS
                link = CommunicationLink(
                    haps,
                    bs,
                    total_bandwidth=2,
                    signal_power=2,
                    carrier_frequency=1,
                    debug=self.debug,
                )
                self.communication_links.append(link)
                self.debug_print(f"Created link: {haps} -> {bs}")

        # Add new section: Connect each LEO to all HAPS (bidirectional)
        for leo in leo_nodes:
            for haps in haps_nodes:
                # HAPS -> LEO
                link = CommunicationLink(
                    haps,
                    leo,
                    total_bandwidth=2,
                    signal_power=2,
                    carrier_frequency=1,
                    debug=self.debug,
                )
                self.communication_links.append(link)
                self.debug_print(f"Created link: {haps} -> {leo}")

    def get_compute_nodes(
        self, request: Request | None = None, check_state: bool = True
    ) -> List[BaseNode]:
        """Get all nodes with processing capability"""
        return [node for node in self.nodes if node.can_process(request, check_state)]

    def compute_path_time(self, path: List[BaseNode], request: Request) -> float:
        """Calculate the total compute time for a path"""
        return sum(node.processing_time(request) for node in path)

    def generate_request_path(
        self, source: BaseNode, target: BaseNode
    ) -> List[BaseNode]:
        """Generate a path for a request between source and target nodes"""
        closest_haps = None
        min_distance = float("inf")
        for haps in [n for n in self.nodes if isinstance(n, HAPS)]:
            distance = source.position.distance_to(haps.position)
            if distance < min_distance:
                min_distance = distance
                closest_haps = haps

        if target in source.destinations:
            return [source, target]
        elif closest_haps:
            return [source, closest_haps, target]

        raise ValueError(f"No path found for request from {source} to {target}")

    def get_network_delay(self, request: Request, path: List[BaseNode]) -> float:
        """Get the total network delay for a request"""
        time = 0.0
        for i in range(len(path) - 1):
            for link in self.communication_links:
                if link.node_a == path[i] and link.node_b == path[i + 1]:
                    time += link.estimate_network_delay(request)
        return time

    def tick(self, time: float = 0.1):
        """Update network state including request routing"""
        # Update all compute nodes
        for node in self.nodes:
            node.tick(time)

        # Update all communication links and handle completed transmissions
        for link in self.communication_links:
            if link.transmission_queue:
                self.debug_print(
                    f"Link {link.node_a} -> {link.node_b} has {len(link.transmission_queue)} requests in queue"
                )
                self.debug_print(
                    f"Link {link.node_a} -> {link.node_b}: Transmitting request {link.transmission_queue[0].id} ({link.request_progress:.1f}/{link.transmission_queue[0].size} bits)"
                )

            link.tick(time)

            # Handle completed transmissions
            for request in link.completed_requests:
                current_node = request.path[request.path_index]
                request.path_index += 1

                # If request has reached its final destination
                if request.path_index >= len(request.path):
                    if current_node == request.target_node:
                        self.debug_print(
                            f"Request {request.id} reached target node {current_node}, adding to processing queue"
                        )
                        current_node.add_request_to_process(request)
                else:
                    # Route to next node
                    next_node = request.path[request.path_index]
                    self.debug_print(
                        f"Request {request.id} completed transmission to {current_node}, routing to {next_node}"
                    )

                    # Find next link and add request to its queue
                    for next_link in self.communication_links:
                        if (
                            next_link.node_a == current_node
                            and next_link.node_b == next_node
                        ):
                            next_link.add_to_queue(request)
                            request.next_node = next_node
                            break
