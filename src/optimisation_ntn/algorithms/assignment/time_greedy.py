from typing import List

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class TimeGreedyAssignment(AssignmentStrategy):
    """Assigns requests to nodes that can process them fastest"""

    def __init__(self, network):
        self.network = network

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        best_node = None
        best_total_time = float("inf")
        best_path = None

        for compute_node in nodes:
            # Estimate processing time
            processing_time = compute_node.estimated_processing_time(request)

            # Get path and network delay
            path = self.network.generate_request_path(
                request.current_node, compute_node
            )
            network_delay = self.network.get_network_delay(request, path)

            # Calculate total time
            total_time = processing_time + network_delay

            if total_time < best_total_time:
                best_total_time = total_time
                best_node = compute_node
                best_path = path

        return best_node, best_path, best_total_time
