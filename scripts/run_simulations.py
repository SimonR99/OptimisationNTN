"""Script to run multiple simulations with different parameter combinations in parallel"""

import subprocess
import itertools
from typing import Dict, List, Tuple, Optional
from multiprocessing import Pool, cpu_count
import logging
from datetime import datetime
import time
import os

from optimisation_ntn.simulation import Simulation, SimulationConfig
from optimisation_ntn.algorithms.assignment.qlearning_trainer import QLearningTrainer
from optimisation_ntn.algorithms.assignment.strategy_factory import QLearningAssignment

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
    "user_counts": [10, 30, 50, 75, 100, 200],
}


def train_qlearning(user_count: int) -> str:
    """Train Q-learning model for specific user count and return path to saved model"""
    qtable_path = f"trained_models/qtable_users_{user_count}.pkl"

    # Skip if model already exists
    if os.path.exists(qtable_path):
        logging.info(f"Q-learning model for {user_count} users already exists")
        return qtable_path

    logging.info(f"Training Q-learning model for {user_count} users...")

    # Create simulation
    sim = Simulation(
        config=SimulationConfig(
            seed=None,
            debug=False,
            time_step=Simulation.DEFAULT_TICK_TIME,
            max_time=Simulation.DEFAULT_MAX_SIMULATION_TIME,
            user_count=user_count,
            power_strategy="OnDemand",
            save_results=False,
        )
    )

    # Create and run trainer
    trainer = QLearningTrainer(
        simulation=sim,
        episodes=150,
        save_path=qtable_path,
    )

    # Create directory if it doesn't exist
    os.makedirs("trained_models", exist_ok=True)

    trainer.train()
    return qtable_path


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
        cmd_parts.extend(["--generations 20", "--population 50"])

    # Add Q-learning specific parameters
    if params["assignment_strategy"] == "QLearning":
        qtable_path = f"trained_models/qtable_users_{params['user_count']}.pkl"
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

    # If using Q-learning, ensure model exists
    if assign_strat == "QLearning":
        train_qlearning(user_count)

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


def run_parallel_simulations(max_workers: Optional[int] = None):
    """Run all simulation combinations in parallel"""
    if max_workers is None:
        max_workers = max(1, cpu_count() - 1)

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
