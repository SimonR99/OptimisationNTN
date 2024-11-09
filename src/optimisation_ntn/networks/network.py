import math
import random
from typing import List

from optimisation_ntn.networks.request import Request, RequestStatus
from optimisation_ntn.nodes.base_node import BaseNode

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

    def get_compute_nodes(self) -> List[BaseNode]:
        """Get all nodes with processing capability"""
        return [
            node
            for node in self.nodes
            if not isinstance(node, UserDevice) and node.processing_power > 0
        ]

    def route_request(self, request: Request) -> bool:
        """Route request to target compute node through available paths."""
        source = request.current_node
        target = request.target_node
        
        # Find all possible paths to target
        paths = self._find_paths(source, target)
        if not paths:
            print(f"WARNING: No path found for request {request.id} from {source} to {target}")
            return False
            
        # Use shortest path
        path = min(paths, key=len)
        print(f"Found path for request {request.id}: {' -> '.join(str(node) for node in path)}")
        
        # Store the complete path in the request
        request.path = path
        request.path_index = 0
        
        # Start routing through first link
        return self._route_to_next_node(request)

    def _route_to_next_node(self, request: Request) -> bool:
        """Route request to its next node in the path."""
        if not hasattr(request, 'path') or not request.path:
            print(f"WARNING: Request {request.id} has no path")
            return False
            
        if request.path_index >= len(request.path) - 1:
            print(f"Request {request.id} has reached its target")
            return True
            
        current_node = request.path[request.path_index]
        next_node = request.path[request.path_index + 1]
        
        # Find link between current and next node
        link = next((l for l in self.communication_links 
                    if l.node_a == current_node and l.node_b == next_node), None)
        
        if link:
            link.add_to_queue(request)
            request.status = RequestStatus.IN_TRANSIT
            request.next_node = next_node
            print(f"Added request {request.id} to transmission queue: {current_node} -> {next_node}")
            return True
        else:
            print(f"WARNING: No link found between {current_node} and {next_node}")
            return False

    def _find_paths(self, start: BaseNode, end: BaseNode, path=None, visited=None) -> list[list[BaseNode]]:
        """Find all possible paths between start and end nodes"""
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
        for link in self.communication_links:
            if link.node_a == start and link.node_b not in visited:
                neighbors.add(link.node_b)
            elif link.node_b == start and link.node_a not in visited:
                neighbors.add(link.node_a)
                
        for neighbor in neighbors:
            if neighbor not in visited:
                new_paths = self._find_paths(neighbor, end, path, visited)
                paths.extend(new_paths)
                
        visited.remove(start)
        return paths

    def tick(self, time: float = 0.1):
        """Update network state including request routing"""
        # First process all nodes
        for node in self.nodes:
            node.tick(time)

        # Then update all communication links
        for link in self.communication_links:
            if link.transmission_queue:
                print(f"Link {link.node_a} -> {link.node_b} has {len(link.transmission_queue)} requests in queue")
            link.tick(time)

        # Check for stuck requests and try to route them
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
                            print(f"Request {request.id} not in any queue, attempting to route to next node")
                            request.path_index += 1  # Move to next node in path
                            self._route_to_next_node(request)
