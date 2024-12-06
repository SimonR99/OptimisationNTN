import random
from abc import ABC, abstractmethod

import numpy as np
import pygad

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.utils import genetic_config


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


class GeneticAlgorithmStrategy:
    """Optimizes power state configuration using Genetic Algorithm."""

    def __init__(self):
        self.population_size = genetic_config.POPULATION_SIZE
        self.generations = genetic_config.GENERATIONS
        self.mutation_rate = genetic_config.MUTATION_RATE
        self.crossover_rate = genetic_config.CROSSOVER_RATE
        self.num_nodes = Simulation.DEFAULT_COMPUTE_NODES
        self.num_steps = (
            int(Simulation.DEFAULT_MAX_SIMULATION_TIME / Simulation.DEFAULT_TICK_TIME)
            + 1
        )

    @property
    def matrix_size(self):
        """Returns the total size of the matrix (flattened for use with PyGAD)."""
        return self.num_nodes * self.num_steps

    @staticmethod
    def evaluate_solution(power_matrice_genetic, energy_weight=0.8, qos_weight=0.2):
        """
        Evaluates a power state matrix using the simulation.
        """
        simulation = Simulation(
            seed=42,
            time_step=Simulation.DEFAULT_TICK_TIME,
            max_time=Simulation.DEFAULT_MAX_SIMULATION_TIME,
            debug=False,
            user_count=Simulation.DEFAULT_USER_COUNT,
            strategy="Genetic",
        )
        # Run the simulation with the provided power state matrix
        energy_consumed = simulation.run(power_matrice_genetic)

        # Calculate energy consumption and QoS satisfaction
        qos_satisfaction = simulation.evaluate_qos_satisfaction()

        # Normalize metrics to [0, 1]
        normalized_energy = energy_consumed / 600000
        normalized_qos = qos_satisfaction / 100

        fitness_score = (qos_weight * normalized_qos) - (
            energy_weight * normalized_energy
        )

        fitness_score = max(fitness_score, 0)

        return fitness_score

    def fitness_function(self, ga_instance, solution, solution_idx):
        """
        Fitness function for PyGAD.

        Args:
            ga_instance: The PyGAD instance.
            solution: The current solution being evaluated.
            solution_idx: The index of the solution in the population.

        Returns:
            The fitness score of the solution.
        """
        # Reshape the solution into the original power matrix dimensions
        power_state_matrix = np.reshape(solution, (self.num_nodes, self.num_steps))
        fitness = self.evaluate_solution(power_state_matrix)
        print("***********************************************")
        print(f"Solution Index {solution_idx}:")
        print(f"Power State Matrix: {power_state_matrix}")
        print(f"Fitness: {round(fitness,2)}")
        print("***********************************************")
        # Evaluate the solution
        return fitness
