from abc import ABC, abstractmethod
from typing import List

from ...networks.request import Request
from ...nodes.base_node import BaseNode


class AssignmentStrategy(ABC):
    """Base class for request assignment strategies"""

    @abstractmethod
    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        """Select a compute node for the request.

        Args:
            request: The request to be assigned
            nodes: List of available compute nodes

        Returns:
            tuple[BaseNode, List[BaseNode], float]: Selected node, path to node, and total delay
        """
        pass

    def get_name(self) -> str:
        """Get strategy name for display/logging"""
        return self.__class__.__name__
