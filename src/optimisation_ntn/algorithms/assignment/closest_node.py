""" Closest node assignment strategy """

from typing import List

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class ClosestNodeAssignment(AssignmentStrategy):
    """Assigns requests to the physically closest available node"""

    def __init__(self, network):
        self.network = network

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        best_node = None
        best_distance = float("inf")
        best_path = None

        for compute_node in nodes:
            distance = request.current_node.position.distance_to(compute_node.position)

            if distance < best_distance:
                best_distance = distance
                best_node = compute_node
                best_path = self.network.generate_request_path(
                    request.current_node, compute_node
                )

        # Calculate total delay for the chosen path
        total_delay = (
            self.network.get_network_delay(request, best_path)
            if best_path
            else float("inf")
        )

        return best_node, best_path, total_delay
