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
    DEFAULT_USER_COUNT = 20

    DEFAULT_TICK_TIME = 0.1
    DEFAULT_MAX_SIMULATION_TIME = 10

    def __init__(
        self,
        time_step: float = DEFAULT_TICK_TIME,
        max_time: float = DEFAULT_MAX_SIMULATION_TIME,
        debug: bool = False,
    ):
        self.current_step = 0
        self.current_time = 0.0
        self.time_step = time_step
        self.max_time = max_time
        self.network = Network(debug=debug)
        self.matrices = DecisionMatrices(dimension=self.DEFAULT_USER_COUNT)
        self.strategy: PowerStateStrategy | None = None
        self.matrix_history: list[DecisionMatrices] = []
        self.total_requests = 0
        self.request_stats = {status: 0 for status in RequestStatus}
        self.is_paused = False
        self.debug = debug

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

        # Print simulation parameters (always show these)
        print("\nStarting simulation with parameters:")
        print(f"Time step: {self.time_step}s")
        print(f"Max simulation time: {self.max_time}s")
        print(f"{self.network}")
        print("\nSimulation running...\n")

        while self.current_time < self.max_time:
            if not self.step():
                break

        # QoS Evaluation
        success_rate = self.evaluate_qos_satisfaction()
        print(f"\nQoS Success Rate: {success_rate:.2f}%")

        # Calculate execution time and print results (always show these)
        execution_time = time.time() - start_time
        print("\nSimulation completed:")
        print(f"Total requests: {self.total_requests}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Simulation steps: {self.current_step}")
        print(f"Simulated time: {self.current_time:.2f} seconds")
        print(f"Average speed: {self.current_step/execution_time:.0f} steps/second\n")

        # Print request statistics (always show these)
        print("\nRequest Statistics:")
        for status, count in self.request_stats.items():
            print(f"{status.name}: {count}")

        return 0  # TODO: Implement energy calculation

    def evaluate_qos_satisfaction(self) -> float:
        """Evaluate QoS satisfaction for all requests."""
        satisfied_requests = 0

        for user in [n for n in self.network.nodes if isinstance(n, UserDevice)]:
            for request in user.current_requests:

                if request.satisfaction:
                    satisfied_requests += 1

        if self.total_requests == 0:
            return 100.0  # No requests, success rate is 100%

        success_rate = (satisfied_requests / self.total_requests) * 100
        return success_rate

    def step(self) -> bool:
        """Run simulation for a single step."""
        # Get new requests from request matrix for this tick
        new_requests = self.matrices.get_matrix(MatrixType.REQUEST)[
            :, self.current_step
        ]

        # Get user devices and compute nodes
        user_devices = [n for n in self.network.nodes if isinstance(n, UserDevice)]

        # Create new requests for users
        for i, request_flag in enumerate(new_requests):
            if request_flag == 1:
                user = user_devices[i]

                # Create the request
                request = user.create_request(self.current_step)
                compute_nodes = self.network.get_compute_nodes(request)

                # Find optimal compute node based on both compute and network delay
                best_node = None
                best_total_time = float("inf")
                best_path = None
                for compute_node in compute_nodes:
                    # Estimate processing time based on node's compute capacity
                    processing_time = compute_node.processing_time(request)
                    path = self.network.generate_request_path(user, compute_node)
                    network_delay = self.network.get_network_delay(request, path)
                    total_time = processing_time + network_delay

                    if total_time < best_total_time:
                        best_total_time = total_time
                        best_node = compute_node
                        best_path = path

                # If we found a suitable compute node, assign it and initialize routing
                if best_node:
                    user.assign_target_node(request, best_node)
                    request.path = best_path
                    request.path_index = 1
                    request.status = RequestStatus.IN_TRANSIT

                    # Add request to first transmission queue
                    current_node = request.path[0]
                    next_node = request.path[1]

                    # Find the appropriate link
                    for link in self.network.communication_links:
                        if link.node_a == current_node and link.node_b == next_node:
                            link.add_to_queue(request)
                            request.next_node = next_node
                            self.debug_print(
                                f"Added request {request.id} to transmission queue: {current_node} -> {next_node}"
                            )
                            break

                    self.total_requests += 1
                else:
                    self.debug_print(f"No available compute nodes found for {user}")

        # Update network state
        self.network.tick(self.time_step)

        # Update matrices and stats
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
        self.set_nodes(BaseStation, nb_base_station)

        # Add default HAPS
        self.set_nodes(HAPS, nb_haps)

        # Add default LEO satellites
        for i in range(nb_leo):
            self.network.add_node(LEO(i))

        # Add default user devices
        self.set_nodes(UserDevice, self.DEFAULT_USER_COUNT)

    def set_nodes(self, node_type: type, count: int, **kwargs):
        """Generic method to set nodes of a specific type."""
        # Remove existing nodes of this type
        self.network.nodes = [
            node for node in self.network.nodes if not isinstance(node, node_type)
        ]

        # Add new nodes based on type
        if node_type == BaseStation:
            start_x = -(count - 1) * 1.5 / 2
            for i in range(count):
                x_pos = start_x + (i * 1.5)
                self.network.add_node(
                    node_type(i, Position(x_pos, 0), debug=self.debug)
                )

        elif node_type == HAPS:
            start_x = -(count - 1) * 2 / 2
            height = 20
            for i in range(count):
                x_pos = start_x + (i * 2)
                self.network.add_node(node_type(i, Position(x_pos, height)))

        elif node_type == UserDevice:
            for i in range(count):
                x_pos = random.uniform(-4, 4)
                height = -2
                self.network.add_node(node_type(i, Position(x_pos, height)))

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

        # Generate request matrix using the new counting method
        self.matrices.generate_request_matrix(
            num_requests=self.network.count_nodes_by_type(UserDevice),
            num_steps=matrix_size,
        )

        # Generate coverage matrix
        self.matrices.generate_coverage_matrix(self.network)

        # Generate power matrix using the new counting method
        num_devices = (
            self.network.count_nodes_by_type(HAPS)
            + self.network.count_nodes_by_type(BaseStation)
            + self.network.count_nodes_by_type(LEO)
        )
        self.matrices.generate_power_matrix(
            num_devices=num_devices,
            num_steps=matrix_size,
            strategy=AllOnStrategy(),
        )

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)
