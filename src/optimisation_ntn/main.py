import argparse

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.utils.position import Position
from optimisation_ntn.algorithms.req_generator import ReqGenerator


class Main:
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

    #This is a matrix_k generation usage example
    matrix_k_generator = ReqGenerator(100)

    #Contains all the request but the value is null
    requests = []

    simulation = Simulation()

    simulation.matrix_k = matrix_k_generator.matrix_k_populate(1000, requests, 6)
