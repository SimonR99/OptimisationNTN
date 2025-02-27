""" HAPS node """

from optimisation_ntn.utils.earth import Earth

from ..utils.position import Position
from .base_node import BaseNode


class HAPS(BaseNode):
    """HAPS node"""

    haps_altitude = 20e3
    sky_visibility_angle = 10
    haps_orbit_radius = Earth.radius + haps_altitude

    def __init__(
        self,
        node_id: int,
        initial_position: Position = Position(0, haps_altitude),
        debug: bool = False,
    ):
        super().__init__(node_id, initial_position, debug=debug)
        self.add_antenna("UHF", 15.0)
        self.add_antenna("VHF", 15.0)
        self.battery_capacity = 2e4
        self.processing_frequency = 5e9
        self.k_const = 10e-28
        self.transmission_power = 33
        self.name = "HAPS"

    def __str__(self):
        return f"HAPS {self.node_id}"
