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
    def __init__(self, dimension: int):
        """Initialize matrices used in network decision processes."""
        self.matrices: Dict[MatrixType, Matrix] = {
            MatrixType.COVERAGE_ZONE: Matrix(
                dimension, dimension, "Coverage Zone Matrix"
            ),
            MatrixType.POWER_STATE: Matrix(dimension, dimension, "Power State Matrix"),
            MatrixType.REQUEST: Matrix(dimension, dimension, "Request Matrix"),
            MatrixType.ASSIGNMENT: Matrix(dimension, dimension, "Assignment Matrix"),
        }

        print("Matrices initialized")
        print(self.matrices)

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
        self, num_users: int, simulation_time: float, mean_arrival_rate: float = 0.1
    ):
        """Generate request matrix using Poisson distribution"""
        request_matrix = np.zeros((num_users, int(simulation_time)))

        for user in range(num_users):
            # Generate Poisson process for request arrivals
            arrivals = np.random.poisson(mean_arrival_rate, int(simulation_time))
            request_matrix[user, :] = arrivals

        self.matrices["K"].update(request_matrix)

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

    def get_matrix(self, name: str | MatrixType) -> Matrix:
        """Get matrix by name or enum value.
        
        Args:
            name: Matrix name as string or MatrixType enum
            
        Returns:
            The requested matrix
            
        Raises:
            ValueError: If matrix doesn't exist
        """
        try:
            if isinstance(name, str):
                # Try to find matching enum by value
                matrix_type = next(t for t in MatrixType if t.value == name)
                return self.matrices[matrix_type]
            return self.matrices[name]
        except (KeyError, StopIteration):
            raise ValueError(f"Matrix '{name}' does not exist.")

    def set_matrix(self, name: str | MatrixType, matrix: Matrix):
        """Set matrix by name or enum value.
        
        Args:
            name: Matrix name as string or MatrixType enum
            matrix: Matrix to set
            
        Raises:
            ValueError: If matrix name is invalid
        """
        try:
            if isinstance(name, str):
                matrix_type = next(t for t in MatrixType if t.value == name)
                self.matrices[matrix_type] = matrix
            else:
                self.matrices[name] = matrix
        except StopIteration:
            raise ValueError(f"Unknown matrix name: {name}")
