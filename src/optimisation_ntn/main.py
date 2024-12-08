import argparse

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.algorithms.assignment.strategy_factory import (
    AssignmentStrategyFactory,
)


def create_parser():
    parser = argparse.ArgumentParser(
        description="Run the NTN network simulation with custom parameters."
    )

    parser.add_argument(
        "--max_time",
        type=int,
        default=Simulation.DEFAULT_MAX_SIMULATION_TIME,
        help="The maximum simulation time in seconds",
    )

    parser.add_argument(
        "--tick_time",
        type=float,
        default=Simulation.DEFAULT_TICK_TIME,
        help="Number of seconds per tick",
    )

    parser.add_argument(
        "--num_leo",
        type=int,
        default=Simulation.DEFAULT_LEO_COUNT,
        help="Number of LEO satellites",
    )

    parser.add_argument(
        "--num_base_stations",
        type=int,
        default=Simulation.DEFAULT_BS_COUNT,
        help="Number of base stations",
    )

    parser.add_argument(
        "--user_count",
        type=int,
        default=Simulation.DEFAULT_USER_COUNT,
        help="Number of users in the simulation",
    )

    parser.add_argument(
        "--power_strategy",
        type=str,
        choices=["AllOn", "OnDemand", "OnDemandWithTimeout"],
        default="AllOn",
        help="Power strategy to use",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug printing",
    )

    parser.add_argument(
        "--assignment_strategy",
        type=str,
        choices=AssignmentStrategyFactory.available_strategies(),
        default="TimeGreedy",
        help="Assignment strategy to use",
    )

    parser.add_argument(
        "--hide_output",
        action="store_true",
        default=False,
        help="Hide output",
    )

    return parser


def main(args):
    # Create a new simulation instance
    simulation = Simulation(
        seed=42,
        time_step=args.tick_time,
        max_time=args.max_time,
        debug=args.debug,
        user_count=args.user_count,
        power_strategy=args.power_strategy,
        assignment_strategy=args.assignment_strategy,
        print_output=not args.hide_output,
    )

    # Run the simulation
    total_energy = simulation.run()
    print(f"Total energy consumed: {total_energy} joules")
    return total_energy


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
