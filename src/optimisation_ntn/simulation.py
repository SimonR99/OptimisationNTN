""" Simulation class that instantiates the Network class and runs the simulation. """

import random
from typing import Optional
import time

from .algorithms.power_strategy import PowerStateStrategy
from .matrices.decision_matrices import DecisionMatrices
from .networks.network import Network
from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.leo import LEO
from .nodes.user_device import UserDevice
from .utils.position import Position


class Simulation:
    """Class to run the simulation."""

    DEFAULT_BS_COUNT = 4
    DEFAULT_HAPS_COUNT = 1
    DEFAULT_LEO_COUNT = 1
    DEFAULT_USER_COUNT = 5
    MAX_SIMULATION_TIME = 300

    def __init__(self, time_step: float = 0.001, max_time: float = MAX_SIMULATION_TIME):
        self.current_step = 0
        self.current_time = 0.0
        self.time_step = time_step
        self.max_time = max_time
        self.network = Network()
        self.matrices = DecisionMatrices(dimension=0)
        self.strategy: PowerStateStrategy | None = None
        self.matrix_history: list[DecisionMatrices] = []  # Store historical matrices

        # Initialize with default values
        self.initialize_default_nodes()

    @property
    def max_tick_time(self) -> int:
        return self.MAX_SIMULATION_TIME / self.time_step

    def set_strategy(self, strategy: PowerStateStrategy):
        """Set the optimization strategy to use"""
        self.strategy = strategy

    def run(self) -> float:
        """Run simulation until MAX_SIMULATION_TIME.
        Returns:
            float: Total energy consumed during simulation
        """
        start_time = time.time()
        
        # Print simulation parameters
        print("\nStarting simulation with parameters:")
        print(f"Time step: {self.time_step}s")
        print(f"Max simulation time: {self.max_time}s")
        print(f"{self.network}")  # Use Network's string representation
        print("\nSimulation running...\n")

        while self.current_time < self.max_time:
            if not self.step():
                break

        # Calculate execution time and print results
        execution_time = time.time() - start_time
        print("\nSimulation completed:")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Simulation steps: {self.current_step}")
        print(f"Simulated time: {self.current_time:.2f} seconds")
        print(f"Average speed: {self.current_step/execution_time:.0f} steps/second\n")

        # Calculate and return total energy consumed
        return 0  # TODO: Implement energy calculation

    def step(self) -> bool:
        """Run simulation for a single step.
        
        Returns:
            bool: True if simulation can continue, False if simulation should end
        """
        # Update network state
        self.network.tick(self.time_step)
        
        # Update time and step counter
        self.current_time += self.time_step
        self.current_step += 1
        
        # Return False if simulation should end
        return self.current_time < self.max_time

    def reset(self):
        """Reset the simulation to initial state."""
        self.current_time = 0.0
        self.current_step = 0  # Reset step counter
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

    def optimize(self, num_iterations: int = 10) -> tuple[float, list[float]]:
        """Run multiple simulations to optimize energy consumption."""
        start_time = time.time()
        
        print(f"\nStarting optimization with {num_iterations} iterations")
        print("Initial parameters:")
        print(f"Time step: {self.time_step}s")
        print(f"Max simulation time: {self.max_time}s")
        print(f"{self.network}")  # Use Network's string representation
        print("\nOptimization running...\n")
        
        best_energy = float('inf')
        energy_history = []
        
        for i in range(num_iterations):
            print(f"Iteration {i+1}/{num_iterations}")
            energy = self.run()
            energy_history.append(energy)
            
            if energy < best_energy:
                best_energy = energy
                
            self.reset()
            
            if self.strategy:
                self.strategy.update_parameters(energy_history)
        
        # Print optimization results
        execution_time = time.time() - start_time
        print("\nOptimization completed:")
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"Average time per iteration: {execution_time/num_iterations:.2f} seconds")
        print(f"Best energy found: {best_energy}")
        
        return best_energy, energy_history

    def calculate_total_energy(self) -> float:
        """Calculate total energy consumed during simulation.
        
        Returns:
            float: Total energy consumption
        """
        total_energy = 0.0
        for matrix in self.matrix_history:
            # Sum energy consumption from each matrix snapshot
            total_energy += matrix.calculate_energy()
        return total_energy
