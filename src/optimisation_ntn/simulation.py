""" Simulation class that instantiates the Network class and runs the simulation. """

import random
import time
from typing import Literal, Optional
from dataclasses import dataclass

import numpy as np
import pandas as pd

from optimisation_ntn.networks.request import Request, RequestStatus

from .algorithms.assignment.matrix_based import MatrixBasedAssignment
from .algorithms.assignment.strategy_factory import AssignmentStrategyFactory
from .matrices.decision_matrices import DecisionMatrices, MatrixType
from .networks.network import Network
from .nodes.base_station import BaseStation
from .nodes.haps import HAPS
from .nodes.leo import LEO
from .nodes.user_device import UserDevice
from .utils.position import Position


# pylint: disable=too-many-instance-attributes
@dataclass
class SimulationConfig:
    """Configuration class for Simulation parameters."""

    seed: Optional[int] = None
    time_step: float = 0.01
    max_time: float = 10
    debug: bool = False
    user_count: int = 10
    print_output: bool = False
    assignment_strategy: str = "TimeGreedy"
    power_strategy: str = "AllOn"
    save_results: bool = True
    optimizer: None | Literal["GA", "PSO", "DE"] = None
    qtable_path: Optional[str] = None


class Simulation:
    """Class to run the simulation."""

    DEFAULT_BS_COUNT = 4
    DEFAULT_HAPS_COUNT = 1
    DEFAULT_LEO_COUNT = 1
    DEFAULT_USER_COUNT = 10
    DEFAULT_TICK_TIME = 0.01
    DEFAULT_MAX_SIMULATION_TIME = 10

    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize simulation with given configuration."""
        if config is None:
            config = SimulationConfig()

        # Set the random seed if provided
        if config.seed is not None:
            random.seed(config.seed)

        self.config = config
        self.user_count = config.user_count
        self.current_step = 0
        self.current_time = 0.0
        self.time_step = config.time_step
        self.max_time = config.max_time
        self.seed = config.seed
        self.debug = config.debug
        self.matrices = DecisionMatrices(dimension=config.user_count)
        self.network = Network(debug=self.debug, power_strategy=config.power_strategy)
        self.assignment_strategy = AssignmentStrategyFactory.get_strategy(
            config.assignment_strategy, self.network, config.qtable_path
        )
        self.save_results = config.save_results
        self.total_requests = 0
        self.is_paused = False
        self.system_energy_consumed = 0
        self.system_energy_history = []
        self.print_output = config.print_output
        self.optimizer = config.optimizer

        self.track_stats = False

        # Initialize stats only when needed
        self.request_state_stats = {}

        # UI variables
        self.steps_since_last_ui_update = 0

        # self.reset()
        self.reset()

    @property
    def max_tick_time(self) -> int:
        """Calculate the maximum number of simulation steps."""
        return int(self.max_time / self.time_step)

    def run(self) -> float:
        """Run simulation until self.max_time.
        Returns:
            float: Total energy consumed during simulation
        """
        start_time = time.time()

        # Print simulation parameters (always show these)
        if self.print_output:
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

        # Calculate execution time and print results (always show these)
        execution_time = time.time() - start_time

        # Calculate total energy consumed
        self.system_energy_consumed = self.network.get_total_energy_consumed()

        # Always collect request list for saving results
        request_list = []
        for user in self.network.user_nodes:
            requests = user.current_requests
            for request in requests:
                request_list.append(request.__dict__)

        # Process statistics only if tracking is enabled
        if self.track_stats:
            self.request_state_stats = {status: 0 for status in RequestStatus}
            for request in request_list:
                self.request_state_stats[request["status"]] += 1

        if self.print_output:
            print("\nSimulation completed:")
            print(f"Total requests: {self.total_requests}")
            print(f"Execution time: {execution_time:.2f} seconds")
            print(f"Simulation steps: {self.current_step}")
            print(f"Simulated time: {self.current_time:.2f} seconds")
            print(f"\nQoS Success Rate: {success_rate:.2f}%")
            print(f"Average speed: {self.current_step/execution_time:.0f} steps/second")
            print(f"Total energy consumed: {self.system_energy_consumed} joules\n")

            if self.track_stats:
                print("\nRequest Statistics:")
                for status, count in self.request_state_stats.items():
                    print(f"{status.name}: {count}")

        if self.save_results:
            if self.optimizer:
                assignment_strategy_name = self.optimizer
            else:
                assignment_strategy_name = self.assignment_strategy.get_name()
            # Save energy history to csv
            energy_history = pd.DataFrame(
                {str(node): node.energy_history for node in self.network.nodes}
            )
            energy_history.to_csv(
                f"output/energy_history_{self.config.power_strategy}_"
                f"{assignment_strategy_name}_{self.user_count}.csv",
                index=False,
            )

            # Save request stats to csv
            request_stats = pd.DataFrame(request_list)
            request_stats.to_csv(
                f"output/request_stats_{self.config.power_strategy}_"
                f"{assignment_strategy_name}_{self.user_count}.csv",
                index=False,
            )

        return self.system_energy_consumed

    def evaluate_qos_satisfaction(self) -> float:
        """Evaluate QoS satisfaction for all requests."""
        satisfied_requests = 0
        failed_requests = 0
        for user in [n for n in self.network.nodes if isinstance(n, UserDevice)]:
            for request in user.current_requests:
                if request.status == RequestStatus.COMPLETED:
                    satisfied_requests += 1
                elif request.status == RequestStatus.FAILED:
                    failed_requests += 1
                else:
                    print(f"request {request.id} is in status {request.status}")
        if self.total_requests == 0:
            return 100.0  # No requests, success rate is 100%

        success_rate = satisfied_requests / (satisfied_requests + failed_requests)
        return success_rate * 100

    def get_current_tick(self):
        """Get current tick"""
        return self.current_step

    def step(self) -> bool:
        """Run simulation for a single step."""
        # Get new requests from request matrix for this tick
        new_requests = self.matrices.get_matrix(MatrixType.REQUEST)[
            :, self.current_step
        ]

        # Get user devices and compute nodes
        user_devices = self.network.user_nodes

        # Create new requests for users
        for i, request_flag in enumerate(new_requests):
            if request_flag == 1:
                user = user_devices[i]

                # Create the request
                request = Request(
                    tick=self.current_step,
                    tick_time=self.time_step,
                    initial_node=user,
                    get_tick=self.get_current_tick,
                    debug=self.debug,
                )
                user.add_request(request)

                # Get available compute nodes
                compute_nodes = self.network.get_compute_nodes(
                    request, check_state=False
                )

                # Use assignment strategy to select node
                best_node, best_path, _ = self.assignment_strategy.select_compute_node(
                    request, self.network.compute_nodes
                )

                # If we found a suitable compute node, assign it and initialize routing
                if best_node:
                    user.assign_target_node(request, best_node)
                    request.path = best_path
                    request.path_index = 1
                    request.update_status(RequestStatus.IN_TRANSIT)

                    # Add request to first transmission queue
                    current_node = request.path[0]
                    next_node = request.path[1]

                    # Find the appropriate link
                    for link in self.network.communication_links:
                        if link.node_a == current_node and link.node_b == next_node:
                            link.add_to_queue(request)
                            request.next_node = next_node
                            self.debug_print(
                                f"Added request {request.id} to transmission queue: "
                                f"{current_node} -> {next_node}"
                            )
                            break

                else:
                    request.update_status(RequestStatus.FAILED)
                    self.debug_print(f"No available compute nodes found for {user}")

                self.total_requests += 1

        # Update network state
        self.network.tick(self.time_step)

        # Update total energy consumed
        self.system_energy_consumed = self.network.get_total_energy_consumed()

        # Track statistics only when needed
        if self.track_stats:
            # Add the energy consumed in this step to history
            step_energy = sum(
                node.energy_history[-1] if node.energy_history else 0
                for node in self.network.compute_nodes
            )
            self.system_energy_history.append(step_energy)

            # Update request statistics
            self.request_state_stats = {status: 0 for status in RequestStatus}
            for user in self.network.user_nodes:
                for request in user.current_requests:
                    self.request_state_stats[request.status] += 1

        # Update time and step counter
        self.current_time += self.time_step
        self.current_step += 1

        return self.current_time < self.max_time

    def reset(self):
        """Reset the simulation to initial state."""
        self.current_time = 0.0
        self.current_step = 0
        self.network = Network(
            debug=self.debug, power_strategy=self.config.power_strategy
        )
        self.total_requests = 0
        self.system_energy_consumed = 0
        self.system_energy_history = []

        self.assignment_strategy = AssignmentStrategyFactory.get_strategy(
            self.config.assignment_strategy, self.network, self.config.qtable_path
        )

        # Reset energy consumption for all nodes
        if self.seed is not None:
            random.seed(self.seed)

        self.initialize_default_nodes()
        self.initialize_matrices()

        if self.track_stats:
            self.system_energy_history = []
            self.request_state_stats = {status: 0 for status in RequestStatus}

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
        self.set_nodes(UserDevice, self.user_count)

    def set_nodes(self, node_type: type, count: int):
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
                    node_type(
                        i,
                        Position(x_pos, 0),
                        debug=self.debug,
                    )
                )

        elif node_type == HAPS:
            start_x = -(count - 1) * 2 / 2
            height = 20
            for i in range(count):
                x_pos = start_x + (i * 2)
                self.network.add_node(
                    node_type(
                        i,
                        Position(x_pos, height),
                    )
                )

        elif node_type == UserDevice:
            for i in range(count):
                x_pos = random.uniform(-4, 4)
                height = -2
                self.network.add_node(
                    node_type(
                        i,
                        Position(x_pos, height),
                    )
                )

    def initialize_matrices(self):
        """Initialize all matrices needed for simulation"""
        # Calculate required matrix size based on simulation parameters
        matrix_size = self.max_tick_time + 1  # Add 1 to include the final step

        # Generate request matrix using the new counting method
        self.matrices.generate_request_matrix(
            num_requests=self.network.count_nodes_by_type(UserDevice),
            num_steps=matrix_size,
            time=self.time_step,
            time_buffer=2,
        )

        # Generate coverage matrix
        self.matrices.generate_coverage_matrix(self.network)

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

    def run_with_assignment(self, assignment_vector: np.ndarray) -> tuple[float, float]:
        """Run simulation with a specific assignment vector.

        Args:
            assignment_vector: Vector specifying node assignments for each request

        Returns:
            tuple[float, float]: (energy consumed, QoS satisfaction rate)
        """
        # Reset simulation state
        self.reset()

        # Create and set matrix-based strategy
        matrix_strategy = MatrixBasedAssignment(self.network)
        matrix_strategy.set_assignment_matrix(assignment_vector)
        self.assignment_strategy = matrix_strategy

        # Run simulation
        energy_consumed = self.run()
        satisfaction_rate = self.evaluate_qos_satisfaction()

        return (
            energy_consumed,
            satisfaction_rate / 100.0,
        )  # Convert percentage to fraction

    def enable_stats_tracking(self):
        """Enable tracking of statistics for UI"""
        self.track_stats = True
        self.request_state_stats = {status: 0 for status in RequestStatus}

    def disable_stats_tracking(self):
        """Disable tracking of statistics"""
        self.track_stats = False
        self.system_energy_history = []
        self.request_state_stats = {}
