from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np

from ..matrices.decision_matrices import DecisionMatrices, MatrixType
from ..matrices.matrix import Matrix
from ..networks.network import Network


class OptimizationStrategy(ABC):
    """Base class for optimization strategies"""

    def __init__(self, matrices: DecisionMatrices, network: Network):
        """Initialize optimization strategy.

        Args:
            matrices: Decision matrices containing network state
            network: Network to optimize
        """
        self.matrices = matrices
        self.network = network

    @abstractmethod
    def optimize(self, matrix_history: List[Dict[MatrixType, np.ndarray]]) -> Matrix:
        """Optimize power states using historical data.

        Args:
            matrix_history: List of historical matrix states

        Returns:
            Updated power state matrix (Matrix B)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name for display/logging.

        Returns:
            Strategy name
        """
        pass


class AllOnStrategy(OptimizationStrategy):
    """Simple strategy that keeps all nodes powered on"""

    def optimize(self, matrix_history: List[Dict[MatrixType, np.ndarray]]) -> Matrix:
        num_nodes = len(self.network.nodes)
        power_matrix = np.ones((num_nodes, num_nodes))

        # Create and update matrix B
        power_state_matrix = Matrix(num_nodes, num_nodes, "Power State Matrix")
        power_state_matrix.update(power_matrix)

        # Update the power state matrix in DecisionMatrices
        self.matrices.set_matrix(MatrixType.POWER_STATE, power_state_matrix)

        return power_state_matrix

    def get_name(self) -> str:
        return "All On Strategy"


class RandomStrategy(OptimizationStrategy):
    """Strategy that randomly turns nodes on/off with given probability"""

    def __init__(
        self, matrices: DecisionMatrices, network: Network, probability: float = 0.5
    ):
        """Initialize random strategy.

        Args:
            matrices: Decision matrices
            network: Network to optimize
            probability: Probability of a node being turned on (default: 0.5)
        """
        super().__init__(matrices, network)
        self.probability = probability

    def optimize(self, matrix_history: List[Dict[MatrixType, np.ndarray]]) -> Matrix:
        num_nodes = len(self.network.nodes)

        # Generate random power states based on probability
        power_matrix = np.random.random((num_nodes, num_nodes)) < self.probability

        # Example: Adjust probability based on historical request patterns
        if matrix_history:
            recent_requests = matrix_history[-1][MatrixType.REQUEST]
            # Adjust probability based on request patterns
            self.probability = np.mean(recent_requests) + 0.5

        power_matrix = power_matrix.astype(float)

        # Create and update matrix B
        power_state_matrix = Matrix(num_nodes, num_nodes, "Power State Matrix")
        power_state_matrix.update(power_matrix)

        # Update the power state matrix in DecisionMatrices
        self.matrices.set_matrix(MatrixType.POWER_STATE, power_state_matrix)

        return power_state_matrix

    def get_name(self) -> str:
        return f"Random Strategy (p={self.probability})"
