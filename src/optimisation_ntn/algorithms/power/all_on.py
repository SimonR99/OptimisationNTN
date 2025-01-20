"""All on power strategy"""

from typing import List

from ...nodes.base_node import BaseNode
from .power_strategy import PowerStrategy


class AllOnPowerStrategy(PowerStrategy):
    """Keeps all nodes powered on"""

    def apply_strategy(self, nodes: List[BaseNode], time: float) -> None:
        for node in nodes:
            node._turn_on()
