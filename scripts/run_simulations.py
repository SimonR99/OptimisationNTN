"""Script to run multiple simulations with different parameter combinations"""

import subprocess
import itertools
from typing import List, Dict

# Define parameter variations
PARAMETERS = {
    "power_strategies": ["AllOn", "Random", "StaticRandom"],
    "assignment_strategies": ["TimeGreedy", "ClosestNode", "EnergyGreedy", "HAPSOnly"],
}


def generate_command(params: Dict) -> str:
    """Generate command string for a parameter combination"""
    base_cmd = "python -m optimisation_ntn.main"

    # Add parameters
    cmd_parts = [
        base_cmd,
        f"--algorithm {params['power_strategy']}",
        f"--assignment_strategy {params['assignment_strategy']}",
        f"--iteration_count {params['iteration_count']}",
        f"--user_count_multiplier {params['user_count_multiplier']}",
    ]

    return " ".join(cmd_parts)


def run_simulations():
    """Run all simulation combinations"""
    # Generate all parameter combinations
    combinations = list(
        itertools.product(
            PARAMETERS["power_strategies"],
            PARAMETERS["assignment_strategies"],
        )
    )

    total_combinations = len(combinations)
    print(f"Starting {total_combinations} simulation combinations...")

    # Run each combination
    for i, (power_strat, assign_strat) in enumerate(combinations, 1):
        params = {
            "power_strategy": power_strat,
            "assignment_strategy": assign_strat,
            "user_count_multiplier": 1.1,
            "iteration_count": 10,
        }

        cmd = generate_command(params)
        print(f"\nRunning combination {i}/{total_combinations}:")
        print(f"Power Strategy: {power_strat}")
        print(f"Assignment Strategy: {assign_strat}")
        print(f"Generated Command: {cmd}\n")

        # Execute the command
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Successfully completed combination {i}")
        except subprocess.CalledProcessError as e:
            print(f"Error running combination {i}: {e}")
            continue


if __name__ == "__main__":
    run_simulations()
