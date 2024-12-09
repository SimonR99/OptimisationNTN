import numpy as np

from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.utils.earth import Earth

from .base_node import BaseNode
from typing import Literal


class LEO(BaseNode):
    leo_altitude = 500e3
    leo_temperature = 200

    leo_orbit_radius = Earth.radius + leo_altitude
    haps_orbit_radius = Earth.radius + HAPS.haps_altitude

    final_angle = (
        180
        - 100
        - np.rad2deg(
            np.arcsin(
                haps_orbit_radius
                * np.sin(np.deg2rad(90 + HAPS.sky_visibility_angle))
                / (leo_orbit_radius)
            )
        )
    )

    initial_angle = -final_angle

    def __init__(
        self,
        node_id,
        start_angle=initial_angle,
        debug: bool = False,
        power_strategy: Literal["AllOn", "OnDemand", "OnDemandWithTimeout"] = "AllOn",
    ):
        global_position = Earth.calculate_position_from_angle(
            start_angle, self.leo_orbit_radius
        )
        super().__init__(
            node_id,
            Earth.global_coordinate_to_local(global_position),
            debug=debug,
            power_strategy=power_strategy,
        )
        self.add_antenna("UHF", 8)
        self.battery_capacity = 2e3  # J
        self.current_angle = start_angle
        self.processing_frequency = 10e9  # Hz
        self.k_const = 10e-28
        self.name = "LEO"

    @property
    def is_visible(self) -> bool:
        """Check if satellite is in visible range"""
        return self.initial_angle <= self.current_angle <= self.final_angle

    @property
    def speed(self):
        """return the speed of the LEO satellite in m/s"""
        return (
            Earth.gravitational_constant * Earth.mass / (self.leo_orbit_radius)
        ) ** 0.5

    @property
    def angular_speed(self):
        """return the angular speed of the LEO satellite in rad/s"""
        return self.speed / self.leo_orbit_radius * 360 / (2 * np.pi)

    def tick(self, time: float):
        super().tick(time)

        # Update the position of the LEO satellite
        delta_angle = self.angular_speed * time
        self.current_angle += delta_angle

        global_position = Earth.calculate_position_from_angle(
            self.current_angle, self.leo_orbit_radius
        )
        self.position = Earth.global_coordinate_to_local(global_position)

    def __str__(self):
        return f"LEO {self.node_id}"
