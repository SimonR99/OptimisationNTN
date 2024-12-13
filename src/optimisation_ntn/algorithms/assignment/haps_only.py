""" HAPS only assignment strategy """

from typing import List

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from ...nodes.haps import HAPS
from .assignment_strategy import AssignmentStrategy


class HAPSOnlyAssignment(AssignmentStrategy):
    """Assigns requests only to HAPS nodes"""

    def __init__(self, network):
        self.network = network

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        # Filter only HAPS nodes
        haps_nodes = [node for node in nodes if isinstance(node, HAPS)]

        if not haps_nodes:
            return None, None, float("inf")

        # Find closest HAPS
        best_node = None
        best_distance = float("inf")
        best_path = None

        for haps in haps_nodes:
            distance = request.current_node.position.distance_to(haps.position)
            if distance < best_distance:
                best_distance = distance
                best_node = haps
                best_path = self.network.generate_request_path(
                    request.current_node, haps
                )

        total_delay = self.network.get_network_delay(request, best_path)

        return best_node, best_path, total_delay
