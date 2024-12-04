import argparse
import math

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.utils.data_export import collect_graph_data


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
        type=int,
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
        "--iteration_count",
        type=int,
        default=1,
        help="Number of iterations",
    )

    parser.add_argument(
        "--user_count_multiplier",
        type=float,
        default=1.0,
        help="Number of users",
    )

    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["Random", "StaticRandom", "AllOn", "Genetic"],
        default="AllOn",
        help="Algorithm used for optimizing or running the simulation",
    )

    # Debug mode
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug printing",
    )

    return parser


def main(args):
    all_iterations_data = []
    current_user_count = Simulation.DEFAULT_USER_COUNT

    for i in range(args.iteration_count):
        if i != 0:
            current_user_count = math.ceil(
                current_user_count * args.user_count_multiplier
            )
        print(
            f"Starting iteration {i + 1}/{args.iteration_count} with {current_user_count} users..."
        )

        # Create a new simulation instance for each iteration
        simulation = Simulation(
            seed=42,
            time_step=args.tick_time,
            max_time=args.max_time,
            debug=args.debug,
            user_count=current_user_count,  # Use the computed user count
            strategy=args.algorithm,
        )

        # Run the simulation
        total_energy = simulation.run()

        # Collect data for the current iteration
        iteration_data = {
            "total_requests": simulation.total_requests,
            "success_rate": simulation.evaluate_qos_satisfaction(),
            "total_energy_bs": simulation.total_energy_bs,
            "total_energy_haps": simulation.total_energy_haps,
            "total_energy_leo": simulation.total_energy_leo,
        }
        all_iterations_data.append(iteration_data)

        print(f"Iteration {i + 1} - Total energy consumed: {total_energy} joules")

    # Compile and export data for all iterations
    if args.debug:
        collect_graph_data(all_iterations_data)


if __name__ == "__main__":
    parser = create_parser()
    parser.add_argument(
        "--mode",
        choices=["run"],
        default="run",
        help="Simulation mode: run a single simulation",
    )
    args = parser.parse_args()
    main(args)
