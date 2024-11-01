from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.type import Position

from ..network.antenna import Antenna
from .base_node import BaseNode


class BaseStation(BaseNode):
    def __init__(self, node_id: int, initial_position: Position):
        super().__init__(node_id, initial_position)

        user_base_station_antenna = Antenna([UserDevice], 10)

        self.antennas = [user_base_station_antenna]
        self.state = "off"

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"Base Station {self.node_id}"
