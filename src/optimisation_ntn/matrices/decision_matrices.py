from enum import Enum
from typing import Dict

import numpy as np

from ..nodes.base_station import BaseStation
from ..nodes.haps import HAPS
from ..nodes.leo import LEO
from ..nodes.user_device import UserDevice
from .matrix import Matrix


class MatrixType(Enum):
    COVERAGE_ZONE = "A"
    POWER_STATE = "B"
    REQUEST = "K"
    ASSIGNMENT = "X"


class DecisionMatrices:
    def __init__(self, dimension: int = 0):
        """Initialize matrices used in network decision processes."""
        self.matrices: Dict[MatrixType, Matrix] = {
            MatrixType.COVERAGE_ZONE: Matrix(
                dimension, dimension, "Coverage Zone Matrix"
            ),
            MatrixType.POWER_STATE: Matrix(dimension, dimension, "Power State Matrix"),
            MatrixType.REQUEST: Matrix(dimension, dimension, "Request Matrix"),
            MatrixType.ASSIGNMENT: Matrix(dimension, dimension, "Assignment Matrix"),
        }

    def compute_coverage_zones(self, network, coverage_radius: float = 5000):
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

        self.matrices[MatrixType.COVERAGE_ZONE].update(coverage_matrix)

    def generate_request_matrix(
        self, num_requests: int, num_steps: int
    ):
        """Generate request matrix where each user generates exactly one request.
        
        Args:
            num_requests: Number of users (each will generate one request)
            num_steps: Number of time steps to distribute requests over
        
        Raises:
            ValueError: If num_requests or num_steps is less than or equal to 0
        """
        if num_requests <= 0:
            raise ValueError("Number of requests must be positive")
        if num_steps <= 0:
            raise ValueError("Number of time steps must be positive")
        
        count = 0
        while True:
            ps = np.random.poisson(num_requests / num_steps, num_steps)
            count += 1
            if np.sum(ps) == num_requests:
                matrix = np.zeros((num_requests, num_steps), dtype=int)
                row_index = 0
                for tick, count in enumerate(ps):
                    for _ in range(count):
                        matrix[row_index, tick] = 1
                        row_index += 1
                self.matrices[MatrixType.REQUEST].update(matrix)
                break

    def update_assignment_matrix(self, network):
        """Update real-time request assignment matrix"""
        users = [n for n in network.nodes if isinstance(n, UserDevice)]
        servers = [n for n in network.nodes if isinstance(n, (BaseStation, HAPS, LEO))]

        assignment_matrix = np.zeros((len(users), len(servers)))

        # Assign requests based on current network state and active links
        for i, user in enumerate(users):
            for j, server in enumerate(servers):
                for link in network.communication_links:
                    if link.node_a == user and link.node_b == server:
                        assignment_matrix[i, j] = 1 if link.transmission_queue else 0

        self.matrices["X"].update(assignment_matrix)

    def get_matrix(self, name: MatrixType | str) -> Matrix:
        """Get matrix by name or enum value.

        Args:
            name: Matrix name as string or MatrixType enum

        Returns:
            The requested matrix

        Raises:
            ValueError: If matrix doesn't exist
        """
        try:
            # If it's already a MatrixType, use it directly
            if isinstance(name, MatrixType):
                return self.matrices[name]
            # If it's a string, convert to MatrixType
            return self.matrices[MatrixType(name)]
        except (KeyError, ValueError):
            raise ValueError(f"Matrix '{name}' does not exist.")

    def set_matrix(self, name: MatrixType, matrix: Matrix) -> None:
        """Set matrix by name or enum value.

        Args:
            name: Matrix name as string or MatrixType enum
            matrix: Matrix to store

        Raises:
            ValueError: If matrix name type is invalid
        """
        matrix_type = name if isinstance(name, MatrixType) else MatrixType(name)
        self.matrices[matrix_type] = matrix

    def get_snapshot(self) -> Dict[MatrixType, np.ndarray]:
        """Create a snapshot of current matrices state"""
        return {
            matrix_type: matrix.data.copy()
            for matrix_type, matrix in self.matrices.items()
        }
