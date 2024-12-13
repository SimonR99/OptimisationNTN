""" Earth model """

import numpy as np

from optimisation_ntn.utils.position import Position


class Earth:
    """Earth model"""

    radius = 6.371e6  # m
    mass = 5.972e24  # kg
    gravitational_constant = 6.67430e-11  # m^3 kg^-1 s^-2

    bolztmann_constant = 1.38064852e-23  # J/K
    speed_of_light = 299792458  # m/s

    @staticmethod
    def calculate_position_from_angle(angle, orbit_radius):
        """Calculate position from angle"""
        return Position(
            x=orbit_radius * np.sin(np.deg2rad(angle)),
            y=orbit_radius * np.cos(np.deg2rad(angle)),
        )

    @staticmethod
    def global_coordinate_to_local(global_position):
        """Convert global coordinates to local coordinates"""
        earth_base_position = Position(0, Earth.radius)

        return Position(
            x=global_position.x - earth_base_position.x,
            y=global_position.y - earth_base_position.y,
        )
