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
    simulation = Simulation()

    # Run the simulation with the provided parameters (example usage)
    print(
        f"Running simulation with {args.num_base_stations} base stations, and a maximum time of {args.max_time} seconds."
    )


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
