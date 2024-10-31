import numpy as np

from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.utils.earth import Earth

from ..utils.type import Position
from .base_node import BaseNode


class LEO(BaseNode):

    leo_altitude = 500e3
    leo_temperature = 200

    earth_mass = 5.972e24
    earth_radius = 6.371e6
    gravitational_constant = 6.67430e-11

    bolztmann_constant = 1.38064852e-23

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

    def __init__(self, node_id, start_angle=initial_angle):
        global_position = Earth.calculate_position_from_angle(
            start_angle, self.leo_orbit_radius
        )
        super().__init__(node_id, Earth.global_coordinate_to_local(global_position))
        self.state = False
        self.battery_capacity = 100
        self.current_angle = start_angle

    @property
    def speed(self):
        """return the speed of the LEO satellite in m/s"""
        return (
            self.gravitational_constant
            * self.earth_mass
            / (self.earth_radius + self.leo_altitude)
        ) ** 0.5

    @property
    def angular_speed(self):
        """return the angular speed of the LEO satellite in rad/s"""
        return self.speed / self.leo_orbit_radius * 360 / (2 * np.pi)

    @property
    def spectral_noise_density(self):
        return self.bolztmann_constant * self.leo_temperature

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"LEO {self.node_id}"

    def tick(self, time):
        # Update the position of the LEO satellite
        delta_angle = self.angular_speed * time
        self.current_angle += delta_angle

        global_position = Earth.calculate_position_from_angle(
            self.current_angle, self.leo_orbit_radius
        )
        self.position = Earth.global_coordinate_to_local(global_position)
