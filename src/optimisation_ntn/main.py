import argparse

from optimisation_ntn.simulation import Simulation


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
        "--algorithm",
        type=str,
        choices=["Random", "AllOn"],
        default="AllOn",
        help="Algorithm used for optimizating or running the simulation",
    )

    return parser


def main(args):
    simulation = Simulation(time_step=args.tick_time, max_time=args.max_time)

    if args.algorithm not in ["Random", "AllOn"]:
        # Run optimization mode
        best_energy, energy_history = simulation.optimize(num_iterations=10)
        print(f"Best energy consumption: {best_energy}")
        print(f"Energy history: {energy_history}")
    else:
        # Run normal simulation mode
        total_energy = simulation.run()
        print(f"Total energy consumed: {total_energy} joules")


if __name__ == "__main__":
    parser = create_parser()
    parser.add_argument(
        "--mode",
        choices=["run", "optimize"],
        default="run",
        help="Simulation mode: run a single simulation or optimize over multiple runs",
    )
    args = parser.parse_args()
    main(args)
