""" Matrix based assignment strategy """

from typing import List, Optional

import numpy as np

from optimisation_ntn.networks.network import Network
from optimisation_ntn.networks.request import Request
from optimisation_ntn.nodes.base_node import BaseNode

from .assignment_strategy import AssignmentStrategy


class MatrixBasedAssignment(AssignmentStrategy):
    """Assigns requests based on a pre-defined assignment matrix"""

    def __init__(self, network: Network):
        self.network = network
        self.assignment_matrix: Optional[np.ndarray] = None
        self.current_request_index = 0

    def set_assignment_matrix(self, matrix: np.ndarray):
        """Set the assignment matrix to use for request routing"""
        self.assignment_matrix = matrix
        self.current_request_index = 0

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[Optional[BaseNode], Optional[List[BaseNode]], float]:
        if self.assignment_matrix is None:
            raise ValueError("Assignment matrix not set")

        # Get the assigned node index from the matrix
        if self.current_request_index >= len(self.assignment_matrix):
            return None, None, float("inf")

        assigned_node_idx = self.assignment_matrix[self.current_request_index]
        self.current_request_index += 1

        # Find the corresponding node
        compute_nodes = self.network.compute_nodes
        if assigned_node_idx >= len(compute_nodes):
            return None, None, float("inf")

        selected_node = compute_nodes[assigned_node_idx]

        # Generate path and calculate delay
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        return selected_node, path, total_delay
