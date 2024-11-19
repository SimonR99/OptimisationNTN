from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.position import Position

from ..networks.antenna import Antenna
from .base_node import BaseNode


class BaseStation(BaseNode):
    def __init__(self, node_id: int, initial_position: Position, debug: bool = False):
        super().__init__(node_id, initial_position, debug=debug)
        self.state = True
        self.processing_power = 50.0
        self.add_antenna("VHF", 1.5)

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"Base Station {self.node_id}"
