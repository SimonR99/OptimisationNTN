from optimisation_ntn.networks.antenna import Antenna
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.earth import Earth
from optimisation_ntn.utils.position import Position
from ..networks.request import Request

from ..utils.position import Position
from .base_node import BaseNode


class HAPS(BaseNode):
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
        self.add_antenna("UHF", 2.0)
        self.add_antenna("VHF", 2.0)
        self.state = True
        self.battery_capacity = 10000
        self.processing_power = 40.0
        self.processing_frequency = 2.5e9
        self.k_const = 10e-25
        self.transmission_power = 10
        self.name = "HAPS"
        """Ce peak d'énergie est une constante déterminée sans sources scientifiques."""
        self.turn_on_energy_peak = 2.5e-26
        self.turn_on_standby_energy = 1e-26

    def __str__(self):
        return f"HAPS {self.node_id}"