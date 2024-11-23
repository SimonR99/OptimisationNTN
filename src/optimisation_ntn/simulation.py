""" Simulation class that instantiates the Network class and runs the simulation. """

import random
import time
from typing import Optional

import numpy as np

from optimisation_ntn.networks.request import Request, RequestStatus

from .algorithms.power_strategy import AllOnStrategy, PowerStateStrategy
from .matrices.decision_matrices import DecisionMatrices, MatrixType
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

    DEFAULT_TICK_TIME = 0.1
    DEFAULT_MAX_SIMULATION_TIME = 300

    def __init__(
        self,
        time_step: float = DEFAULT_TICK_TIME,
        max_time: float = DEFAULT_MAX_SIMULATION_TIME,
    ):
        self.current_step = 0
        self.current_time = 0.0
        self.time_step = time_step
        self.max_time = max_time
        self.network = Network()
        self.matrices = DecisionMatrices(dimension=self.DEFAULT_USER_COUNT)
        self.strategy: PowerStateStrategy | None = None
        self.matrix_history: list[DecisionMatrices] = []
        self.total_requests = 0
        self.request_stats = {status: 0 for status in RequestStatus}
        self.is_paused = False

        # Initialize with default values
        self.initialize_default_nodes()

        # Initialize matrices after network is set up
        self.initialize_matrices()

    @property
    def max_tick_time(self) -> int:
        """Calculate the maximum number of simulation steps."""
        return int(self.max_time / self.time_step)

    def set_strategy(self, strategy: PowerStateStrategy):
        """Set the optimization strategy to use"""
        self.strategy = strategy

    def run(self) -> float:
        """Run simulation until self.max_time.
        Returns:
            float: Total energy consumed during simulation
        """
        start_time = time.time()

        # Print simulation parameters
        print("\nStarting simulation with parameters:")
        print(f"Time step: {self.time_step}s")
        print(f"Max simulation time: {self.max_time}s")
        print(f"{self.network}")
        print("\nSimulation running...\n")

        while self.current_time < self.max_time:
            if not self.step():
                break

        # Calculate execution time and print results
        execution_time = time.time() - start_time
        print("\nSimulation completed:")
        print(f"Total requests: {self.total_requests}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Simulation steps: {self.current_step}")
        print(f"Simulated time: {self.current_time:.2f} seconds")
        print(f"Average speed: {self.current_step/execution_time:.0f} steps/second\n")

        # Print request statistics
        print("\nRequest Statistics:")
        for status, count in self.request_stats.items():
            print(f"{status.name}: {count}")

        return 0  # TODO: Implement energy calculation

    def step(self) -> bool:
        """Run simulation for a single step."""

        # Get new requests from request matrix for this tick
        new_requests = self.matrices.get_matrix(MatrixType.REQUEST).data[
            :, self.current_step
        ]

        # Get user devices and compute nodes
        user_devices = [n for n in self.network.nodes if isinstance(n, UserDevice)]
        compute_nodes = self.network.get_compute_nodes()

        # Create new requests for users
        for i, request_flag in enumerate(new_requests):
            if request_flag == 1 and i < len(user_devices):
                user = user_devices[i]

                # Find closest available compute node
                closest_compute = None
                min_distance = float("inf")

                for compute_node in compute_nodes:
                    if compute_node.state and compute_node.frequency > 0:
                        distance = user.position.distance_to(compute_node.position)
                        if distance < min_distance:
                            min_distance = distance
                            closest_compute = compute_node

                # Create request to closest compute node if found
                if closest_compute:
                    request = user.spawn_request(self.current_step, closest_compute)
                    print(
                        f"Created request from {user} to {closest_compute} (distance: {min_distance:.2f})"
                    )

                    # Try to route the request through the network
                    if self.network.route_request(request):
                        print(f"Request {request.id} routed successfully")
                        self.total_requests += 1
                    else:
                        print(f"Failed to route request {request.id}")
                else:
                    print(f"No available compute nodes found for {user}")

        # Update network state (transfer + processing)
        self.network.tick(self.time_step)

        # Update assignment matrix and stats
        self.matrices.update_assignment_matrix(self.network)
        self.update_request_stats()

        # Update time and step counter
        self.current_time += self.time_step
        self.current_step += 1
        return self.current_time < self.max_time

    def reset(self):
        """Reset the simulation to initial state."""
        self.current_time = 0.0
        self.current_step = 0
        self.network = Network()
        self.matrix_history.clear()
        self.total_requests = 0
        self.request_stats = {status: 0 for status in RequestStatus}
        self.initialize_default_nodes()
        self.initialize_matrices()  # Re-initialize matrices after reset

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

        # Add default user devices
        self.set_users(self.DEFAULT_USER_COUNT)

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

        best_energy = float("inf")
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
        print(
            f"Average time per iteration: {execution_time/num_iterations:.2f} seconds"
        )
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

    def update_request_stats(self):
        """Update statistics for all requests in the network"""
        # Reset stats
        self.request_stats = {status: 0 for status in RequestStatus}

        # Count requests in each state
        for user in [n for n in self.network.nodes if isinstance(n, UserDevice)]:
            for request in user.current_requests:
                self.request_stats[request.status] += 1

    def initialize_matrices(self):
        """Initialize all matrices needed for simulation"""
        # Calculate required matrix size based on simulation parameters
        matrix_size = self.max_tick_time + 1  # Add 1 to include the final step

        # Generate request matrix
        self.matrices.generate_request_matrix(
            num_requests=self.network.count_users(), num_steps=matrix_size
        )

        # Generate coverage matrix
        self.matrices.generate_coverage_matrix(self.network)

        # Generate power matrix
        num_devices = (
            self.network.count_haps()
            + self.network.count_base_stations()
            + self.network.count_leos()
        )
        self.matrices.generate_power_matrix(
            num_devices=num_devices,
            num_steps=matrix_size,
            strategy=AllOnStrategy(),
        )
