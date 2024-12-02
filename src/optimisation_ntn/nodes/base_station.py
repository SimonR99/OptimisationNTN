from optimisation_ntn.utils.position import Position
from .base_node import BaseNode


class BaseStation(BaseNode):
    def __init__(self, node_id: int, initial_position: Position, debug: bool = False):
        super().__init__(node_id, initial_position, debug=debug)
        self.state = True
        self.processing_power = 50.0
        self.processing_frequency = 1e9  # 1 GHz
        self.k_const = 10e-28
        self.add_antenna("VHF", 1.5)
        self.name = "BS"

    def __str__(self):
        return f"Base Station {self.node_id}"
