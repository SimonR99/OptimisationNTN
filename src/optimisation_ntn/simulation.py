""" Simulation class that instantiates the Network class and runs the simulation. """

import random
from typing import Optional

from .networks.network import Network
from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.leo import LEO
from .nodes.user_device import UserDevice
from .utils.position import Position
from .algorithms.optimization_strategy import OptimizationStrategy
from .matrices.decision_matrices import DecisionMatrices


class Simulation:
    """Class to run the simulation."""

    DEFAULT_BS_COUNT = 4
    DEFAULT_HAPS_COUNT = 1
    DEFAULT_LEO_COUNT = 1
    DEFAULT_USER_COUNT = 0
    MAX_SIMULATION_TIME = 1000

    def __init__(self, time_step: float = 1.0):
        self.current_time = 0.0
        self.time_step = time_step
        self.network = Network()
        self.matrices = DecisionMatrices(dimension=0)
        self.strategy: OptimizationStrategy | None = None
        self.is_running = False
        self.matrix_history = []  # Store historical matrices
        
        # Initialize with default values
        self.initialize_default_nodes()

    def set_strategy(self, strategy: OptimizationStrategy):
        """Set the optimization strategy to use"""
        self.strategy = strategy

    def run(self, duration: float):
        """Run simulation for specified duration"""
        self.is_running = True
        end_time = self.current_time + duration

        while self.current_time < end_time and self.is_running:
            # Store current matrices state in history
            self.matrix_history.append(self.matrices.get_snapshot())
            
            # Update network state
            self.network.update(self.current_time)
            
            # Optimize power states if strategy is set
            if self.strategy:
                self.strategy.optimize(self.matrix_history)
                
            self.current_time += self.time_step

    def pause(self):
        self.is_running = False

    def resume(self):
        self.is_running = True

    def reset(self):
        self.current_time = 0.0
        self.is_running = False
        self.network = Network()
        self.matrix_history.clear()
        self.initialize_default_nodes()

    def initialize_default_nodes(
        self,
        nb_base_station: int = DEFAULT_BS_COUNT,
        nb_haps: int = DEFAULT_HAPS_COUNT,
        nb_leo: int = DEFAULT_LEO_COUNT,
    ):
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
