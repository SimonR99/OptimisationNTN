import argparse
import numpy as np
from typing import List, Tuple

from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize

from optimisation_ntn.simulation import Simulation
from optimisation_ntn.optimization.optimization_problem import OptimizationProblem


def create_parser():
    parser = argparse.ArgumentParser(description="Optimize the NTN network simulation.")

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
        "--num_requests",
        type=int,
        default=10,
        help="Number of requests to optimize",
    )

    parser.add_argument(
        "--algorithm",
        type=str,
        choices=["GA", "DE", "PSO"],
        default="GA",
        help="Optimization algorithm to use",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug printing",
    )

    parser.add_argument(
        "--generations",
        type=int,
        default=10,
        help="Number of generations for optimization",
    )

    parser.add_argument(
        "--population",
        type=int,
        default=50,
        help="Population size for optimization",
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
            sampling=IntegerRandomSampling(),
            w=0.9,
            c1=2.0,
            c2=2.0,
            repair=RoundingRepair(),
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
        print(f"QoS satisfaction: {satisfaction:.2f}%")
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
        user_count=args.num_requests,
        power_strategy="OnDemand",
    )

    # Run optimization
    best_vector, energy, satisfaction = run_optimization(
        simulation, args.algorithm, args.generations, args.population
    )

    # Compare with baseline strategy
    print("\nComparing with TimeGreedy strategy...")
    simulation.reset()
    baseline_energy, baseline_satisfaction = simulation.run_with_assignment(
        np.random.randint(
            0, len(simulation.network.compute_nodes) - 1, simulation.user_count
        )
    )

    print("\nResults comparison:")
    print(f"Optimized solution: {energy:.2f} J, {satisfaction*100:.2f}% QoS")
    print(
        f"Baseline strategy: {baseline_energy:.2f} J, {baseline_satisfaction*100:.2f}% QoS"
    )

    improvement = ((baseline_energy - energy) / baseline_energy) * 100
    print(f"\nEnergy improvement: {improvement:.1f}%")


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    main(args)
