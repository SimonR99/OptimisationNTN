""" Decision matrices class """

from enum import Enum
from typing import Dict

import numpy as np

from ..networks.network import Network
from ..networks.request import RequestStatus
from ..nodes.base_station import BaseStation
from ..nodes.user_device import UserDevice


class MatrixType(Enum):
    """Matrix type enum"""

    COVERAGE_ZONE = "A"
    POWER_STATE = "B"
    REQUEST = "K"
    ASSIGNMENT = "X"


class DecisionMatrices:
    """Decision matrices class"""

    def __init__(self, dimension: int = 0):
        """Initialize matrices used in network decision processes."""
        self.matrices: Dict[MatrixType, np.ndarray] = {
            MatrixType.COVERAGE_ZONE: np.zeros((dimension, dimension)),
            MatrixType.POWER_STATE: np.zeros((dimension, dimension)),
            MatrixType.REQUEST: np.zeros((dimension, dimension)),
            MatrixType.ASSIGNMENT: np.zeros((dimension, dimension)),
        }

    def generate_coverage_matrix(self, network, coverage_radius: float = 5000):
        """Pre-compute coverage zones for base stations.
        For each user, marks only the closest base station(s) within coverage range.

        Args:
            network: Network containing users and base stations
            coverage_radius: Maximum coverage radius to consider for all base stations
        """
        users = [n for n in network.nodes if isinstance(n, UserDevice)]
        base_stations = [n for n in network.nodes if isinstance(n, BaseStation)]

        coverage_matrix = np.zeros((len(users), len(base_stations)))

        for i, user in enumerate(users):
            # Calculate distances to all base stations
            distances = [user.position.distance_to(bs.position) for bs in base_stations]
            in_range_indices = [
                j for j, dist in enumerate(distances) if dist <= coverage_radius
            ]

            if in_range_indices:  # If there are base stations in range
                # Find the closest base station(s)
                min_distance = min(distances[j] for j in in_range_indices)
                # Mark only the closest base station(s)
                for j in in_range_indices:
                    if distances[j] == min_distance:
                        coverage_matrix[i, j] = 1

        self.matrices[MatrixType.COVERAGE_ZONE] = coverage_matrix

    def generate_request_matrix(
        self, num_requests: int, num_steps: int, time=0.1, time_buffer=None
    ):
        """Generate request matrix where each user generates exactly one request."""
        np.random.seed(42)
        if num_requests <= 0 or num_steps <= 0:
            raise ValueError("Number of requests and steps must be positive")

        if time_buffer is None:
            request_matrix = np.zeros((num_requests, num_steps))
        else:
            num_steps = num_steps - int(time_buffer / time)
            request_matrix = np.zeros((num_requests, num_steps))

        # Generate Poisson distribution of requests
        count = 0
        while True:
            ps = np.random.poisson(num_requests / num_steps, num_steps)
            count += 1
            if np.sum(ps) == num_requests or count > 1000:  # Add timeout
                row_index = 0
                for tick, count in enumerate(ps):
                    for _ in range(count):
                        if row_index < num_requests:
                            request_matrix[row_index, tick] = 1
                            row_index += 1
                self.matrices[MatrixType.REQUEST] = request_matrix
                break

        # Add padding to the request matrix if time_buffer is provided (padding with 0s)
        if time_buffer is not None:
            self.matrices[MatrixType.REQUEST] = np.pad(
                request_matrix, (0, int(time_buffer / time)), mode="constant"
            )

    def update_assignment_matrix(self, network: Network):
        """Update real-time request assignment matrix"""
        users = [n for n in network.nodes if isinstance(n, UserDevice)]
        compute_nodes = network.get_compute_nodes(check_state=False)

        assignment_matrix = np.zeros((len(users), len(compute_nodes)))

        # Check each user's active requests
        for i, user in enumerate(users):
            for request in user.current_requests:
                if request.status == RequestStatus.PROCESSING:
                    # Find index of compute node processing this request
                    for j, node in enumerate(compute_nodes):
                        if node == request.current_node:
                            assignment_matrix[i, j] = 1
                            break

        self.matrices[MatrixType.ASSIGNMENT] = assignment_matrix

    def get_matrix(self, name: MatrixType) -> np.ndarray:
        """Get matrix by enum value.

        Args:
            name: MatrixType enum

        Returns:
            The requested matrix

        Raises:
            ValueError: If matrix doesn't exist
        """
        try:
            return self.matrices[name]
        except KeyError as exc:
            raise ValueError(f"Matrix '{name}' does not exist.") from exc

    def set_matrix(self, name: MatrixType, matrix: np.ndarray) -> None:
        """Set matrix by enum value.

        Args:
            name: Matrix name as MatrixType enum
            matrix: Matrix to store

        Raises:
            ValueError: If matrix name type is invalid
        """
        matrix_type = name if isinstance(name, MatrixType) else MatrixType(name)
        self.matrices[matrix_type] = matrix

    def get_snapshot(self) -> Dict[MatrixType, np.ndarray]:
        """Create a snapshot of current matrices state"""
        return {
            matrix_type: matrix.copy() for matrix_type, matrix in self.matrices.items()
        }
