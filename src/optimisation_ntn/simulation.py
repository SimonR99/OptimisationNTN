""" Simulation class that instantiates the Network class and runs the simulation. """

import random
from typing import Optional

from .networks.network import Network
from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.leo import LEO
from .nodes.user_device import UserDevice
from .utils.type import Position


class Simulation:
    """Class to run the simulation."""

    DEFAULT_BS_COUNT = 4
    DEFAULT_HAPS_COUNT = 1
    DEFAULT_LEO_COUNT = 1
    DEFAULT_USER_COUNT = 0
    MAX_SIMULATION_TIME = 1000

    def __init__(self):
        self.current_time = 0.0
        self.current_step = 0
        self.step_duration = 0.1  # Duration of each simulation step in seconds
        self.network = Network()
        self.is_paused = False

        # Initialize with default values
        self.initialize_default_nodes()

    def step(self):
        """Execute one simulation step"""
        if self.current_time < self.MAX_SIMULATION_TIME and not self.is_paused:
            # Update network with step duration
            self.network.tick(self.step_duration)
            # Increment counters
            self.current_time += self.step_duration
            self.current_step += 1
            return True
        return False

    def initialize_default_nodes(self, nb_base_station:int = self.DEFAULT_BS_COUNT, nb_haps:int = self.DEFAULT_HAPS_COUNT, nb_leo:int = self.DEFAULT_LEO_COUNT):
        """Initialize network with default nodes or a desired amount"""
        # Add default base stations
        self.set_base_stations(nb_base_station)

        # Add default HAPS
        self.set_haps(nb_haps)

        # Add default LEO satellites
        for i in range(nb_leo):
            self.network.add_node(LEO(i))

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

    def reset(self):
        """Reset simulation to initial state"""
        self.current_time = 0.0
        self.current_step = 0
        self.network = Network()
        self.initialize_default_nodes()
