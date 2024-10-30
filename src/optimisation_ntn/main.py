import argparse

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import Haps
from optimisation_ntn.nodes.leo import Leo
from optimisation_ntn.utils.type import Position


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

    nodes = []

    bs1 = BaseStation(1, Position(0.5, 0))
    nodes.append(bs1)

    bs2 = BaseStation(2, Position(1.5, 0))
    nodes.append(bs2)

    bs3 = BaseStation(3, Position(2.5, 0))
    nodes.append(bs3)

    bs4 = BaseStation(4, Position(3.5, 0))
    nodes.append(bs4)

    haps = Haps(5, Position(2, 20))
    nodes.append(haps)

    leo = Leo(6, Position(4, 500))
    nodes.append(leo)

    simulation = Simulation()

    simulation.run()