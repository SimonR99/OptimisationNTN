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