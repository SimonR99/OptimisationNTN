"""Power strategy base class"""

from abc import ABC, abstractmethod
from typing import List

from ...nodes.base_node import BaseNode


class PowerStrategy(ABC):
    """Base class for power management strategies"""

    @abstractmethod
    def apply_strategy(self, nodes: List[BaseNode], time: float) -> None:
        """Apply power strategy to nodes.

        Args:
            nodes: List of nodes to manage power for
            time: Current simulation time
        """

    def get_name(self) -> str:
        """Get strategy name for display/logging"""
        return self.__class__.__name__
