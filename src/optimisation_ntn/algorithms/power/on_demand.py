"""On demand power strategy"""

from typing import List

from ...nodes.base_node import BaseNode
from .power_strategy import PowerStrategy


class OnDemandPowerStrategy(PowerStrategy):
    """Powers nodes on only when they have requests to process"""

    def apply_strategy(self, nodes: List[BaseNode], time: float) -> None:
        for node in nodes:
            if node.processing_queue:
                node._turn_on()
            else:
                node._turn_off() 