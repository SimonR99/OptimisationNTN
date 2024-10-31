from optimisation_ntn.antenna import Antenna
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.earth import Earth
from optimisation_ntn.utils.type import Position

from .base_node import BaseNode


class HAPS(BaseNode):

    haps_altitude = 20e3
    sky_visibility_angle = 10

    def __init__(
        self, node_id: int, initial_position: Position = Position(0, haps_altitude)
    ):
        super().__init__(node_id, initial_position)
        self.add_antenna("UHF", 2.0)  # Example type and gain
        self.add_antenna("VHF", 1.0)  # Another type and gain example

        self.state = "off"
        self.battery_capacity = 1000

        haps_leo_antenna = Antenna([type], 10)
        user_device_haps_antenna = Antenna([UserDevice], 10)

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"HAPS {self.node_id}"
