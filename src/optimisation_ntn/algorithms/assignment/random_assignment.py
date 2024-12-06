from typing import List
import random

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class RandomAssignment(AssignmentStrategy):
    """Randomly assigns requests to available compute nodes"""

    def __init__(self, network):
        self.network = network

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        if not nodes:
            return None, None, float("inf")

        # Randomly select a node
        selected_node = random.choice(nodes)
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        return selected_node, path, total_delay
