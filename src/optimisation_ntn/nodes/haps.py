from optimisation_ntn.networks.antenna import Antenna
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.earth import Earth
from optimisation_ntn.utils.position import Position

from ..utils.position import Position
from .base_node import BaseNode


class HAPS(BaseNode):
    haps_altitude = 20e3
    sky_visibility_angle = 10
    haps_orbit_radius = Earth.radius + haps_altitude

    def __init__(
        self, node_id: int, initial_position: Position = Position(0, haps_altitude)
    ):
        super().__init__(node_id, initial_position)
        self.add_antenna("UHF", 2.0)
        self.add_antenna("VHF", 1.0)
        self.state = False
        self.battery_capacity = 1000

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"HAPS {self.node_id}"
