""" Main module, runs the simulation or optimization """

import argparse
from typing import List, Tuple

import numpy as np
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.optimize import minimize

from optimisation_ntn.algorithms.assignment.strategy_factory import (
    AssignmentStrategyFactory,
)
from optimisation_ntn.optimization.optimization_problem import OptimizationProblem
from optimisation_ntn.simulation import Simulation, SimulationConfig
from optimisation_ntn.algorithms.power.strategy_factory import PowerStrategyFactory


def create_argument_parser():
    """Create parser for command line arguments"""
    arg_parser = argparse.ArgumentParser(description="Run the NTN network simulation.")

    arg_parser.add_argument(
        "--max_time",
        type=int,
        default=Simulation.DEFAULT_MAX_SIMULATION_TIME,
        help="The maximum simulation time in seconds",
    )

    arg_parser.add_argument(
        "--tick_time",
        type=float,
        default=Simulation.DEFAULT_TICK_TIME,
        help="Number of seconds per tick",
    )

    arg_parser.add_argument(
        "--user_count",
        type=int,
        default=Simulation.DEFAULT_USER_COUNT,
        help="Number of users in the simulation",
    )

    arg_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug printing",
    )

    # Power strategy choice
    power_strategies = PowerStrategyFactory.available_strategies()
    arg_parser.add_argument(
        "--power",
        type=str,
        choices=power_strategies,
        default="AllOn",
        help="Power management strategy to use",
    )

    # Combined assignment strategy and optimization algorithm choice
    all_strategies = AssignmentStrategyFactory.available_strategies() + [
        "GA",
        "DE",
        "PSO",
    ]
    arg_parser.add_argument(
        "--strategy",
        type=str,
        choices=all_strategies,
        default="TimeGreedy",
        help="Assignment strategy or optimization algorithm to use",
    )

    # Optimization specific arguments
    arg_parser.add_argument(
        "--generations",
        type=int,
        default=5,
        help="Number of generations for optimization algorithms",
    )

    arg_parser.add_argument(
        "--population",
        type=int,
        default=30,
        help="Population size for optimization algorithms",
    )

    arg_parser.add_argument(
        "--hide_output",
        action="store_true",
        default=False,
        help="Hide output",
    )

    arg_parser.add_argument(
        "--no-save",
        action="store_true",
        default=False,
        help="Disable saving results to files",
    )

    return arg_parser


def run_optimization(
    simulation: Simulation, algorithm_name: str, n_generations: int, pop_size: int
) -> Tuple[List[int], float, float]:
    """Run optimization with specified algorithm.

    Args:
        simulation: Simulation instance
        algorithm_name: Name of algorithm to use
        n_generations: Number of generations to run
        pop_size: Population size

    Returns:
        Tuple of (best assignment vector, energy consumed, satisfaction rate)
    """
    # Count compute nodes
    n_nodes = (
        len(simulation.network.base_stations)
        + len(simulation.network.haps_nodes)
        + len(simulation.network.leo_nodes)
    )

    # Create optimization problem
    problem = OptimizationProblem(simulation, simulation.user_count, n_nodes)

    # Configure algorithm
    if algorithm_name == "GA":
        algorithm = GA(
            pop_size=pop_size,
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=0.9, eta=3, repair=RoundingRepair()),
            mutation=PM(prob=0.1, eta=3, repair=RoundingRepair()),
            eliminate_duplicates=True,
            repair=RoundingRepair(),
        )
    elif algorithm_name == "DE":
        algorithm = DE(
            pop_size=pop_size,
            sampling=IntegerRandomSampling(),
            variant="DE/rand/1/bin",
            CR=0.9,
            F=0.8,
            repair=RoundingRepair(),
        )
    else:  # PSO
        algorithm = PSO(
            pop_size=pop_size,
            sampling=IntegerRandomSampling(),  # type: ignore
            w=0.9,
            c1=2.0,
            c2=2.0,
            repair=RoundingRepair(),  # type: ignore
        )

    # Run optimization
    print(f"\nRunning optimization with {algorithm_name}...")
    result = minimize(
        problem, algorithm, ("n_gen", n_generations), seed=42, verbose=True
    )

    if result.X is not None:
        best_x = result.X.astype(int)
        energy, satisfaction = simulation.run_with_assignment(best_x)
        print(f"\nBest solution found by {algorithm_name}:")
        print(f"Assignment vector: {best_x}")
        print(f"Energy consumed: {energy:.2f} J")
        print(f"QoS satisfaction: {satisfaction * 100:.2f}%")
        return best_x, energy, satisfaction

    print(f"\n{algorithm_name} found no feasible solution")
    return [], 0.0, 0.0


def main(cli_args):
    """Main function"""
    # Create simulation configuration
    config = SimulationConfig(
        seed=42,
        time_step=cli_args.tick_time,
        max_time=cli_args.max_time,
        debug=cli_args.debug,
        user_count=cli_args.user_count,
        print_output=not cli_args.hide_output,
        assignment_strategy=cli_args.strategy,
        power_strategy=cli_args.power,
        save_results=not cli_args.no_save,
        optimizer=(
            cli_args.strategy if cli_args.strategy in ["GA", "DE", "PSO"] else None
        ),
    )

    # Create simulation instance
    simulation = Simulation(config)

    # Check if using an optimization algorithm
    if cli_args.strategy in ["GA", "DE", "PSO"]:
        baseline_energy, baseline_satisfaction = simulation.run_with_assignment(
            np.random.randint(
                0, len(simulation.network.compute_nodes) - 1, simulation.user_count
            )
        )

        best_vector, energy, satisfaction = run_optimization(
            simulation, cli_args.strategy, cli_args.generations, cli_args.population
        )

        # Compare with baseline
        if not cli_args.hide_output:
            print("\nComparing with Random strategy...")
            print("\nResults comparison:")
            print(f"Optimized solution: {energy:.2f} J, {satisfaction*100:.2f}% QoS")
            print(
                f"Baseline strategy: {baseline_energy:.2f} J, {baseline_satisfaction*100:.2f}% QoS"
            )
            improvement = ((baseline_energy - energy) / baseline_energy) * 100
            print(f"\nEnergy improvement: {improvement:.1f}%")
            print(f"Best vector: {best_vector}")

        return energy

    # Run with traditional assignment strategy
    return simulation.run()


if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()
    main(args)
