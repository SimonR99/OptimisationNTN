"""Random power strategy"""

import random
from typing import Dict, List, Set, Tuple

from ...nodes.base_node import BaseNode
from .power_strategy import PowerStrategy


class RandomPowerStrategy(PowerStrategy):
    """Randomly activates nodes based on epsilon parameter"""

    def __init__(
        self,
        epsilon: float = 0.5,
        with_change: bool = True,
        change_interval: float = 5.0,
    ):
        """Initialize random power strategy.

        Args:
            epsilon: Fraction of nodes to keep active (default: 0.5)
            with_change: Whether to change active nodes periodically (default: True)
            change_interval: Time interval between changes in seconds (default: 5.0)
        """
        if not 0 <= epsilon <= 1:
            raise ValueError("Epsilon must be between 0 and 1")

        self.epsilon = epsilon
        self.with_change = with_change
        self.change_interval = change_interval
        self.active_nodes: Set[Tuple[str, int]] = set()  # (node_type, node_id)
        self.last_change_time = -float("inf")
        self.accumulated_time = 0.0

    def _get_node_key(self, node: BaseNode) -> Tuple[str, int]:
        """Get unique key for a node."""
        return (type(node).__name__, node.node_id)

    def _select_active_nodes(self, nodes: List[BaseNode]) -> None:
        """Randomly select nodes to activate based on epsilon."""
        if not nodes:
            return

        num_active = max(1, int(len(nodes) * self.epsilon))
        active_indices = random.sample(range(len(nodes)), num_active)
        self.active_nodes = {self._get_node_key(nodes[i]) for i in active_indices}

    def apply_strategy(self, nodes: List[BaseNode], time: float) -> None:
        """Apply random power strategy to nodes.

        Args:
            nodes: List of nodes to manage power for
            time: Current simulation time step
        """
        # Accumulate time
        self.accumulated_time += time

        # Check if we need to update active nodes
        time_since_last_change = self.accumulated_time - self.last_change_time

        if not self.active_nodes or (
            self.with_change and time_since_last_change >= self.change_interval
        ):
            self._select_active_nodes(nodes)
            self.last_change_time = self.accumulated_time

        # Apply power state based on active nodes set
        for node in nodes:
            if self._get_node_key(node) in self.active_nodes:
                node._turn_on()
            else:
                node._turn_off()
