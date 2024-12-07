"""Script to run multiple simulations with different parameter combinations in parallel"""
import subprocess
import itertools
from typing import Dict, Tuple
from multiprocessing import Pool, cpu_count
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'simulation_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Define parameter variations
PARAMETERS = {
    "power_strategies": ["AllOn", "Random", "StaticRandom"],
    "assignment_strategies": ["TimeGreedy", "ClosestNode", "EnergyGreedy", "HAPSOnly"],
    "user_counts": [20, 30, 40, 50, 60, 70, 80, 90, 100],
}

def generate_command(params: Dict) -> str:
    """Generate command string for a parameter combination"""
    base_cmd = "python -m optimisation_ntn.main"
    cmd_parts = [
        base_cmd,
        f"--algorithm {params['power_strategy']}",
        f"--assignment_strategy {params['assignment_strategy']}",
        f"--user_count {params['user_count']}",
    ]
    return " ".join(cmd_parts)

def run_single_simulation(params: Tuple) -> Dict:
    """Run a single simulation with given parameters"""
    power_strat, assign_strat, user_count = params
    
    simulation_params = {
        "power_strategy": power_strat,
        "assignment_strategy": assign_strat,
        "user_count": user_count,
    }
    
    cmd = generate_command(simulation_params)
    
    logging.info(f"\nRunning simulation:")
    logging.info(f"Power Strategy: {power_strat}")
    logging.info(f"Assignment Strategy: {assign_strat}")
    logging.info(f"User Count: {user_count}")
    logging.info(f"Generated Command: {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
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
        "command": cmd
    }

def run_parallel_simulations(max_workers: int = None):
    """Run all simulation combinations in parallel"""
    if max_workers is None:
        max_workers = max(1, cpu_count() - 1)  # Leave one CPU free
    
    # Generate all parameter combinations
    combinations = list(
        itertools.product(
            PARAMETERS["power_strategies"],
            PARAMETERS["assignment_strategies"],
            PARAMETERS["user_counts"],
        )
    )
    total_combinations = len(combinations)
    
    logging.info(f"Starting {total_combinations} simulation combinations using {max_workers} workers...")
    
    # Create a pool of workers and run simulations in parallel
    with Pool(processes=max_workers) as pool:
        results = []
        for result in pool.imap_unordered(run_single_simulation, combinations):
            results.append(result)
            logging.info(f"Completed simulation: {result['parameters']}")
    
    # Summarize results
    successful = sum(1 for r in results if r['status'] == 'Success')
    failed = sum(1 for r in results if r['status'] == 'Failed')
    
    logging.info("\nSimulation Summary:")
    logging.info(f"Total simulations: {total_combinations}")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")
    
    # Log failed simulations for review
    if failed > 0:
        logging.info("\nFailed Simulations:")
        for result in results:
            if result['status'] == 'Failed':
                logging.info(f"Parameters: {result['parameters']}")
                logging.info(f"Error: {result['error']}\n")
    
    return results

if __name__ == "__main__":
    start_time = time.time()
    run_parallel_simulations()
    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")