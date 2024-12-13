""" Energy greedy assignment strategy """

from typing import List

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class EnergyGreedyAssignment(AssignmentStrategy):
    """Assigns requests to nodes with lowest energy consumption"""

    def __init__(self, network):
        self.network = network

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        best_node = None
        best_energy = float("inf")
        best_path = None

        for compute_node in nodes:
            # Calculate energy cost for processing
            processing_energy = (
                compute_node.processing_energy()
                * compute_node.estimated_processing_time(request)
            )

            # Get path and transmission energy
            path = self.network.generate_request_path(
                request.current_node, compute_node
            )
            transmission_energy = sum(node.transmission_energy() for node in path[:-1])

            total_energy = processing_energy + transmission_energy

            if total_energy < best_energy:
                best_energy = total_energy
                best_node = compute_node
                best_path = path

        return best_node, best_path, best_energy
