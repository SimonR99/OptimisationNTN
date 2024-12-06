import argparse
import math

import numpy as np
from pygad import pygad

from optimisation_ntn.algorithms.power_strategy import (
    GeneticAlgorithmStrategy,
    AllOnStrategy,
    RandomStrategy,
    StaticRandomStrategy,
)

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.utils import genetic_config
from optimisation_ntn.utils.data_export import collect_graph_data

previous_population = None


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
        "--iteration_count",
        type=int,
        default=1,
        help="Number of iterations",
    )

    parser.add_argument(
        "--user_count_multiplier",
        type=float,
        default=1.0,
        help="Multiplier for user count across iterations",
    )

    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["Random", "StaticRandom", "AllOn", "Genetic"],
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

    strategy = set_strategy(args.algorithm)

    if args.algorithm == "Genetic":
        genetic_algorithm = GeneticAlgorithmStrategy()

        # Initialize PyGAD
        ga_instance = pygad.GA(
            num_generations=genetic_config.GENERATIONS,  # Number of generations
            num_parents_mating=int(math.ceil(genetic_config.POPULATION_SIZE/3)), # Number of parents mating (typically a fraction of population)
            parent_selection_type="rank",
            fitness_func=genetic_algorithm.fitness_function,  # Fitness function
            sol_per_pop=genetic_config.POPULATION_SIZE,  # Population size
            num_genes=int(genetic_algorithm.matrix_size),  # Chromosome length (size of matrix)
            gene_space=[0, 1],  # Genes can be either 0 (OFF) or 1 (ON)
            mutation_type="adaptive",  # Mutation type (adaptive mutation)
            mutation_percent_genes=[80, 7],  # Initial mutation rate is 95%, final mutation rate is 5%
            crossover_type="two_points",  # Crossover type (two-point crossover)
            on_generation=on_generation,  # Callback function after each generation
        )

        # Run the Genetic Algorithm
        ga_instance.run()

        # Get the best solution
        best_solution, best_solution_fitness, _ = ga_instance.best_solution()

        # Reshape the best solution back to a 2D matrix
        best_power_state_matrix = np.reshape(
            best_solution,
            (
                Simulation.DEFAULT_COMPUTE_NODES,
                int(
                    Simulation.DEFAULT_MAX_SIMULATION_TIME
                    / Simulation.DEFAULT_TICK_TIME
                )
                + 1,
            ),
        )

        print("Best solution (flattened):", best_solution)
        print("Best solution fitness:", best_solution_fitness)
        print("Best power state matrix:")
        print(best_power_state_matrix)

        # Plot fitness over generations (optional)
        ga_instance.plot_fitness(title="Fitness Progress Over Generations")

    else:
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
                strategy=strategy,
            )

            # Run the simulation
            total_energy = simulation.run(np.zeros(2))

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


def set_strategy(strategy: str):
    """Set the optimization strategy to use"""
    match strategy:
        case "AllOn":
            return AllOnStrategy()
        case "Random":
            return RandomStrategy()
        case "StaticRandom":
            return StaticRandomStrategy()


def on_generation(ga_instance):
    # Access the latest best fitness value from the list of best_solutions_fitness
    best_fitness_so_far = ga_instance.best_solutions_fitness[-1]
    print(f"Best Fitness so far: {best_fitness_so_far}")


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
