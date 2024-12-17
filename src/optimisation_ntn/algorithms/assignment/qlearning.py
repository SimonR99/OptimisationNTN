"""Q-Learning based assignment strategy"""

from calendar import c
import numpy as np
from typing import List, Dict, Tuple, Optional
import pickle
import os
from ...networks.request import Request, RequestStatus
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class QLearningAssignment(AssignmentStrategy):
    """Assigns requests using Q-Learning"""

    def __init__(
        self,
        network,
        epsilon=0.0,
        alpha=0.1,
        gamma=0.9,
        qtable_path=None,
    ):
        self.network = network
        # Set very low epsilon if using a pre-trained model
        self.epsilon = epsilon
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.q_table: Dict[str, np.ndarray] = {}
        self.last_state = None
        self.last_action = None
        self.debug = False
        self.last_request = None

        # Load Q-table if path provided
        if qtable_path and os.path.exists(qtable_path):
            with open(qtable_path, "rb") as f:
                self.q_table = pickle.load(f)
                # print the first 10 states and their corresponding q-values
                # print(f"Number of states: {len(self.q_table)}")
                # print first q-table entry
                # print(f"First state: {list(self.q_table.keys())[0]}")
                # print(f"First q-values: {self.q_table[list(self.q_table.keys())[0]]}")

    def get_state(self, request: Request, nodes: List[BaseNode]) -> str:
        """Convert current system state to a string representation

        State format for each node:
        - on/off state (1/0)
        - remaining battery category (i/-1/l/m/h for infinite/-1/<100/<1000/>=1000)
        - can process (1/0)
        - processing power category (J/Mbit)
        """
        state_parts = []

        # Request features - keep the existing size categorization
        size_category = 0
        if request.size > 5e6:
            size_category = 2
        elif request.size > 3e6:
            size_category = 1
        state_parts.append(f"s{size_category}")  # Request size category

        # Node states with new features
        for node in nodes:
            node_state = []

            # Node on/off state
            node_state.append(f"{'1' if node.state else '0'}")

            # Remaining battery energy categorization
            if node.battery_capacity == -1:
                battery_cat = "i"  # infinite
            else:
                remaining_energy = node.battery_capacity - node.energy_consumed
                if remaining_energy < 100:
                    battery_cat = "l"  # low
                elif remaining_energy < 1000:
                    battery_cat = "m"  # medium
                else:
                    battery_cat = "h"  # high
            node_state.append(f"{battery_cat}")

            # Can process check
            can_process = "1" if node.can_process(request) else "0"
            node_state.append(f"{can_process}")

            # Processing power category (in J/Mbit)
            processing_time = (
                request.size * node.cycle_per_bit / node.processing_frequency
            )
            processing_energy = node.processing_energy() * processing_time

            processing_power = processing_energy / request.size
            processing_power = processing_power * 1e6
            discretized_power = 0
            if processing_power < 2:
                discretized_power = 0
            elif processing_power < 5:
                discretized_power = 1
            elif processing_power < 10:
                discretized_power = 2
            else:
                discretized_power = 3
            node_state.append(f"{discretized_power}")

            # Add the discretized request size
            discretized_request_size = 0
            if request.size > 3e6:
                discretized_request_size = 2
            elif request.size > 6e6:
                discretized_request_size = 1
            else:
                discretized_request_size = 0
            node_state.append(f"{discretized_request_size}")

            state_parts.append("_".join(node_state))

        return "|".join(state_parts)

    def get_q_values(self, state: str, num_actions: int) -> np.ndarray:
        """Get Q-values for a state, initializing if needed"""
        if state not in self.q_table:
            self.q_table[state] = np.zeros(num_actions)
        return self.q_table[state]

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        # Calculate reward for previous action if applicable
        if self.last_request is not None and self.last_action is not None:
            if self.last_request.status == RequestStatus.FAILED:
                reward = -100.0
            elif (
                self.last_request.status == RequestStatus.COMPLETED
                and 0 <= self.last_action < len(nodes)
            ):  # Validate index
                selected_node = nodes[self.last_action]

                # Calculate processing energy
                processing_time = (
                    self.last_request.size
                    * selected_node.cycle_per_bit
                    / selected_node.processing_frequency
                )
                processing_energy = selected_node.processing_energy() * processing_time

                # Calculate transmission energy - use the first link's bandwidth as reference
                # Find the communication link for this node
                for link in self.network.communication_links:
                    if link.node_b == selected_node:
                        transmission_time = (
                            self.last_request.size / link.config.total_bandwidth
                        )
                        transmission_energy = (
                            selected_node.transmission_energy() * transmission_time
                        )
                        break
                else:
                    # If no link found, only use processing energy
                    transmission_energy = 0

                # Total energy consumed
                total_energy = processing_energy + transmission_energy
                # print(f"Total energy: {total_energy:.2f} J")
                # print(f"request size: {request.size}")
                energy_per_m_bit = (total_energy / request.size) * 1e6
                # print(f"energy/size: {energy_per_m_bit:.2f} J/Mbit")
                # print(f"node: {selected_node.name}")
                reward = -(energy_per_m_bit**2)
            else:
                reward = 0.0

            # print(f"Reward: {reward:.2f}")
            self.update(reward, request, nodes)

        state = self.get_state(request, nodes)
        q_values = self.get_q_values(state, len(nodes))

        # Epsilon-greedy action selection
        valid_actions = list(range(len(nodes)))
        if not valid_actions:
            raise ValueError("No valid nodes available for assignment")

        if np.random.random() < self.epsilon:
            action = np.random.choice(valid_actions)
        else:
            action = np.argmax(q_values)
            if action >= len(valid_actions):  # Safety check
                action = np.random.choice(valid_actions)

        self.last_state = state
        self.last_action = action
        self.last_request = request

        selected_node = nodes[action]
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        if self.debug:
            print(f"Q values: {q_values}, for state {state}")
            print(f"Selected node {action} with Q-values: {q_values}")

        return selected_node, path, total_delay

    def update(
        self, reward: float, new_request: Optional[Request], nodes: List[BaseNode]
    ):
        """Update Q-values based on reward and new state"""
        if self.last_state is None:
            return

        if new_request is None:
            # Terminal state - only use immediate reward
            old_value = self.q_table[self.last_state][self.last_action]
            new_value = (1 - self.alpha) * old_value + self.alpha * reward
        else:
            # Non-terminal state - use Q-learning update
            new_state = self.get_state(new_request, nodes)
            new_q_values = self.get_q_values(new_state, len(nodes))

            old_value = self.q_table[self.last_state][self.last_action]
            next_max = np.max(new_q_values)
            new_value = (1 - self.alpha) * old_value + self.alpha * (
                reward + self.gamma * next_max
            )

        self.q_table[self.last_state][self.last_action] = new_value

        # print(f"Updated Q-value from {old_value:.2f} to {new_value:.2f}")
        # print(self.q_table)

        if self.debug:
            print(f"Updated Q-value from {old_value:.2f} to {new_value:.2f}")

    def save_qtable(self, path: str):
        """Save Q-table to file"""
        with open(path, "wb") as f:
            pickle.dump(self.q_table, f)

    def calculate_request_reward(
        self, request: Request, selected_node: BaseNode
    ) -> float:
        """Calculate reward for a single request completion"""
        if request.status == RequestStatus.FAILED:
            return -100.0  # Heavy penalty for failure

        if request.status == RequestStatus.COMPLETED:
            # Calculate QoS satisfaction
            completion_time = request.get_tick() - request.creation_time
            qos_satisfaction = completion_time <= request.qos_limit

            # Calculate energy efficiency
            processing_time = (
                request.size
                * selected_node.cycle_per_bit
                / selected_node.processing_frequency
            )
            energy_consumed = (
                selected_node.processing_energy() * processing_time
            ) / 1000  # Convert to kJ

            # Combine metrics
            reward = 50.0 if qos_satisfaction else -50.0  # Base reward/penalty
            reward -= energy_consumed * 10  # Energy penalty (scaled)

            return reward

        return 0.0  # Neutral reward for other states
