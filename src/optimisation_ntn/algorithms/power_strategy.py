from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np

from ..matrices.decision_matrices import DecisionMatrices, MatrixType
from ..matrices.matrix import Matrix
from ..networks.network import Network


class PowerStateStrategy(ABC):
    """Base class for optimization strategies"""

    @abstractmethod
    def generate_power_matrix(self, num_devices: int, num_steps: int) -> np.ndarray:
        """Generate power state matrix for the given number of devices and time steps.
        
        Args:
            num_devices: Number of devices to generate power states for
            num_steps: Number of time steps to plan for
            
        Returns:
            numpy array of shape (num_devices, num_steps) with power states
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name for display/logging.

        Returns:
            Strategy name
        """
        pass


class AllOnStrategy(PowerStateStrategy):
    """Simple strategy that keeps all nodes powered on"""

    def generate_power_matrix(self, num_devices: int, num_steps: int) -> np.ndarray:
        """Generate matrix with all devices powered on for all time steps.
        
        Args:
            num_devices: Number of devices
            num_steps: Number of time steps
            
        Returns:
            Matrix of ones with shape (num_devices, num_steps)
        """
        return np.ones((num_devices, num_steps), dtype=int)

    def get_name(self) -> str:
        return "All On Strategy"


class RandomStrategy(PowerStateStrategy):
    """Strategy that randomly turns nodes on/off with given probability"""

    def __init__(self, probability: float = 0.5):
        """Initialize with probability of node being on.
        
        Args:
            probability: Probability of each node being on at each time step
        """
        self.probability = probability

    def generate_power_matrix(self, num_devices: int, num_steps: int) -> np.ndarray:
        """Generate random power states based on probability.
        
        Args:
            num_devices: Number of devices
            num_steps: Number of time steps
            
        Returns:
            Random binary matrix with shape (num_devices, num_steps)
        """
        return np.random.choice(
            [0, 1],
            size=(num_devices, num_steps),
            p=[1 - self.probability, self.probability]
        ).astype(int)

    def get_name(self) -> str:
        return f"Random Strategy (p={self.probability})"
