"""Script to run multiple simulations with different parameter combinations in parallel"""

import subprocess
import itertools
from typing import Dict, List, Tuple
from multiprocessing import Pool, cpu_count
import logging
from datetime import datetime
import time
import os

from optimisation_ntn.algorithms.qlearning.trainer import QLearningTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Define parameter variations
PARAMETERS = {
    "power": ["OnDemand"],
    "assignment_strategies": [
        "TimeGreedy",
        "ClosestNode",
        "HAPSOnly",
        "GA",
        "PSO",
        "DE",
        "QLearning",
    ],
    "user_counts": [10, 30, 50, 70, 100],
}


def generate_command(params: Dict) -> str:
    """Generate command string for a parameter combination"""
    base_cmd = "python -m optimisation_ntn.main"
    cmd_parts = [
        base_cmd,
        f"--power {params['power']}",
        f"--strategy {params['assignment_strategy']}",
        f"--user_count {params['user_count']}",
        "--hide_output",
    ]

    # Add optimization parameters if using an optimization algorithm
    if params["assignment_strategy"] in ["GA", "PSO", "DE"]:
        cmd_parts.extend(["--generations 5", "--population 30"])

    # Add Q-learning specific parameters
    if params["assignment_strategy"] == "QLearning":
        qtable_path = f"trained_models/qtable_users_{params['user_count']}.npy"
        cmd_parts.append(f"--qtable_path {qtable_path}")

    return " ".join(cmd_parts)


def run_single_simulation(params: Tuple) -> Dict:
    """Run a single simulation with given parameters"""
    power_strat, assign_strat, user_count = params
    simulation_params = {
        "power": power_strat,
        "assignment_strategy": assign_strat,
        "user_count": user_count,
    }

    cmd = generate_command(simulation_params)
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        status = "Success"
        error = None
    except subprocess.CalledProcessError as e:
        status = "Failed"
        error = str(e)
        logging.error(f"Error in simulation: {error}")

    return {
        "parameters": simulation_params,
        "status": status,
        "error": error,
        "command": cmd,
    }


def run_parallel_simulations(max_workers: int = None):
    """Run all simulation combinations in parallel"""
    if max_workers is None:
        max_workers = max(1, cpu_count() - 1)

    # First, train Q-learning agents for all user counts if needed
    if "QLearning" in PARAMETERS["assignment_strategies"]:
        trainer = QLearningTrainer()
        trainer.train_all(PARAMETERS["user_counts"])

    # Generate all parameter combinations
    combinations = list(
        itertools.product(
            PARAMETERS["power"],
            PARAMETERS["assignment_strategies"],
            PARAMETERS["user_counts"],
        )
    )
    total_combinations = len(combinations)

    logging.info(
        f"Starting {total_combinations} simulation combinations using {max_workers} workers..."
    )

    # Run simulations in parallel
    with Pool(processes=max_workers) as pool:
        results = []
        for result in pool.imap_unordered(run_single_simulation, combinations):
            results.append(result)
            logging.info(f"Completed simulation: {result['parameters']}")

    # Summarize results
    successful = sum(1 for r in results if r["status"] == "Success")
    failed = sum(1 for r in results if r["status"] == "Failed")

    logging.info("\nSimulation Summary:")
    logging.info(f"Total simulations: {total_combinations}")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")

    if failed > 0:
        logging.info("\nFailed Simulations:")
        for result in results:
            if result["status"] == "Failed":
                logging.info(f"Parameters: {result['parameters']}")
                logging.info(f"Error: {result['error']}\n")

    return results


if __name__ == "__main__":
    start_time = time.time()
    run_parallel_simulations()
    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")
