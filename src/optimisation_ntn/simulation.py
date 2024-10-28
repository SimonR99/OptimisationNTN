""" Simulation class that instantiates the Network class and runs the simulation. """

import argparse
import string

from optimisation_ntn.matrices.base_matrice import Matrice
from optimisation_ntn.network import Network

class Simulation:
    """Class to run the simulation."""
    max_time = 3000

    def __init__(self, initial_dimension: int = 6):
        self.network = Network()
        self.matrix_a = Matrice(initial_dimension, initial_dimension, "matrice A")
        self.matrix_b = Matrice(initial_dimension, initial_dimension, "matrice B")
        self.matrix_k = Matrice(initial_dimension, initial_dimension, "matrice K")
        self.matrix_s = Matrice(initial_dimension, initial_dimension, "matrice S")
        self.matrix_x = Matrice(initial_dimension, initial_dimension, "matrice X")

    def run(self):
        for _ in range(self.max_time):
            self.network.tick()

    def reset(self):
        pass  # TODO

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Run the NTN network simulation with custom parameters."
    )
    parser.add_argument(
        "--max_time",
        type=int,
        default=3000,
        help="The maximum simulation time in ticks",
    )
    parser.add_argument(
        "--num_leo", type=int, default=2, help="Number of LEO satellites"
    )
    parser.add_argument(
        "--num_base_stations", type=int, default=4, help="Number of base stations"
    )
    parser.add_argument(
        "--initial_sat_position",
        type=int,
        default=0,
        help="Initial position of the satellite",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["GeneticAlgorithm", "QLearning"],
        default="GeneticAlgorithm",
        help="Algorithm used for optimization (GeneticAlgorithm or QLearning)",
    )

    args = parser.parse_args()

    simulation = Simulation()

    simulation.run()