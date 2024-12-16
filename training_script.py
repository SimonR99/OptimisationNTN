"""Training script for Q-learning assignment strategy"""

import numpy as np
from optimisation_ntn.simulation import Simulation, SimulationConfig
from optimisation_ntn.algorithms.assignment.qlearning import QLearningAssignment


def get_min_max_energy(config: SimulationConfig, iterations: int = 25):
    sim = Simulation(config)

    max_energy = float("-inf")
    min_energy = float("inf")

    for _ in range(iterations):
        sim.reset()
        energy = sim.run()
        max_energy = max(max_energy, energy)
        min_energy = min(min_energy, energy)

    return min_energy, max_energy


def train_qlearning(
    episodes: int = 100,
    min_energy: float = None,
    max_energy: float = None,
    config: SimulationConfig = None,
):
    """Train Q-learning agent"""

    sim = Simulation(config)
    q_learning = sim.assignment_strategy

    # Training loop
    energy_history = []
    qos_history = []
    best_energy = float("inf")
    best_qos = 0

    for episode in range(episodes):
        # Update epsilon for this episode
        q_learning.epsilon = q_learning.get_epsilon(episode, episodes)

        # Reset episode-specific variables but keep Q-table
        q_table_backup = q_learning.q_table.copy()
        q_learning.reset()
        q_learning.q_table = q_table_backup

        # Run episode
        energy = sim.run()
        qos = sim.evaluate_qos_satisfaction()

        # Track best performance
        if qos >= 90 and energy < best_energy:
            best_energy = energy
            best_qos = qos
            print(f"\nNew best performance - Energy: {energy:.2f}, QoS: {qos:.2f}%")

        # Calculate final reward
        qos_threshold = 90.0
        if qos < qos_threshold:
            reward = -10.0
        else:
            # Normalize energy between 0 and 1
            max_energy = max_energy * 0.9
            min_energy = min_energy * 0.6
            normalized_energy = (energy - min_energy) / (max_energy - min_energy)
            energy_reward = 1.0 - normalized_energy
            reward = energy_reward * qos**2

        # Update Q-values with final reward
        q_learning.update_q_value(reward, None)

        # Store metrics
        energy_history.append(energy)
        qos_history.append(qos)

        # Save Q-table after each episode
        q_learning.save_q_table("qtable.npy")

        # Reset simulation for next episode
        sim.reset()

        # Restore Q-learning agent with saved table
        q_learning = sim.assignment_strategy
        q_learning.load_q_table("qtable.npy")

        # Print progress
        if (episode + 1) % 10 == 0:
            avg_energy = np.mean(energy_history[-10:])
            avg_qos = np.mean(qos_history[-10:])
            print(f"\nEpisode {episode + 1}/{episodes}")
            print(f"Average Energy: {avg_energy:.2f}")
            print(f"Average QoS: {avg_qos:.2f}%")
            print(f"Current epsilon: {q_learning.epsilon:.3f}")
            print(f"Last Reward: {reward:.4f}")

    return energy_history, qos_history


def test_qlearning(trained: bool = False, config: SimulationConfig = None):
    """Test trained Q-learning agent"""

    sim = Simulation(config)
    sim.reset()
    q_learning = sim.assignment_strategy

    if trained:
        try:
            q_learning.load_q_table("qtable.npy")
            print("Testing with trained Q-table")
        except FileNotFoundError:
            print("No trained Q-table found")

    # Set epsilon to 0 for testing (no exploration)
    q_learning.epsilon = 0

    # Run test episode
    energy = sim.run()
    qos = sim.evaluate_qos_satisfaction()

    print("\nTest Results:")
    print(f"Energy Consumed: {energy:.2f}")
    print(f"QoS: {qos:.2f}%")

    return energy, qos


if __name__ == "__main__":
    import os

    # delete qtable.npy if it exists
    if os.path.exists("qtable.npy"):
        os.remove("qtable.npy")

    n_users = 10

    config = SimulationConfig(
        assignment_strategy="TimeGreedy",
        power_strategy="OnDemand",
        user_count=n_users,
    )

    min_energy, max_energy = get_min_max_energy(config=config)

    print(f"Min energy: {min_energy:.2f}")
    print(f"Max energy: {max_energy:.2f}")

    config = SimulationConfig(
        seed=None,
        assignment_strategy="QLearning",
        power_strategy="OnDemand",
        user_count=n_users,
    )

    # Train the agent
    print("Starting training...")
    energy_history, qos_history = train_qlearning(
        episodes=100,
        min_energy=min_energy,
        max_energy=max_energy,
        config=config,
    )

    trained_better_than_untrained = 0

    for i in range(10):
        config.seed = i

        # Test the trained agent
        print("\nTesting trained agent...")
        untrained_energy, untrained_qos = test_qlearning(trained=False, config=config)

        # Test the trained agent
        print("\nTesting trained agent...")
        trained_energy, trained_qos = test_qlearning(trained=True, config=config)

        if trained_energy < untrained_energy:
            trained_better_than_untrained += 1

    print(f"Trained better than untrained: {trained_better_than_untrained}")
