import numpy as np

from optimisation_ntn.utils.type import Position

from .base_node import BaseNode


class LEO(BaseNode):

    leo_altitude = 500e3
    leo_temperature = 200

    earth_mass = 5.972e24
    earth_radius = 6.371e6
    gravitational_constant = 6.67430e-11

    bolztmann_constant = 1.38064852e-23

    intial_angle = -(
        180
        - 100
        - np.rad2deg(
            np.arcsin(
                (earth_radius + 20e3)
                * np.sin(np.deg2rad(100))
                / (earth_radius + leo_altitude)
            )
        )
    )

    final_angle = -intial_angle

    def __init__(self, node_id, position):
        super().__init__(node_id, position)
        self.state = "off"
        self.battery_capacity = 100

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
        return self.speed / (self.earth_radius + self.leo_altitude)

    @property
    def spectral_noise_density(self):
        return self.bolztmann_constant * self.leo_temperature

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"LEO {self.node_id}"

    def tick(self, time):
        pass
