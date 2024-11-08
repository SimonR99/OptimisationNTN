import argparse

from optimisation_ntn.algorithms.req_generator import ReqGenerator
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.simulation import Simulation
from optimisation_ntn.utils.position import Position


def create_parser():
    parser = argparse.ArgumentParser(
        description="Run the NTN network simulation with custom parameters."
    )

    parser.add_argument(
        "--max_time",
        type=int,
        default=300,
        help="The maximum simulation time in seconds",
    )

    parser.add_argument(
        "--tick_time", type=int, default=0.001, help="Number of seconds per tick"
    )

    parser.add_argument(
        "--num_leo", type=int, default=1, help="Number of LEO satellites"
    )

    parser.add_argument(
        "--num_base_stations", type=int, default=4, help="Number of base stations"
    )

    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["Random", "AllOn"],
        default="AllOn",
        help="Algorithm used for optimizating or running the simulation",
    )

    return parser


def main(args):
    simulation = Simulation(time_step=args.tick_time)
    
    if args.algorithm not in ["Random", "AllOn"]:
        # Run optimization mode
        best_energy, energy_history = simulation.optimize(num_iterations=10)
        print(f"Best energy consumption: {best_energy}")
        print(f"Energy history: {energy_history}")
    else:
        # Run normal simulation mode
        total_energy = simulation.run()
        print(f"Total energy consumed: {total_energy}")


if __name__ == "__main__":
    parser = create_parser()
    parser.add_argument(
        "--mode",
        choices=["run", "optimize"],
        default="run",
        help="Simulation mode: run a single simulation or optimize over multiple runs"
    )
    args = parser.parse_args()
    main(args)
