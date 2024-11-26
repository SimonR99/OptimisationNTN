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
                # HAPS -> User
                link = CommunicationLink(
                    haps,
                    user,
                    total_bandwidth=1,
                    signal_power=1,
                    carrier_frequency=1,
                    debug=self.debug,
                )
                self.communication_links.append(link)
                self.debug_print(f"Created link: {haps} -> {user}")

            # Connect to closest base station (both directions)
            if base_stations:
                # Print distances to all base stations for debugging
                self.debug_print(f"\nDistances from {user} to base stations:")
                for bs in base_stations:
                    distance = user.position.distance_to(bs.position)
                    self.debug_print(f"{bs}: {distance:.2f} units")

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
                    # BS -> User
                    link = CommunicationLink(
                        closest_bs,
                        user,
                        total_bandwidth=1,
                        signal_power=1,
                        carrier_frequency=1,
                        debug=self.debug,
                    )
                    self.communication_links.append(link)
                    self.debug_print(f"Created link: {closest_bs} -> {user}")

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

    def get_compute_nodes(self) -> List[BaseNode]:
        """Get all nodes with processing capability"""
        return [node for node in self.nodes if node.frequency > 0]

    def route_request(self, request: Request) -> bool:
        """
        Route request to target compute node through available paths.

        Args:
            request (Request): The request to be routed

        Returns:
            is_routed (bool): True if request was successfully routed
        """
        source = request.current_node
        target = request.target_node

        # Find all possible paths to target
        paths = self._find_paths_depth_first_search(source, target)
        if not paths:
            print(
                f"WARNING: No path found for request {request.id} from {source} to {target}"
            )
            return False

        # Calculate path costs
        path_costs = []
        self.debug_print("Path costs:")
        for path in paths:
            cost = 0.0
            for i in range(len(path) - 1):
                # Add distance cost
                distance = path[i].position.distance_to(path[i + 1].position)
                cost += distance
            path_costs.append(cost)
            self.debug_print(
                f"Path: {' -> '.join(str(node) for node in path)}, Cost: {cost:.2f}"
            )

        # Use path with minimum cost
        min_cost_index = path_costs.index(min(path_costs))
        path = paths[min_cost_index]
        self.debug_print(
            f"Selected path for request {request.id}: {' -> '.join(str(node) for node in path)}"
        )

        # Store the complete path in the request
        request.path = path
        request.path_index = 0

        # Start routing through first link
        return self._route_to_next_node(request)

    def _route_to_next_node(self, request: Request) -> bool:
        """Route request to its next node in the path."""
        if not hasattr(request, "path") or not request.path:
            print(f"WARNING: Request {request.id} has no path")
            return False

        if request.path_index >= len(request.path) - 1:
            self.debug_print(f"Request {request.id} has reached its target")
            return True

        current_node = request.path[request.path_index]
        next_node = request.path[request.path_index + 1]

        # Find link between current and next node
        for link in self.communication_links:  # For all available links
            # If the link connects the current node to the next node
            if link.node_a == current_node and link.node_b == next_node:
                link.add_to_queue(request)
                request.status = RequestStatus.IN_TRANSIT
                request.next_node = next_node
                self.debug_print(
                    f"Added request {request.id} to transmission queue: {current_node} -> {next_node}"
                )
                return True
        return False

    def _find_paths_depth_first_search(
        self, start: BaseNode, end: BaseNode, path=None, visited=None
    ) -> list[list[BaseNode]]:
        """Find all possible paths between start and end nodes using depth-first search."""
        if path is None:
            path = []
        if visited is None:
            visited = set()

        path = path + [start]
        visited.add(start)

        paths = []
        if start == end:
            return [path]

        # Find all connected nodes through communication links
        neighbors = set()
        self.debug_print(f"\nFinding neighbors for {start}:")  # Debug print

        # Only check node_a since we have bidirectional links
        for link in self.communication_links:
            if link.node_a == start and link.node_b not in visited:
                neighbors.add(link.node_b)
                self.debug_print(f"Found link to: {link.node_b}")

        # Try all possible paths through neighbors
        for neighbor in neighbors:
            if neighbor not in visited:
                # Create a new visited set for each neighbor to allow multiple paths
                new_visited = visited.copy()
                new_paths = self._find_paths_depth_first_search(
                    neighbor, end, path, new_visited
                )
                if new_paths:
                    paths.extend(new_paths)

        # Remove current node from visited before backtracking
        visited.remove(start)
        return paths

    def tick(self, time: float = 0.1):
        """Update network state including request routing"""
        # First process all nodes
        for node in self.nodes:
            # consume basic standby energy
            node.consume_standby_energy()
            node.tick(time)

        # Then update all communication links
        for link in self.communication_links:
            if link.transmission_queue:
                self.debug_print(
                    f"Link {link.node_a} -> {link.node_b} has {len(link.transmission_queue)} requests in queue"
                )
                self.debug_print(
                    f"Link {link.node_a} -> {link.node_b}: Transmitting request {link.transmission_queue[0].id} ({link.request_progress:.1f}/{link.transmission_queue[0].size} bits)"
                )
            link.tick(time)

        # Check for requests that need routing
        for node in self.nodes:
            if isinstance(node, UserDevice):
                for request in node.current_requests:
                    if request.status == RequestStatus.IN_TRANSIT:
                        # Find if request is actually in any transmission queue
                        in_queue = False
                        for link in self.communication_links:
                            if request in link.transmission_queue:
                                in_queue = True
                                break

                        if not in_queue:
                            # Request has finished transmission to next node
                            current_node = request.path[request.path_index]
                            request.current_node = current_node

                            # Move to next node in path
                            request.path_index += 1

                            # If we've reached the end of the path, add to processing queue
                            if request.path_index >= len(request.path):
                                if current_node == request.target_node:
                                    self.debug_print(
                                        f"Request {request.id} reached final target node {current_node}, adding to processing queue"
                                    )
                                    current_node.add_request_to_process(request)
                                else:
                                    self.debug_print(
                                        f"WARNING: Path ended at {current_node} but target was {request.target_node}"
                                    )
                            else:
                                # Route to next node in path
                                next_node = request.path[request.path_index]
                                self.debug_print(
                                    f"Request {request.id} completed transmission to {current_node}, routing to next node {next_node}"
                                )

                                # Find the appropriate link
                                next_link = next(
                                    (
                                        l
                                        for l in self.communication_links
                                        if l.node_a == current_node
                                        and l.node_b == next_node
                                    ),
                                    None,
                                )

                                if next_link:
                                    # Add request to the next link's queue
                                    next_link.add_to_queue(request)
                                    request.status = RequestStatus.IN_TRANSIT
                                    request.next_node = next_node
                                    self.debug_print(
                                        f"Added request {request.id} to transmission queue: {current_node} -> {next_node}"
                                    )
                                else:
                                    self.debug_print(
                                        f"WARNING: Failed to find link between {current_node} and {next_node}"
                                    )

    def get_total_energy_consumed(self):
        total_energy_consumed = 0
        for node in self.nodes:
            total_energy_consumed += node.energy_consumed
        return total_energy_consumed