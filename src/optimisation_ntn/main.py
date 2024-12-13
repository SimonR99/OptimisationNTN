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
from optimisation_ntn.simulation import Simulation


def create_parser():
    parser = argparse.ArgumentParser(description="Run the NTN network simulation.")

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

    # Combined assignment strategy and optimization algorithm choice
    all_strategies = AssignmentStrategyFactory.available_strategies() + [
        "GA",
        "DE",
        "PSO",
    ]
    parser.add_argument(
        "--strategy",
        type=str,
        choices=all_strategies,
        default="TimeGreedy",
        help="Assignment strategy or optimization algorithm to use",
    )

    # Optimization specific arguments
    parser.add_argument(
        "--generations",
        type=int,
        default=5,
        help="Number of generations for optimization algorithms",
    )

    parser.add_argument(
        "--population",
        type=int,
        default=30,
        help="Population size for optimization algorithms",
    )

    parser.add_argument(
        "--hide_output",
        action="store_true",
        default=False,
        help="Hide output",
    )

    return parser


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
    else:
        print(f"\n{algorithm_name} found no feasible solution")
        return [], 0.0, 0.0


def main(args):
    # Create simulation instance
    simulation = Simulation(
        seed=42,
        time_step=args.tick_time,
        max_time=args.max_time,
        debug=args.debug,
        user_count=args.user_count,
        power_strategy=args.power_strategy,
        print_output=not args.hide_output,
    )

    # Check if using an optimization algorithm
    if args.strategy in ["GA", "DE", "PSO"]:
        simulation.optimizer = args.strategy

        baseline_energy, baseline_satisfaction = simulation.run_with_assignment(
            np.random.randint(
                0, len(simulation.network.compute_nodes) - 1, simulation.user_count
            )
        )

        best_vector, energy, satisfaction = run_optimization(
            simulation, args.strategy, args.generations, args.population
        )

        # Compare with baseline
        if not args.hide_output:
            print("\nComparing with Random strategy...")
            print("\nResults comparison:")
            print(f"Optimized solution: {energy:.2f} J, {satisfaction*100:.2f}% QoS")
            print(
                f"Baseline strategy: {baseline_energy:.2f} J, {baseline_satisfaction*100:.2f}% QoS"
            )
            improvement = ((baseline_energy - energy) / baseline_energy) * 100
            print(f"\nEnergy improvement: {improvement:.1f}%")

        return energy
    else:
        # Run with traditional assignment strategy
        strategy = AssignmentStrategyFactory.get_strategy(
            args.strategy, simulation.network
        )
        simulation.assignment_strategy = strategy
        return simulation.run()


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
