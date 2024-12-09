from optimisation_ntn.utils.position import Position
from .base_node import BaseNode
from typing import Literal


class BaseStation(BaseNode):
    def __init__(
        self,
        node_id: int,
        initial_position: Position,
        debug: bool = False,
        power_strategy: Literal["AllOn", "OnDemand", "OnDemandWithTimeout"] = "AllOn",
    ):
        super().__init__(
            node_id, initial_position, debug=debug, power_strategy=power_strategy
        )
        self.state = True
        self.processing_frequency = 3e9  # 3 GHz
        self.k_const = 10e-28
        self.add_antenna("VHF", 10)
        self.name = "BS"

    def __str__(self):
        return f"Base Station {self.node_id}"
