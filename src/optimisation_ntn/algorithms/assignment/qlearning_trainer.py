"""Q-Learning trainer for assignment strategy"""

import numpy as np
from typing import Optional
import os

from ...simulation import RequestStatus
from ...simulation import Simulation


class QLearningTrainer:
    def __init__(
        self,
        simulation,
        episodes: int = 1000,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.1,
        epsilon_decay: float = 0.98,
        save_path: Optional[str] = None,
    ):
        self.simulation = simulation
        self.episodes = episodes
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.save_path = save_path

        self.max_energy = float("-inf")
        self.min_energy = float("inf")

    def episode_reward(self, qos_score: float, energy_consumed: float) -> float:
        """Calculate reward based on QoS score and energy consumed"""
        print(f"QoS score: {qos_score:.2}, Energy consumed: {energy_consumed:.2f}")

        if qos_score > 0.8:
            if energy_consumed > self.max_energy:
                self.max_energy = energy_consumed
            if energy_consumed < self.min_energy:
                self.min_energy = energy_consumed

            energy_score = (energy_consumed - self.min_energy) / (
                self.max_energy - self.min_energy
            )
            print(f"Energy score: {(1 - energy_score):.2f}")
            print(
                f"Max energy: {self.max_energy:.2f}, Min energy: {self.min_energy:.2f}"
            )
            return (0.5 - energy_score) * qos_score * 10
        else:
            print(f"QoS impact: {-(1 - qos_score)*10:.2f}")
            return -(1 - qos_score) * 10

    def train(self, seed: Optional[int] = None):
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

        # Create Q-learning strategy
        strategy = QLearningAssignment(self.simulation.network)
        strategy.debug = False  # Enable debug prints

        best_qos = float("-inf")
        epsilon = self.epsilon_start
        self.simulation.assignment_strategy = strategy

        print("Starting training...")

        for episode in range(self.episodes):

            strategy.epsilon = epsilon

            # Run episode
            self.simulation.run()

            # Track performance using QoS score
            qos_score = self.simulation.evaluate_qos_satisfaction() / 100
            energy_consumed = self.simulation.system_energy_consumed
            reward = self.episode_reward(qos_score, energy_consumed)

            strategy.update(reward, None, self.simulation.network.compute_nodes)

            # Decay epsilon
            epsilon = max(self.epsilon_end, epsilon * self.epsilon_decay)

            # Save if best performance
            if qos_score > best_qos:
                best_qos = qos_score

            # Print progress
            if (episode + 1) % 10 == 0:
                print(f"Episode {episode + 1}/{self.episodes}")
                print(f"QoS Score: {qos_score:.2f}%, Best: {best_qos:.2f}%")
                print(f"Epsilon: {epsilon:.3f}")
                print("---")

            # Reset simulation for next episode
            self.simulation.reset()
            strategy.last_request = None  # Reset last request tracking

        strategy.save_qtable(self.save_path)

        print("Training completed!")
        print(f"Best QoS Score achieved: {best_qos:.2f}%")
