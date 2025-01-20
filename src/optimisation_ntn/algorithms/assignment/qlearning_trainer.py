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

        self.max_energy = self.simulation.user_count * 300
        self.min_energy = self.max_energy

        self.training_history = []

    def calculate_episode_reward(self, qos_score: float, total_energy: float) -> float:
        """Calculate final reward for the episode"""
        # Normalize energy between 0 and 1 with less weight
        if qos_score > 80:
            if total_energy > self.max_energy:
                self.max_energy = total_energy
            if total_energy < self.min_energy:
                self.min_energy = total_energy

            # max difference is 20% between min and max energy
            factor = 1.2
            print(
                f"---- Max energy: {self.max_energy:.2f}, Min energy: {self.min_energy:.2f}, energy x factor: {self.min_energy * factor:.2f}"
            )
            if self.min_energy * factor < self.max_energy:
                self.max_energy = self.min_energy * factor

            norm_energy = (total_energy - self.min_energy) / (
                self.max_energy - self.min_energy
            )
        else:
            norm_energy = 1

        print(f"Max energy: {self.max_energy:.2f}, Min energy: {self.min_energy:.2f}")
        print(f"Norm energy: {norm_energy:.2f}")
        print(f"QoS score: {qos_score:.2f}")

        norm_energy = norm_energy - (qos_score / 100)
        energy_penalty = 250 - (norm_energy * 500)  # Reduced energy penalty

        print(f"Energy penalty: {energy_penalty:.2f}")

        return energy_penalty

    def train(self):
        """Train the Q-learning agent"""
        from ...algorithms.assignment import QLearningAssignment, ClosestNodeAssignment

        self.simulation.assignment_strategy = ClosestNodeAssignment(
            self.simulation.network
        )

        self.simulation.reset()
        print(f"Max energy: {self.max_energy:.2f}, Min energy: {self.min_energy:.2f}")

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
            energy_reward = self.calculate_episode_reward(qos_score, total_energy)

            # Apply episode reward to the strategy
            strategy.apply_episode_reward(energy_reward, qos_score)

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
