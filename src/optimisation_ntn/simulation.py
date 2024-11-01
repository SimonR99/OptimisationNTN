""" Simulation class that instantiates the Network class and runs the simulation. """

import argparse
import random
import string

from optimisation_ntn.matrices.base_matrice import Matrice
from optimisation_ntn.networks.network import Network
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.type import Position


class Simulation:
    """Class to run the simulation."""

    max_time = 3000

    def __init__(self, initial_dimension: int = 6):
        self.network = Network()
        self.matrix_a = Matrice(initial_dimension, initial_dimension, "matrice A")
        self.matrix_b = Matrice(initial_dimension, initial_dimension, "matrice B")
        self.matrix_k = Matrice(initial_dimension, initial_dimension, "matrice K")
        self.matrix_s = Matrice(initial_dimension, initial_dimension, "matrice S")
        self.matrix_x = Matrice(initial_dimension, initial_dimension, "matrice X")

        # Initialize with default values
        self.set_base_stations(1)
        self.set_haps(1)
        self.set_users(0)

    def set_base_stations(self, num_base_stations: int):
        """Remove all existing base stations and create new ones."""
        # Remove all existing base stations
        self.network.nodes = [
            node for node in self.network.nodes if not isinstance(node, BaseStation)
        ]

        # Add new base stations
        start_x = -(num_base_stations - 1) * 1.5 / 2
        for i in range(num_base_stations):
            x_pos = start_x + (i * 1.5)
            base_station = BaseStation(i, Position(x_pos, 0))
            self.network.add_node(base_station)

    def set_haps(self, num_haps: int):
        """Remove all existing HAPS and create new ones."""
        # Remove all existing HAPS
        self.network.nodes = [
            node for node in self.network.nodes if not isinstance(node, HAPS)
        ]

        # Add new HAPS
        start_x = -(num_haps - 1) * 2 / 2
        height = 20  # Height for HAPS layer
        for i in range(num_haps):
            x_pos = start_x + (i * 2)
            haps = HAPS(i, Position(x_pos, height))
            self.network.add_node(haps)

    def set_users(self, num_users: int):
        """Remove all existing users and create new ones with random positions."""
        # Remove all existing users
        self.network.nodes = [
            node for node in self.network.nodes if not isinstance(node, UserDevice)
        ]

        # Add new users with random positions
        for i in range(num_users):
            # Random position between -4 and 4 on x-axis
            x_pos = random.uniform(-4, 4)
            height = -2  # Height for users (below base stations)
            user = UserDevice(i, Position(x_pos, height))
            self.network.add_node(user)

    def reset_network(self):
        """Reset the network to its initial state."""
        self.network = Network()
        self.set_base_stations(1)
        self.set_haps(1)
        self.set_users(0)

    def run(self):
        for _ in range(self.max_time):
            self.network.tick()

    def reset(self):
        pass  # TODO
