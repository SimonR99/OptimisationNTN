from abc import ABC, abstractmethod

import numpy as np
import pygad

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

class GeneticAlgorithmStrategy(PowerStateStrategy):
    """Strategy implementing a Genetic Algorithm to optimize power states."""

    def __init__(self, population_size=10, generations=20, mutation_prob=0.1, crossover_prob=0.9):
        """Initialize the Genetic Algorithm parameters.

        Args:
            population_size: Number of individuals in the population.
            generations: Number of generations for the genetic algorithm.
            mutation_prob: Probability of mutating a gene.
            crossover_prob: Probability of crossover during mating.
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_prob = mutation_prob
        self.crossover_prob = crossover_prob

    def fitness_function(self, individual, num_devices, num_steps):
        """Evaluate the fitness of an individual solution.

        Args:
            individual: Flattened matrix representing on/off states of nodes.
            num_devices: Number of devices in the system.
            num_steps: Number of time steps in the system.

        Returns:
            Fitness score (higher is better).
        """
        # Reshape individual into power matrix
        power_matrix = np.array(individual).reshape((num_devices, num_steps))

        # Calculate total energy consumption per node
        energy_per_node = np.sum(power_matrix, axis=1)  # Sum over time steps

        # Fitness is higher when energy is evenly distributed across nodes
        energy_variance = np.var(energy_per_node)
        return -energy_variance  # Minimize variance for balance

    def generate_power_matrix(self, num_devices: int, num_steps: int) -> np.ndarray:
        """Generate power state matrix optimized using Genetic Algorithm."""

        def fitness_wrapper(solution, _):
            return self.fitness_function(solution, num_devices, num_steps)

        # Total genes = num_devices * num_steps
        num_genes = num_devices * num_steps

        # Initial population
        initial_population = np.random.randint(0, 2, size=(self.population_size, num_genes))

        # PyGAD setup
        ga_instance = pygad.GA(
            num_generations=self.generations,
            num_parents_mating=self.population_size // 2,
            fitness_func=fitness_wrapper,
            sol_per_pop=self.population_size,
            num_genes=num_genes,
            mutation_probability=self.mutation_prob,
            crossover_probability=self.crossover_prob,
            gene_space=[0, 1],  # Binary genes
        )

        # Run the genetic algorithm
        ga_instance.run()

        # Get the best solution
        best_solution, _, _ = ga_instance.best_solution()
        return np.array(best_solution).reshape((num_devices, num_steps))

    def get_name(self) -> str:
        return f"Genetic Algorithm Strategy (pop={self.population_size}, gen={self.generations})"