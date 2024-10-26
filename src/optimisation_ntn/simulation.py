""" Simulation class that instantiates the Network class and runs the simulation. """

import argparse

from optimisation_ntn.network import Network


class Simulation:
    """Class to run the simulation."""

    def __init__(self):
        self.network = Network()

    def run(self, max_time=3000):
        for _ in range(max_time):
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

    simulation.run(max_time=args.max_time)
