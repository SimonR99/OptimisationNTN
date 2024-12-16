"""On demand with timeout power strategy"""

from typing import List

from ...nodes.base_node import BaseNode
from .power_strategy import PowerStrategy


class OnDemandWithTimeoutPowerStrategy(PowerStrategy):
    """Powers nodes on when needed and keeps them on for a timeout period"""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.last_active = {}  # type: dict[int, float]

    def apply_strategy(self, nodes: List[BaseNode], time: float) -> None:
        for node in nodes:
            if node.processing_queue:
                self.last_active[node.node_id] = time
                node._turn_on()
            elif node.node_id in self.last_active:
                if time - self.last_active[node.node_id] > self.timeout:
                    node._turn_off()
                    del self.last_active[node.node_id] 