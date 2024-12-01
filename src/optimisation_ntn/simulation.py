""" Simulation class that instantiates the Network class and runs the simulation. """

import random
import time
from typing import Optional
import csv
import os
import numpy as np
import matplotlib.pyplot as plt

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
    DEFAULT_USER_COUNT = 50

    DEFAULT_TICK_TIME = 0.1
    DEFAULT_MAX_SIMULATION_TIME = 300

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
        """This value is will be positive, however, it is to be minimised; as a greater value, means greater energy consumption"""
        self.system_energy_consumed = 0
        self.energy_consumption_graph_x = []
        self.energy_consumption_graph_y = np.arange(0, 300.1, 0.1)
        self.total_energy_bs = 0
        self.total_energy_haps = 0
        self.total_energy_leo = 0

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

        # Calculate total energy consumed
        self.system_energy_consumed = self.network.get_total_energy_consumed()
        print("\nSimulation completed:")
        print(f"Total requests: {self.total_requests}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Simulation steps: {self.current_step}")
        print(f"Simulated time: {self.current_time:.2f} seconds")
        print(f"Average speed: {self.current_step/execution_time:.0f} steps/second")
        print(f"Total energy consumed: {self.system_energy_consumed} joules\n")

        # Print request statistics (always show these)
        print("\nRequest Statistics:")
        for status, count in self.request_stats.items():
            print(f"{status.name}: {count}")

        if self.debug:
            self.consumed_energy_graph()

        # Statistics gathering for total energy consumed for each group of node
        self.total_energy_bs = self.network.get_energy_bs()
        self.total_energy_haps = self.network.get_energy_haps()
        self.total_energy_leo = self.network.get_energy_leo()

        self.collect_graph_data()

        return self.system_energy_consumed

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
        compute_nodes = self.network.get_compute_nodes()

        # Create new requests for users
        for i, request_flag in enumerate(new_requests):
            if request_flag == 1 and i < len(user_devices):
                user = user_devices[i]

                # Find closest available compute node
                closest_compute = None
                min_distance = float("inf")

                for compute_node in compute_nodes:
                    if compute_node.state and compute_node.processing_frequency > 0:
                        distance = user.position.distance_to(compute_node.position)
                        if distance < min_distance:
                            min_distance = distance
                            closest_compute = compute_node

                # Create request to closest compute node if found
                if closest_compute:
                    request = user.spawn_request(self.current_step, closest_compute)
                    self.debug_print(
                        f"Created request from {user} to {closest_compute} (distance: {min_distance:.2f})"
                    )

                    # Try to route the request through the network
                    if self.network.route_request(request):
                        self.debug_print(f"Request {request.id} routed successfully")
                        self.total_requests += 1
                    else:
                        self.debug_print(f"Failed to route request {request.id}")
                else:
                    self.debug_print(f"No available compute nodes found for {user}")

        # Update network state (transfer + processing)
        self.network.tick(self.time_step)

        # Update assignment matrix and stats
        self.matrices.update_assignment_matrix(self.network)
        self.update_request_stats()

        # Update time and step counter
        self.current_time += self.time_step
        self.current_step += 1
        self.system_energy_consumed = self.network.get_total_energy_consumed()
        self.energy_consumption_graph_x.append(self.system_energy_consumed)
        return self.current_time < self.max_time

    def export_to_csv(self, filename, data, headers):
        """Export data to a CSV file."""
        # Ensure the directory exists
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        try:
            # Write data to the CSV file
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                if headers:  # Write headers only if provided
                    writer.writerow(headers)
                if isinstance(data[0], (list, tuple)):  # Check if data is iterable
                    writer.writerows(data)
                else:
                    writer.writerows([[d] for d in data])  # Convert flat data to rows
            print(f"Data successfully exported to {os.path.abspath(filename)}")
        except Exception as e:
            print(f"Error while writing to {os.path.abspath(filename)}: {e}")

    def collect_graph_data(self):
        """Collect data for different plots."""
        # Collect data for plots
        success_rate_vs_total_requests = [[self.total_requests, self.evaluate_qos_satisfaction()]]
        energy_consumed_data = [
            [self.total_requests, self.total_energy_bs],
            [self.total_requests, self.total_energy_haps],
            [self.total_requests, self.total_energy_leo]
        ]
        completed_requests_data = [[self.total_requests, self.total_energy_bs + self.total_energy_haps + self.total_energy_leo]]

        # Define the directory for results
        base_directory = os.path.join(os.getcwd(), "OptimisationNTN/results")
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)

        # Export data to CSV files
        self.export_to_csv(
            os.path.join(base_directory, "success_rate_vs_request.csv"),
            success_rate_vs_total_requests,
            ["Number of Requests", "Success Rate"]
        )
        self.export_to_csv(
            os.path.join(base_directory, "energy_consumed_vs_request.csv"),
            energy_consumed_data,
            ["Number of Requests", "Energy Consumed (by type)"]
        )
        self.export_to_csv(
            os.path.join(base_directory, "energy_vs_completed.csv"),
            completed_requests_data,
            ["Completed Requests", "Total Energy Consumed"]
        )

        print(f"CSV files generated in: {base_directory}")

    def reset(self):
        """Reset the simulation to initial state."""
        self.current_time = 0.0
        self.current_step = 0
        self.network = Network()
        self.matrix_history.clear()
        self.total_requests = 0
        self.request_stats = {status: 0 for status in RequestStatus}
        self.system_energy_consumed = 0
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

    def consumed_energy_graph(self):
        plt.plot(
            self.energy_consumption_graph_y,
            self.energy_consumption_graph_x,
            color="blue",
            marker=".",
        )
        plt.title("Energy consumption")
        plt.xlabel("Secondes")
        plt.ylabel("Cumulative system energy consumed")
        plt.show()

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
