from abc import ABC

import numpy as np

from optimisation_ntn.utils.type import Position


class Earth(ABC):
    radius = 6.371e6  # m

    @staticmethod
    def calculate_position_from_angle(angle, orbit_radius):
        return Position(
            x=orbit_radius * np.sin(np.deg2rad(angle)),
            y=orbit_radius * np.cos(np.deg2rad(angle)),
        )

    @staticmethod
    def global_coordinate_to_local(global_position):
        earth_base_position = Position(0, Earth.radius)

        return Position(
            x=global_position.x - earth_base_position.x,
            y=global_position.y - earth_base_position.y,
        )
