from abc import ABC, abstractmethod

import numpy as np


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

    def get_name(self) -> str:
        """Get strategy name for display/logging.

        Returns:
            Strategy name
        """
        return self.__class__.__name__


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
            p=[1 - self.probability, self.probability],
        ).astype(int)

    def get_name(self) -> str:
        return f"Random Strategy (p={self.probability})"


class StaticRandomStrategy(PowerStateStrategy):
    """Strategy that randomly turns nodes on/off at the start and maintains those states"""

    def generate_power_matrix(self, num_devices: int, num_steps: int) -> np.ndarray:
        """Generate a power matrix where each node's state is randomly chosen once
        and remains constant throughout the simulation.

        Args:
            num_devices: Number of devices to generate states for
            num_steps: Number of time steps in the simulation

        Returns:
            np.ndarray: Power state matrix with shape (num_devices, num_steps)
        """
        # Generate random initial states for each device (0 or 1)
        initial_states = np.random.randint(0, 2, size=num_devices)

        # Repeat these states for all time steps
        power_matrix = np.tile(initial_states.reshape(-1, 1), (1, num_steps))

        return power_matrix

    def update_parameters(self, energy_history: list[float]) -> None:
        """No parameter updates needed for static strategy"""
        pass
