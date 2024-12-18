"""Q-Learning trainer for assignment strategy"""

import numpy as np
from typing import Optional
import os

from ...simulation import RequestStatus
from ...simulation import Simulation


class QLearningTrainer:
    def __init__(
        self,
        simulation: Simulation,
        episodes: int = 1000,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.1,
        epsilon_decay: float = 0.99,
        save_path: Optional[str] = None,
    ):
        self.simulation = simulation
        self.episodes = episodes
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.save_path = save_path

        self.max_energy = self.simulation.user_count * 250
        self.min_energy = self.simulation.user_count * 100

        self.training_history = []

    def calculate_episode_reward(
        self, qos_score: float, total_energy: float
    ) -> tuple[float, float]:
        """Calculate final reward for the episode"""
        # Exponential penalty if QoS is below threshold
        if qos_score < 90:
            qos_reward = -10000.0 * np.exp(90 - qos_score)
        else:
            qos_reward = (
                (qos_score / 100) ** 2
            ) * 2000  # Increased reward for good QoS

        # Normalize energy between 0 and 1 with less weight
        if self.max_energy == self.min_energy:
            norm_energy = 0
        else:
            if qos_score > 90:
                if total_energy > self.max_energy:
                    self.max_energy = total_energy
                if total_energy < self.min_energy:
                    self.min_energy = total_energy
            norm_energy = (total_energy - self.min_energy) / (
                self.max_energy - self.min_energy
            )

        energy_penalty = 250 - (norm_energy * 500)  # Reduced energy penalty

        return qos_reward, energy_penalty

    def train(self):
        """Train the Q-learning agent"""
        from ...algorithms.assignment import QLearningAssignment, ClosestNodeAssignment

        self.simulation.assignment_strategy = ClosestNodeAssignment(
            self.simulation.network
        )

        # get max/min energy consumption
        for i in range(20):
            self.simulation.reset()
            self.simulation.run()
            energy_consumed = self.simulation.system_energy_consumed
            if energy_consumed > self.max_energy:
                self.max_energy = energy_consumed
            if energy_consumed < self.min_energy:
                self.min_energy = energy_consumed

        self.simulation.reset()
        print(f"Max energy: {self.max_energy:.2f}, Min energy: {self.min_energy:.2f}")

        best_reward = float("-inf")
        best_qos = float("-inf")
        best_energy_score = float("-inf")
        epsilon = self.epsilon_start

        # delete qtable if it exists
        if self.save_path and os.path.exists(self.save_path):
            os.remove(self.save_path)

        print("Starting training...")

        for episode in range(self.episodes):
            self.simulation.reset()

            # Run episode
            strategy = QLearningAssignment(
                self.simulation.network,
                epsilon=epsilon,
                qtable_path=self.save_path,
            )
            self.simulation.assignment_strategy = strategy
            self.simulation.run()

            # Calculate episode metrics
            qos_score = self.simulation.evaluate_qos_satisfaction()
            total_energy = self.simulation.system_energy_consumed

            self.training_history.append(
                {
                    "qos_score": qos_score,
                    "total_energy": total_energy,
                }
            )

            # update epsilon
            epsilon = self.epsilon_start * (self.epsilon_decay**episode)

            # Calculate and apply final reward
            qos_reward, energy_reward = self.calculate_episode_reward(
                qos_score, total_energy
            )
            episode_reward = energy_reward

            # Apply episode reward to the strategy
            strategy.apply_episode_reward(episode_reward, qos_score)

            # Save Q-table if path provided
            if self.save_path:
                strategy.save_qtable(self.save_path)

            # Print progress
            if (episode + 1) % 10 == 0:
                print(
                    f"Episode {episode + 1}/{self.episodes} ({self.simulation.user_count} Users)"
                )
                print(f"Total Energy: {total_energy:.2f}J")
                print(f"QoS Score: {qos_score:.2f}")
                print(f"Epsilon: {epsilon:.3f}")
                print("---")

        print("Training completed!")

        return self.training_history
